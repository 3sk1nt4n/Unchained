"""Typed, allowlisted forensic-tool boundary exposed to the investigator."""

from __future__ import annotations

import contextlib
import json
import os
import queue
import shutil
import signal
import subprocess
import sys
import threading
import time
from collections.abc import Callable, Iterable, Mapping
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal

from ._tool_worker import DIRECT_TOOL_TARGETS
from .audit import AuditLog, canonical_json, sha256_text
from .caps import CapExceeded, RunBudget
from .models import EvidenceProfile, FunctionCall, JsonValue, ToolResult

ToolExecutor = Callable[[dict[str, JsonValue]], Any]
_WORKER_MAX_RESPONSE_BYTES = 2_000_000
_EVENT_LOG_MAX_RETURN_BYTES = 500_000


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True, slots=True)
class ToolDefinition:
    """One immutable model-visible tool and its trusted local executor."""

    name: str
    description: str
    parameters: dict[str, JsonValue]
    families: tuple[str, ...]
    os_families: tuple[str, ...]
    executor: ToolExecutor

    def openai_schema(self) -> dict[str, JsonValue]:
        """Return a strict Responses API function-tool declaration."""

        return {
            "type": "function",
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "strict": True,
        }


class ToolProtocolError(ValueError):
    """Raised when a model asks for a nonexistent or schema-invalid tool."""


class ToolRegistry:
    """Validate, meter, execute, and audit fixed forensic functions only."""

    def __init__(
        self,
        definitions: Iterable[ToolDefinition] | Mapping[str, ToolDefinition],
        audit: AuditLog,
        budget: RunBudget,
    ) -> None:
        values = definitions.values() if isinstance(definitions, Mapping) else definitions
        self._definitions = {definition.name: definition for definition in values}
        if len(self._definitions) == 0:
            raise ValueError("at least one available forensic tool is required")
        self.audit = audit
        self.budget = budget
        self._claimed_call_ids: set[str] = set()
        self._claim_lock = threading.Lock()

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._definitions))

    def schemas(self) -> tuple[dict[str, JsonValue], ...]:
        """Return only exact typed functions; paths and commands are never fields."""

        return tuple(self._definitions[name].openai_schema() for name in self.names)

    def definition(self, name: str) -> ToolDefinition:
        try:
            return self._definitions[name]
        except KeyError as exc:
            raise ToolProtocolError(f"tool is unavailable for this evidence route: {name}") from exc

    def validate(self, call: FunctionCall) -> ToolDefinition:
        if not call.call_id:
            raise ToolProtocolError("tool call_id may not be empty")
        if not call.name:
            raise ToolProtocolError("tool name may not be empty")
        if not call.arguments_valid:
            raise ToolProtocolError(call.parse_error or "tool arguments were not valid JSON")
        definition = self.definition(call.name)
        parameters = definition.parameters
        properties = parameters.get("properties", {})
        required = parameters.get("required", [])
        if not isinstance(properties, dict) or not isinstance(required, list):
            raise ToolProtocolError(f"trusted schema is malformed for {call.name}")
        unexpected = sorted(set(call.arguments) - set(properties))
        missing = sorted(set(str(value) for value in required) - set(call.arguments))
        if unexpected:
            raise ToolProtocolError(f"unexpected arguments for {call.name}: {unexpected}")
        if missing:
            raise ToolProtocolError(f"missing arguments for {call.name}: {missing}")
        for key, value in call.arguments.items():
            schema = properties[key]
            if isinstance(schema, dict) and not _matches_type(value, schema.get("type")):
                raise ToolProtocolError(f"argument {key!r} has the wrong type for {call.name}")
        return definition

    def execute(self, call: FunctionCall) -> ToolResult:
        """Execute one validated call after atomically reserving its cap slot."""

        self.validate(call)
        self._claim_calls((call,))
        try:
            self.budget.reserve_tool_calls(1)
        except CapExceeded as exc:
            self._record_unstarted(call, str(exc), status="capped")
            raise
        return self._execute_reserved(call)

    def execute_batch(self, calls: Iterable[FunctionCall]) -> tuple[ToolResult, ...]:
        """Run one-to-six calls concurrently and return results in request order."""

        batch = tuple(calls)
        if not batch:
            return ()
        if len(batch) > 6:
            raise ToolProtocolError("opening batch exceeds the hard maximum of six")
        for call in batch:
            self.validate(call)
        self._claim_calls(batch)
        try:
            self.budget.reserve_tool_calls(len(batch))
        except CapExceeded as exc:
            for call in batch:
                self._record_unstarted(call, str(exc), status="capped")
            raise
        workers = min(6, len(batch))
        ordered: list[ToolResult | None] = [None] * len(batch)
        with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="unchained-tool") as pool:
            futures = {
                pool.submit(self._execute_reserved, call): index for index, call in enumerate(batch)
            }
            for future in as_completed(futures):
                ordered[futures[future]] = future.result()
        return tuple(result for result in ordered if result is not None)

    def rejected(self, call: FunctionCall, reason: str) -> ToolResult:
        """Create a complete audit receipt for a call rejected before execution."""

        self._claim_calls((call,))
        return self._record_unstarted(call, reason, status="rejected")

    def _record_unstarted(
        self,
        call: FunctionCall,
        reason: str,
        *,
        status: Literal["rejected", "capped"],
    ) -> ToolResult:
        """Audit a complete deterministic receipt for a call that never ran."""

        started = _utc_now()
        self.audit.tool_started(call.call_id, call.name, call.arguments)
        output = canonical_json({"error": reason, "status": status})
        result = ToolResult(
            call_id=call.call_id,
            tool_name=call.name,
            arguments=call.arguments,
            output=output,
            output_sha256=sha256_text(output),
            status=status,
            started_at=started,
            ended_at=_utc_now(),
            duration_ms=0,
            error=reason,
        )
        self.audit.tool_completed(result)
        return result

    def _claim_calls(self, calls: tuple[FunctionCall, ...]) -> None:
        """Atomically reserve globally unique receipt ids before any audit event."""

        call_ids = tuple(call.call_id for call in calls)
        if any(not call_id for call_id in call_ids):
            raise ToolProtocolError("tool call_id may not be empty")
        duplicates = sorted(call_id for call_id in set(call_ids) if call_ids.count(call_id) > 1)
        if duplicates:
            raise ToolProtocolError(f"duplicate tool call_id in batch: {duplicates}")
        with self._claim_lock:
            reused = sorted(set(call_ids) & self._claimed_call_ids)
            if reused:
                raise ToolProtocolError(f"tool call_id was already used: {reused}")
            self._claimed_call_ids.update(call_ids)

    def _execute_reserved(self, call: FunctionCall) -> ToolResult:
        started_at = _utc_now()
        started_clock = time.monotonic()
        self.audit.tool_started(call.call_id, call.name, call.arguments)
        cap_error: CapExceeded | None = None
        output: str | None = None
        try:
            definition = self.validate(call)
            raw = definition.executor(dict(call.arguments))
            output = raw if isinstance(raw, str) else canonical_json(raw)
            status, error = _result_status(raw)
            self.budget.check()
        except CapExceeded as exc:
            cap_error = exc
            error = str(exc)
            status = "timeout"
            if output is None:
                output = canonical_json({"status": "timeout", "error": error})
        except Exception as exc:  # noqa: BLE001 - exceptions become typed receipts
            error = f"{type(exc).__name__}: {exc}"
            status = "error"
            output = canonical_json({"status": "error", "error": error})
        ended_clock = time.monotonic()
        assert output is not None
        result = ToolResult(
            call_id=call.call_id,
            tool_name=call.name,
            arguments=call.arguments,
            output=output,
            output_sha256=sha256_text(output),
            status=status,
            started_at=started_at,
            ended_at=_utc_now(),
            duration_ms=max(0, int((ended_clock - started_clock) * 1000)),
            error=error,
        )
        self.audit.tool_completed(result)
        if cap_error is not None:
            raise cap_error
        return result

    @classmethod
    def from_reference(
        cls,
        profile: EvidenceProfile,
        audit: AuditLog,
        budget: RunBudget,
    ) -> ToolRegistry:
        """Lazy-load only typed Qwen forensic callables through a sealed adapter."""

        definitions = load_reference_tools(profile, budget)
        return cls(definitions, audit, budget)


def _matches_type(value: JsonValue, expected: JsonValue) -> bool:
    if expected is None:
        return True
    choices = expected if isinstance(expected, list) else [expected]
    for choice in choices:
        if choice == "null" and value is None:
            return True
        if choice == "integer" and isinstance(value, int) and not isinstance(value, bool):
            return True
        if choice == "number" and isinstance(value, (int, float)) and not isinstance(value, bool):
            return True
        if choice == "string" and isinstance(value, str):
            return True
        if choice == "boolean" and isinstance(value, bool):
            return True
        if choice == "array" and isinstance(value, list):
            return True
        if choice == "object" and isinstance(value, dict):
            return True
    return False


def _result_status(raw: Any) -> tuple[str, str | None]:
    if not isinstance(raw, dict):
        return "success", None
    failure = str(raw.get("failure_mode") or "").lower()
    status = str(raw.get("status") or raw.get("kind") or "").lower()
    error = raw.get("error") or raw.get("reason")
    if failure == "timeout" or status == "timeout":
        return "timeout", str(error) if error else None
    if failure == "not_applicable" or status in {"not_applicable", "not-applicable"}:
        return "not-applicable", str(error) if error else None
    if (
        error
        or status in {"error", "failed", "parse_error", "capped"}
        or failure
        in {
            "exception",
            "runtime_error",
            "parse_error",
            "binary_missing",
        }
    ):
        details = raw.get("errors")
        fallback = failure or status or "tool_error"
        return "error", str(error or details or fallback)
    return "success", None


def _os_families(capability: dict[str, Any], plugin_path: str) -> tuple[str, ...]:
    applicable = {str(value) for value in capability.get("applicable_when", ())}
    if plugin_path.startswith("windows.") or "windows_evidence" in applicable:
        return ("windows",)
    if plugin_path.startswith("linux.") or "linux_evidence" in applicable:
        return ("linux",)
    if plugin_path.startswith("mac.") or "mac_evidence" in applicable:
        return ("macos",)
    return ("windows", "linux", "macos")


def _parameters_for(has_pid: bool, arg_type: str) -> dict[str, JsonValue]:
    properties: dict[str, JsonValue] = {}
    required: list[JsonValue] = []
    if has_pid and arg_type == "memory":
        properties["pid"] = {
            "type": ["integer", "null"],
            "description": "Optional process identifier; null analyzes all processes.",
        }
        required.append("pid")
    return {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }


def load_reference_tools(
    profile: EvidenceProfile,
    budget: RunBudget | None = None,
) -> tuple[ToolDefinition, ...]:
    """Load reviewed Qwen tool modules without importing its coordinator."""

    catalog = _load_qwen_catalog(budget)
    direct_catalog = catalog["direct"]
    volatility_plugins = catalog["volatility_plugins"]
    memory_path = str(profile.memory_items[0].path) if profile.memory_items else ""
    disk_item = profile.disk_items[0] if profile.disk_items else None
    disk_path = str(disk_item.path) if disk_item is not None else ""
    mount_path = str(profile.mount_path) if profile.mount_path else ""
    definitions: list[ToolDefinition] = []
    for name, arg_type, family, operating_systems in _direct_specs():
        if profile.os not in operating_systems:
            continue
        if arg_type == "memory" and (not memory_path or name not in volatility_plugins):
            continue
        if arg_type == "memory" and not any(
            value.startswith("volatility3.") for value in profile.available_tool_families
        ):
            continue
        if arg_type in {"disk", "standalone"} and not mount_path:
            continue
        capability = direct_catalog.get(name)
        if not isinstance(capability, dict):
            continue
        if capability.get("required_args"):
            continue
        definitions.append(
            ToolDefinition(
                name=name,
                description=_description(name, capability),
                parameters=_parameters_for(
                    bool(capability.get("has_pid")),
                    arg_type,
                ),
                families=(family,),
                os_families=operating_systems,
                executor=_direct_executor(
                    name,
                    arg_type,
                    memory_path=memory_path,
                    mount_path=mount_path,
                    budget=budget,
                ),
            )
        )

    definitions.extend(
        _dynamic_memory_definitions(
            profile,
            memory_path,
            volatility_plugins,
            budget,
        )
    )
    if disk_path and "sleuthkit" in profile.available_tool_families:
        for command in ("fsstat", "img_stat", "mmls"):
            if shutil.which(command) is None:
                continue
            filesystem_offset = (
                disk_item.filesystem_offset
                if command == "fsstat" and disk_item is not None
                else None
            )
            if command == "fsstat" and filesystem_offset is None:
                continue
            definitions.append(
                ToolDefinition(
                    name=f"tsk_{command}",
                    description=f"Run fixed read-only Sleuth Kit {command} metadata inspection.",
                    parameters=_empty_parameters(),
                    families=("sleuthkit",),
                    os_families=("windows", "linux", "macos"),
                    executor=_tsk_executor(
                        command,
                        disk_path,
                        budget,
                        filesystem_offset=filesystem_offset,
                    ),
                )
            )

    unique = {definition.name: definition for definition in definitions}
    if not unique:
        raise RuntimeError("no typed forensic tool is ready for this evidence route")
    return tuple(unique[name] for name in sorted(unique))


def _load_qwen_catalog(budget: RunBudget | None) -> dict[str, dict[str, Any]]:
    """Discover Qwen signatures/capabilities inside the same bounded worker."""

    result = _run_qwen_worker({"action": "catalog"}, budget)
    if not isinstance(result, dict):
        raise RuntimeError("the pinned sift-sentinel typed-tool catalog is malformed")
    direct = result.get("direct")
    volatility_plugins = result.get("volatility_plugins")
    if not isinstance(direct, dict) or not isinstance(volatility_plugins, dict):
        error = result.get("error")
        detail = f": {error}" if error else ""
        raise RuntimeError(f"the pinned sift-sentinel typed-tool dependency is unavailable{detail}")
    return {"direct": direct, "volatility_plugins": volatility_plugins}


def _direct_specs() -> tuple[tuple[str, str, str, tuple[str, ...]], ...]:
    windows = ("windows",)
    return (
        ("vol_pstree", "memory", "process_analysis", windows),
        ("vol_psscan", "memory", "process_analysis", windows),
        ("vol_netscan", "memory", "network", windows),
        ("vol_malfind", "memory", "code_injection", windows),
        ("vol_cmdline", "memory", "process_analysis", windows),
        ("vol_dlllist", "memory", "module_analysis", windows),
        ("vol_handles", "memory", "process_analysis", windows),
        ("vol_envars", "memory", "process_analysis", windows),
        ("vol_getsids", "memory", "identity", windows),
        ("vol_privileges", "memory", "identity", windows),
        ("vol_svcscan", "memory", "persistence", windows),
        ("vol_filescan", "memory", "filesystem", windows),
        ("vol_mftscan", "memory", "filesystem", windows),
        ("vol_reg_hivelist", "memory", "registry", windows),
        ("get_amcache", "disk", "execution", windows),
        ("extract_mft_timeline", "disk", "timeline", windows),
        ("parse_event_logs", "standalone", "event_logs", windows),
        ("parse_prefetch", "standalone", "execution", windows),
        ("parse_powershell_transcripts", "standalone", "powershell", windows),
        ("parse_rdp_artifacts", "standalone", "remote_access", windows),
        ("parse_wmi_subscription", "standalone", "persistence", windows),
        ("parse_registry_persistence", "standalone", "persistence", windows),
        ("parse_usb_devices", "standalone", "device_history", windows),
        ("parse_userassist", "standalone", "execution", windows),
        ("parse_scheduled_tasks_disk", "standalone", "persistence", windows),
    )


def _dynamic_memory_definitions(
    profile: EvidenceProfile,
    memory_path: str,
    volatility_plugins: dict[str, str],
    budget: RunBudget | None,
) -> list[ToolDefinition]:
    safe_plugins = {
        "linux.bash.bash",
        "linux.check_syscall.check_syscall",
        "linux.malfind.malfind",
        "linux.psaux.psaux",
        "linux.pslist.pslist",
        "linux.pstree.pstree",
        "linux.sockstat.sockstat",
        "mac.malfind.malfind",
        "mac.netstat.netstat",
        "mac.psaux.psaux",
        "mac.pslist.pslist",
        "mac.pstree.pstree",
    }
    if (
        not memory_path
        or profile.os not in {"linux", "macos"}
        or not any(family.startswith("volatility3.") for family in profile.available_tool_families)
    ):
        return []
    prefix = "linux." if profile.os == "linux" else "mac."
    definitions: list[ToolDefinition] = []
    for name, plugin_path in sorted(volatility_plugins.items()):
        if not plugin_path.startswith(prefix) or plugin_path.lower() not in safe_plugins:
            continue
        definitions.append(
            ToolDefinition(
                name=name,
                description=f"Read-only Volatility 3 function {plugin_path}.",
                parameters=_empty_parameters(),
                families=("memory",),
                os_families=(profile.os,),
                executor=_volatility_executor(name, memory_path, budget),
            )
        )
    return definitions


def _empty_parameters() -> dict[str, JsonValue]:
    return {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False,
    }


def _description(name: str, capability: dict[str, Any]) -> str:
    produces = ", ".join(str(value) for value in capability.get("produces", ()))
    runtime_class = str(capability.get("runtime_class") or "unknown")
    return (
        f"Read-only pinned Qwen function {name}, producing {produces or 'records'} "
        f"(runtime class: {runtime_class})."
    )


def _direct_executor(
    name: str,
    arg_type: str,
    *,
    memory_path: str,
    mount_path: str,
    budget: RunBudget | None,
) -> ToolExecutor:
    target = DIRECT_TOOL_TARGETS.get(name)
    if target is None or target[2] != arg_type:
        raise RuntimeError(f"Qwen worker allowlist is missing the typed tool {name}")

    def execute(arguments: dict[str, JsonValue]) -> Any:
        spec: dict[str, JsonValue] = {
            "action": "direct",
            "tool": name,
            "arguments": arguments,
        }
        if arg_type == "memory":
            spec["evidence_path"] = memory_path
        else:
            spec["mount_path"] = mount_path
        return _run_qwen_worker(spec, budget)

    return execute


def _volatility_executor(
    name: str,
    memory_path: str,
    budget: RunBudget | None,
) -> ToolExecutor:
    def execute(arguments: dict[str, JsonValue]) -> Any:
        return _run_qwen_worker(
            {
                "action": "volatility",
                "tool": name,
                "evidence_path": memory_path,
                "arguments": arguments,
            },
            budget,
        )

    return execute


def _run_qwen_worker(spec: dict[str, JsonValue], budget: RunBudget | None) -> Any:
    """Execute a sealed Qwen invocation in a disposable, time-bounded process."""

    timeout = 300.0 if budget is None else budget.remaining_wall_seconds()
    result = _run_isolated_worker(spec, timeout)
    if budget is not None:
        budget.check()
    return result


def _run_isolated_worker(spec: dict[str, JsonValue], timeout: float) -> Any:
    """Run the private JSON worker and terminate its whole process tree on timeout."""

    timeout = max(0.001, float(timeout))
    deadline = time.monotonic() + timeout
    try:
        # Validate the sealed request before a child exists.  The worker timeout
        # is added only after launch and is itself always JSON-safe.
        json.dumps(spec, ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError) as exc:
        return {"status": "error", "error": f"Qwen worker spec is not JSON-safe: {exc}"}
    command = [sys.executable, "-P", "-m", "unchained._tool_worker"]
    environment = _worker_environment()
    environment.pop("PYTHONHOME", None)
    environment.pop("PYTHONPATH", None)
    environment["PYTHONSAFEPATH"] = "1"
    popen_options: dict[str, Any] = {
        "stdin": subprocess.PIPE,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.DEVNULL,
        "text": True,
        "encoding": "utf-8",
        "errors": "replace",
        "env": environment,
        "shell": False,
    }
    if os.name == "nt":
        popen_options["creationflags"] = (
            subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
        )
    else:
        popen_options["start_new_session"] = True

    try:
        process = subprocess.Popen(command, **popen_options)
    except OSError as exc:
        return {
            "status": "error",
            "error": f"isolated Qwen worker could not start: {type(exc).__name__}: {exc}",
        }

    windows_job: int | None = None
    if os.name == "nt":
        try:
            windows_job = _assign_windows_kill_job(process)
        except OSError as exc:
            # Fail closed: production Qwen code never runs if descendants cannot
            # be placed under a kill-on-close wall-time boundary.
            with contextlib.suppress(OSError):
                process.kill()
            process.wait()
            return {
                "status": "error",
                "error": f"isolated Qwen worker could not enter a Job Object: {exc}",
            }

    timed_out = False
    output_line = ""
    read_error: BaseException | None = None
    output_queue: queue.Queue[str | BaseException] = queue.Queue(maxsize=1)

    def read_protocol_line() -> None:
        try:
            assert process.stdout is not None
            output_queue.put(process.stdout.readline(_WORKER_MAX_RESPONSE_BYTES + 1))
        except BaseException as exc:  # noqa: BLE001 - cross-thread transport
            output_queue.put(exc)

    reader = threading.Thread(
        target=read_protocol_line,
        name="unchained-worker-protocol",
        daemon=True,
    )
    try:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            timed_out = True
        else:
            request = dict(spec)
            request["timeout_seconds"] = remaining
            payload = json.dumps(request, ensure_ascii=False, allow_nan=False) + "\n"
            assert process.stdin is not None
            process.stdin.write(payload)
            process.stdin.flush()
            reader.start()
            try:
                response = output_queue.get(timeout=max(0.001, deadline - time.monotonic()))
            except queue.Empty:
                timed_out = True
            else:
                if isinstance(response, BaseException):
                    read_error = response
                else:
                    output_line = response
    except (OSError, ValueError) as exc:
        read_error = exc
    finally:
        # Cleanup happens on success too.  The worker deliberately remains
        # alive after writing its envelope, so its unique process group cannot
        # be recycled before every ordinary descendant is killed.
        windows_job = _terminate_worker_tree(process, windows_job)
        try:
            process.wait(timeout=2.0)
        except subprocess.TimeoutExpired:
            with contextlib.suppress(OSError):
                process.kill()
            process.wait()
        if reader.is_alive():
            reader.join(timeout=0.2)
        if process.stdin is not None:
            process.stdin.close()
        if process.stdout is not None:
            process.stdout.close()
        if windows_job is not None:
            _close_windows_job(windows_job)

    if timed_out:
        return {
            "status": "timeout",
            "error": f"isolated Qwen worker exceeded {timeout:.3f}s",
        }
    if read_error is not None:
        return {
            "status": "error",
            "error": f"isolated Qwen worker protocol failed: {type(read_error).__name__}: "
            f"{read_error}",
        }
    if not output_line:
        return {
            "status": "error",
            "error": f"isolated Qwen worker exited without a response ({process.returncode})",
        }
    encoded_output = output_line.encode("utf-8", errors="replace")
    if len(encoded_output) > _WORKER_MAX_RESPONSE_BYTES or not output_line.endswith("\n"):
        return {
            "status": "error",
            "error": (
                "isolated Qwen worker response exceeded the fixed "
                f"{_WORKER_MAX_RESPONSE_BYTES}-byte transport boundary"
            ),
        }
    try:
        envelope = json.loads(output_line)
    except json.JSONDecodeError as exc:
        return {
            "status": "error",
            "error": f"isolated Qwen worker returned invalid JSON: {exc}",
        }
    if not isinstance(envelope, dict) or not isinstance(envelope.get("ok"), bool):
        return {"status": "error", "error": "isolated Qwen worker returned a bad envelope"}
    if envelope["ok"]:
        return envelope.get("result")
    error_type = str(envelope.get("error_type") or "WorkerError")
    error = str(envelope.get("error") or "unknown worker failure")
    return {"status": "error", "error": f"{error_type}: {error}"}


def _worker_environment() -> dict[str, str]:
    """Remove unrelated host credentials from the trusted parser subprocess."""

    environment = os.environ.copy()
    runtime_scripts = os.path.dirname(os.path.abspath(sys.executable))
    inherited_path = environment.get("PATH", "")
    environment["PATH"] = os.pathsep.join(
        value for value in (runtime_scripts, inherited_path) if value
    )
    exact_sensitive = {
        "ALL_PROXY",
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "NO_PROXY",
        "SSH_AUTH_SOCK",
        "GPG_AGENT_INFO",
    }
    sensitive_prefixes = (
        "OPENAI_",
        "ANTHROPIC_",
        "AWS_",
        "AZURE_",
        "GOOGLE_",
        "GCP_",
        "GITHUB_",
        "GITLAB_",
        "DOCKER_",
        "KUBE",
    )
    sensitive_terms = ("API_KEY", "PASSWORD", "PRIVATE_KEY", "SECRET", "TOKEN", "CREDENTIAL")
    for key in tuple(environment):
        normalized = key.upper()
        if (
            normalized in exact_sensitive
            or normalized.startswith(sensitive_prefixes)
            or any(term in normalized for term in sensitive_terms)
        ):
            environment.pop(key, None)
    # The pinned event-log parser has an opt-in priority-preserving return-size
    # gate.  Enabling it prevents a 50k-record result from consuming the whole
    # model token budget before the investigator can interpret any evidence.
    environment["SIFT_EVENT_LOG_FORCE_BUDGET"] = "1"
    environment["SIFT_EVENT_LOG_MAX_RETURN_BYTES"] = str(_EVENT_LOG_MAX_RETURN_BYTES)
    return environment


def _terminate_worker_tree(process: subprocess.Popen[str], windows_job: int | None) -> int | None:
    """Terminate the worker and all descendants without invoking a command shell."""

    if os.name == "nt":
        if windows_job is not None:
            _terminate_windows_job(windows_job)
            # KILL_ON_JOB_CLOSE is the fallback if explicit termination failed.
            _close_windows_job(windows_job)
        else:
            with contextlib.suppress(OSError):
                process.kill()
        return None
    with contextlib.suppress(ProcessLookupError):
        os.killpg(process.pid, signal.SIGKILL)
    return windows_job


def _assign_windows_kill_job(process: subprocess.Popen[str]) -> int:
    """Assign a waiting worker to a kill-on-close Windows Job Object."""

    import ctypes
    from ctypes import wintypes

    class JobBasicLimits(ctypes.Structure):
        _fields_ = [
            ("PerProcessUserTimeLimit", ctypes.c_longlong),
            ("PerJobUserTimeLimit", ctypes.c_longlong),
            ("LimitFlags", wintypes.DWORD),
            ("MinimumWorkingSetSize", ctypes.c_size_t),
            ("MaximumWorkingSetSize", ctypes.c_size_t),
            ("ActiveProcessLimit", wintypes.DWORD),
            ("Affinity", ctypes.c_size_t),
            ("PriorityClass", wintypes.DWORD),
            ("SchedulingClass", wintypes.DWORD),
        ]

    class IoCounters(ctypes.Structure):
        _fields_ = [
            ("ReadOperationCount", ctypes.c_ulonglong),
            ("WriteOperationCount", ctypes.c_ulonglong),
            ("OtherOperationCount", ctypes.c_ulonglong),
            ("ReadTransferCount", ctypes.c_ulonglong),
            ("WriteTransferCount", ctypes.c_ulonglong),
            ("OtherTransferCount", ctypes.c_ulonglong),
        ]

    class ExtendedLimitInformation(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", JobBasicLimits),
            ("IoInfo", IoCounters),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryUsed", ctypes.c_size_t),
            ("PeakJobMemoryUsed", ctypes.c_size_t),
        ]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    kernel32.CreateJobObjectW.restype = wintypes.HANDLE
    kernel32.SetInformationJobObject.argtypes = [
        wintypes.HANDLE,
        ctypes.c_int,
        ctypes.c_void_p,
        wintypes.DWORD,
    ]
    kernel32.SetInformationJobObject.restype = wintypes.BOOL
    kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    kernel32.AssignProcessToJobObject.restype = wintypes.BOOL

    job = kernel32.CreateJobObjectW(None, None)
    if not job:
        raise ctypes.WinError(ctypes.get_last_error())
    information = ExtendedLimitInformation()
    information.BasicLimitInformation.LimitFlags = 0x00002000  # KILL_ON_JOB_CLOSE
    if not kernel32.SetInformationJobObject(
        job,
        9,  # JobObjectExtendedLimitInformation
        ctypes.byref(information),
        ctypes.sizeof(information),
    ):
        error = ctypes.WinError(ctypes.get_last_error())
        kernel32.CloseHandle(job)
        raise error
    process_handle = wintypes.HANDLE(int(process._handle))  # type: ignore[attr-defined]
    if not kernel32.AssignProcessToJobObject(job, process_handle):
        error = ctypes.WinError(ctypes.get_last_error())
        kernel32.CloseHandle(job)
        raise error
    return int(job)


def _terminate_windows_job(job: int) -> None:
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
    kernel32.TerminateJobObject.restype = wintypes.BOOL
    kernel32.TerminateJobObject(wintypes.HANDLE(job), 1)


def _close_windows_job(job: int) -> None:
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    kernel32.CloseHandle(wintypes.HANDLE(job))


def _tsk_executor(
    tool_name: str,
    disk_path: str,
    budget: RunBudget | None,
    *,
    filesystem_offset: int | None = None,
) -> ToolExecutor:
    sector_offset: int | None = None
    if filesystem_offset is not None:
        if tool_name != "fsstat":
            raise ValueError("Only fsstat accepts a filesystem offset")
        if filesystem_offset < 0 or filesystem_offset % 512:
            raise ValueError("Filesystem offset must be a non-negative multiple of 512 bytes")
        sector_offset = filesystem_offset // 512

    def execute(arguments: dict[str, JsonValue]) -> Any:
        spec: dict[str, Any] = {
            "action": "tsk",
            "tool": tool_name,
            "evidence_path": disk_path,
            "arguments": arguments,
        }
        if sector_offset is not None:
            spec["sector_offset"] = sector_offset
        return _run_qwen_worker(
            spec,
            budget,
        )

    return execute


def tool_catalog(registry: ToolRegistry) -> str:
    """Return a compact, deterministic catalog for the opening prompt."""

    catalog = [
        {
            "name": name,
            "description": registry.definition(name).description,
            "families": list(registry.definition(name).families),
        }
        for name in registry.names
    ]
    return json.dumps(catalog, ensure_ascii=False, sort_keys=True)
