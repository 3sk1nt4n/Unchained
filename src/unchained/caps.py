"""Central, thread-safe hard caps for tool, token, time, and dollar usage."""

from __future__ import annotations

import math
import os
import threading
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from enum import StrEnum

from .models import JsonValue, ModelUsage


class CapKind(StrEnum):
    TOOL_CALLS = "MAX_TOOL_CALLS"
    TOTAL_TOKENS = "MAX_TOTAL_TOKENS"
    WALL_SECONDS = "MAX_WALL_SECONDS"
    COST_USD = "MAX_COST_USD"


@dataclass(frozen=True, slots=True)
class CapConfig:
    """Validated hard-limit and price configuration."""

    max_tool_calls: int = 60
    max_total_tokens: int = 400_000
    max_wall_seconds: float = 1_800.0
    max_cost_usd: float = 10.0
    input_usd_per_million: float = 5.0
    cached_input_usd_per_million: float = 0.50
    cache_write_usd_per_million: float = 6.25
    output_usd_per_million: float = 30.0

    @classmethod
    def from_env(cls, profile: str = "default") -> CapConfig:
        """Load requested caps, accepting the exact prompt names and prefixed aliases."""

        base = cls() if profile == "default" else cls(20, 100_000, 600.0, 2.50)

        def env(name: str) -> str | None:
            return os.getenv(name) or os.getenv(f"UNCHAINED_{name}")

        def integer(name: str, fallback: int, minimum: int) -> int:
            raw = env(name)
            value = fallback if raw is None else int(raw)
            if value < minimum:
                raise ValueError(f"{name} must be >= {minimum}")
            return value

        def number(name: str, fallback: float, minimum: float) -> float:
            raw = env(name)
            value = fallback if raw is None else float(raw)
            if not math.isfinite(value) or value < minimum:
                raise ValueError(f"{name} must be >= {minimum}")
            return value

        return cls(
            max_tool_calls=integer("MAX_TOOL_CALLS", base.max_tool_calls, 1),
            max_total_tokens=integer("MAX_TOTAL_TOKENS", base.max_total_tokens, 1),
            max_wall_seconds=number("MAX_WALL_SECONDS", base.max_wall_seconds, 0.001),
            max_cost_usd=number("MAX_COST_USD", base.max_cost_usd, 0.0),
            # The tested GPT-5.6 Sol price table is code-owned. Environment
            # input may tighten/relax caps, but cannot underprice observed use.
            input_usd_per_million=base.input_usd_per_million,
            cached_input_usd_per_million=base.cached_input_usd_per_million,
            cache_write_usd_per_million=base.cache_write_usd_per_million,
            output_usd_per_million=base.output_usd_per_million,
        )


@dataclass(frozen=True, slots=True)
class BudgetSnapshot:
    tool_calls: int
    input_tokens: int
    cached_input_tokens: int
    cache_write_tokens: int
    output_tokens: int
    total_tokens: int
    elapsed_seconds: float
    estimated_cost_usd: float
    fired: str | None

    def public_dict(self) -> dict[str, JsonValue]:
        return asdict(self)


class CapExceeded(RuntimeError):
    """Raised exactly once a configured hard cap has fired."""

    def __init__(self, kind: CapKind, detail: str, snapshot: BudgetSnapshot) -> None:
        super().__init__(f"{kind.value}: {detail}")
        self.kind = kind
        self.detail = detail
        self.snapshot = snapshot


class RunBudget:
    """Atomically accounts for a single run; safe for the six-call opening batch."""

    def __init__(
        self,
        config: CapConfig,
        *,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.config = config
        self._clock = clock
        self._started = clock()
        self._lock = threading.Lock()
        self._tool_calls = 0
        self._input_tokens = 0
        self._cached_input_tokens = 0
        self._cache_write_tokens = 0
        self._output_tokens = 0
        self._total_tokens = 0
        self._cost_usd = 0.0
        self._fired: CapKind | None = None
        self._fired_detail = ""

    @property
    def fired(self) -> CapKind | None:
        with self._lock:
            return self._fired

    def _snapshot_unlocked(self) -> BudgetSnapshot:
        return BudgetSnapshot(
            tool_calls=self._tool_calls,
            input_tokens=self._input_tokens,
            cached_input_tokens=self._cached_input_tokens,
            cache_write_tokens=self._cache_write_tokens,
            output_tokens=self._output_tokens,
            total_tokens=self._total_tokens,
            elapsed_seconds=max(0.0, self._clock() - self._started),
            estimated_cost_usd=self._cost_usd,
            fired=self._fired.value if self._fired else None,
        )

    def snapshot(self) -> BudgetSnapshot:
        with self._lock:
            return self._snapshot_unlocked()

    def _raise_fired_unlocked(self) -> None:
        if self._fired is not None:
            raise CapExceeded(self._fired, self._fired_detail, self._snapshot_unlocked())

    def _fire_unlocked(self, kind: CapKind, detail: str) -> None:
        if self._fired is None:
            self._fired = kind
            self._fired_detail = detail
        self._raise_fired_unlocked()

    def check(self) -> None:
        """Fail immediately after the wall deadline or any previously fired cap."""

        with self._lock:
            self._raise_fired_unlocked()
            elapsed = self._clock() - self._started
            if elapsed >= self.config.max_wall_seconds:
                self._fire_unlocked(
                    CapKind.WALL_SECONDS,
                    f"elapsed {elapsed:.3f}s >= {self.config.max_wall_seconds:.3f}s",
                )

    def reserve_tool_calls(self, count: int = 1) -> None:
        """Reserve calls before launch so parallel workers cannot race past the cap."""

        if count < 1:
            raise ValueError("tool call reservation must be positive")
        with self._lock:
            self._raise_fired_unlocked()
            elapsed = self._clock() - self._started
            if elapsed >= self.config.max_wall_seconds:
                self._fire_unlocked(
                    CapKind.WALL_SECONDS,
                    "wall deadline reached before tool launch",
                )
            attempted = self._tool_calls + count
            if attempted > self.config.max_tool_calls:
                self._fire_unlocked(
                    CapKind.TOOL_CALLS,
                    f"reservation would reach {attempted} > {self.config.max_tool_calls}",
                )
            self._tool_calls = attempted

    def record_model_usage(self, usage: ModelUsage, model_id: str = "gpt-5.6") -> float:
        """Charge observed response usage and return that response's estimated cost."""

        call_cost = estimate_usage_cost(self.config, usage, model_id)
        with self._lock:
            self._raise_fired_unlocked()
            self._input_tokens += usage.input_tokens
            self._cached_input_tokens += usage.cached_input_tokens
            self._cache_write_tokens += usage.cache_write_tokens
            self._output_tokens += usage.output_tokens
            self._total_tokens += usage.total_tokens
            self._cost_usd += call_cost
            total = self._total_tokens
            if total > self.config.max_total_tokens:
                self._fire_unlocked(
                    CapKind.TOTAL_TOKENS,
                    f"observed {total} > {self.config.max_total_tokens}",
                )
            if self._cost_usd > self.config.max_cost_usd:
                self._fire_unlocked(
                    CapKind.COST_USD,
                    f"estimated ${self._cost_usd:.6f} > ${self.config.max_cost_usd:.6f}",
                )
        return call_cost

    def max_output_tokens(self, preferred: int = 16_384) -> int:
        """Bound one response by the still-observed total-token allowance."""

        with self._lock:
            remaining = self.config.max_total_tokens - self._total_tokens
            return max(1, min(preferred, remaining))

    def remaining_wall_seconds(self) -> float:
        """Return positive time remaining, firing the wall cap at the deadline."""

        with self._lock:
            self._raise_fired_unlocked()
            remaining = self.config.max_wall_seconds - (self._clock() - self._started)
            if remaining <= 0:
                self._fire_unlocked(CapKind.WALL_SECONDS, "wall deadline reached")
            return remaining

    def prepare_model_request(
        self,
        estimated_input_tokens: int,
        preferred_output_tokens: int,
        model_id: str,
        *,
        minimum_output_tokens: int = 1,
    ) -> int:
        """Conservatively bound a pending response by remaining tokens and dollars."""

        estimated_input_tokens = max(1, estimated_input_tokens)
        preferred_output_tokens = max(1, preferred_output_tokens)
        if (
            isinstance(minimum_output_tokens, bool)
            or not isinstance(minimum_output_tokens, int)
            or minimum_output_tokens < 1
        ):
            raise ValueError("minimum_output_tokens must be a positive integer")
        if minimum_output_tokens > preferred_output_tokens:
            raise ValueError("minimum_output_tokens cannot exceed preferred_output_tokens")
        with self._lock:
            self._raise_fired_unlocked()
            elapsed = self._clock() - self._started
            if elapsed >= self.config.max_wall_seconds:
                self._fire_unlocked(CapKind.WALL_SECONDS, "wall deadline reached")
            remaining_tokens = (
                self.config.max_total_tokens - self._total_tokens - estimated_input_tokens
            )
            if remaining_tokens < 1:
                self._fire_unlocked(
                    CapKind.TOTAL_TOKENS,
                    "conservative request estimate leaves no response-token budget",
                )

            # Implicit prompt caching may miss, so ordinary uncached input is
            # still the safe preflight price. Provider-reported reads/writes
            # are reconciled from observed response usage below.
            input_usage = ModelUsage(input_tokens=estimated_input_tokens)
            estimated_input_cost = estimate_usage_cost(self.config, input_usage, model_id)
            remaining_cost = self.config.max_cost_usd - self._cost_usd - estimated_input_cost
            if remaining_cost <= 0:
                self._fire_unlocked(
                    CapKind.COST_USD,
                    "conservative request estimate leaves no response-cost budget",
                )
            output_multiplier = (
                1.5 if model_id.startswith("gpt-5.6") and estimated_input_tokens > 272_000 else 1.0
            )
            output_rate = self.config.output_usd_per_million * output_multiplier
            if output_rate == 0:
                cost_limited_tokens = remaining_tokens
            else:
                cost_limited_tokens = int(remaining_cost * 1_000_000 / output_rate)
            if cost_limited_tokens < 1:
                self._fire_unlocked(
                    CapKind.COST_USD,
                    "remaining estimated cost permits no response token",
                )
            allowed = min(preferred_output_tokens, remaining_tokens, cost_limited_tokens)
            if allowed < minimum_output_tokens:
                if remaining_tokens < minimum_output_tokens:
                    self._fire_unlocked(
                        CapKind.TOTAL_TOKENS,
                        "conservative request estimate cannot preserve the phase minimum "
                        f"of {minimum_output_tokens} output tokens",
                    )
                self._fire_unlocked(
                    CapKind.COST_USD,
                    "remaining estimated cost cannot preserve the phase minimum "
                    f"of {minimum_output_tokens} output tokens",
                )
            return allowed


def estimate_usage_cost(
    config: CapConfig,
    usage: ModelUsage,
    model_id: str = "gpt-5.6",
) -> float:
    """Estimate one response cost, including GPT-5.6 Sol long-context pricing."""

    _validate_usage(usage)

    uncached = max(
        0,
        usage.input_tokens - usage.cached_input_tokens - usage.cache_write_tokens,
    )
    long_context = model_id.startswith("gpt-5.6") and usage.input_tokens > 272_000
    input_multiplier = 2.0 if long_context else 1.0
    output_multiplier = 1.5 if long_context else 1.0
    return (
        uncached * config.input_usd_per_million * input_multiplier
        + usage.cached_input_tokens * config.cached_input_usd_per_million * input_multiplier
        + usage.cache_write_tokens * config.cache_write_usd_per_million * input_multiplier
        + usage.output_tokens * config.output_usd_per_million * output_multiplier
    ) / 1_000_000


def _validate_usage(usage: ModelUsage) -> None:
    """Reject malformed provider accounting instead of undercharging a hard cap."""

    for field in (
        "input_tokens",
        "output_tokens",
        "cached_input_tokens",
        "cache_write_tokens",
        "reasoning_tokens",
        "provider_total_tokens",
    ):
        value = getattr(usage, field)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"model usage {field} must be a nonnegative integer")
    component_total = usage.input_tokens + usage.output_tokens
    if usage.provider_total_tokens not in {0, component_total}:
        raise ValueError(
            "model usage provider_total_tokens must equal input_tokens + output_tokens"
        )
    if usage.cached_input_tokens + usage.cache_write_tokens > usage.input_tokens:
        raise ValueError("model usage cache read/write tokens must not exceed input_tokens")
