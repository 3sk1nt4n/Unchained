# Reproducible Python environment

The flagship environment is official CPython 3.11.9 on Windows AMD64. The
project requires `>=3.11,<3.12`. The validated base interpreter is:

```text
%LOCALAPPDATA%\Programs\Python\Python311\python.exe
```

Two clean virtual environments were created outside OneDrive:

```text
%LOCALAPPDATA%\venvs\sentinel-unchained-py311
%LOCALAPPDATA%\venvs\sentinel-unchained-py311-lockcheck
```

Both report CPython 3.11.9 AMD64 and pass `pip check`. The C2 commit snapshot
passed 123 tests. Gate A commit `6e696a0` passes 128 tests, Ruff check, Ruff
format check, wheel build, `vol -h`, the exact pinned Qwen catalog smoke, and
real `vol_pstree`, `vol_psscan`, and high-volume `vol_netscan` execution. These
are local operational proofs. They are not a public timestamp, scored result,
or authentic GPT-5.6 run.

## Dependency records

The files have distinct jobs:

- `bootstrap.txt` pins pip, setuptools, build, and wheel so environment creation
  does not drift before project resolution.
- `constraints.windows-amd64-cp311.txt` is the conventional exact-version pip
  constraint input for this validated target.
- `pylock.windows-amd64-cp311.toml` is the pip 25.3 platform lock with source
  URLs, hashes, and the exact VCS commit. It is the stronger provenance record.

The `pylock` is not a legacy requirements file and must not be passed to
`pip install -r`. The runtime proof bundle records its relative path, SHA-256,
target, and whether the installed distribution versions match it.

Neither the constraints nor the lock is claimed to be portable to another
Python version, architecture, or operating system.

## Reproduce the primary environment

Run from the repository root in PowerShell:

```powershell
$venv = "$env:LOCALAPPDATA\venvs\sentinel-unchained-py311"
py -3.11 -m venv $venv
$python = "$venv\Scripts\python.exe"
$env:PIP_REQUIRE_VIRTUALENV = "true"
& $python -m pip install -r requirements/bootstrap.txt
& $python -m pip install -c requirements/constraints.windows-amd64-cp311.txt -e ".[dev]"
& $python -m pip check
```

For an independent clean resolution check:

```powershell
$venv = "$env:LOCALAPPDATA\venvs\sentinel-unchained-py311-lockcheck"
py -3.11 -m venv $venv
$python = "$venv\Scripts\python.exe"
$env:PIP_REQUIRE_VIRTUALENV = "true"
& $python -m pip install -r requirements/bootstrap.txt
& $python -m pip install -c requirements/constraints.windows-amd64-cp311.txt -e ".[dev]"
& $python -m pip check
```

Do not install this proof environment into the repository's OneDrive tree or a
mixed global interpreter.

## Re-run the validated gate

```powershell
$python = "$env:LOCALAPPDATA\venvs\sentinel-unchained-py311\Scripts\python.exe"
& $python --version
& $python -m pip check
& $python -m pytest
& $python -m ruff check .
& $python -m ruff format --check .
& $python -m build
& "$env:LOCALAPPDATA\venvs\sentinel-unchained-py311\Scripts\vol.exe" -h
& $python -c "from unchained.tools import _load_qwen_catalog; c=_load_qwen_catalog(None); print(len(c['direct']), len(c['volatility_plugins']))"
```

The current expected catalog output is:

```text
25 5
```

The native execution gate is also locally green. The official DC01 memory
archive was acquired and retained outside the repository. Its 561,424,278-byte
archive matches publisher MD5
`64A4E2CB47138084A5C2878066B2D7B1` and has SHA-256
`86658D85D8254E8D30DCCC4F50D9C2A8B550A101D2E78A6D932316849E37AD80`.
The extracted 2,147,483,648-byte memory image has SHA-256
`8079A7459B1739CAF7D4FBF6DDE5EB0AE7A9D24DBDE657DEBF4D5202C8DC6B62`.
`windows.info` resolved symbols, the sealed registry exposed 14 Windows-memory
tools, and the authoritative post-sanitizer process batch
`gate-a-final-20260715T015251Z` completed in 5,968 ms. `vol_pstree` returned 40
records in 15,277 accepted bytes with SHA-256
`E2E70D5164939F5A735C450ECC0F2C268E48F22AE4A4DAB76A92FA67F04ECAC6`.
`vol_psscan` returned 72 records in 16,526 accepted bytes with SHA-256
`836951C95FDCC131064B52CFC229BB3753E389567FCB534174AC3F40D14A7FE4`.
Both contain `E001`, contain no runner-local path, and preserve custody.

The first `vol_netscan` attempt produced an honest error receipt because its
legitimate response exceeded the old 2,000,000-byte worker bound. After raising
that fixed bound to 16,000,000 bytes, regression run
`gate-a-netscan-20260715T014947Z` returned 19,685 records. The complete sanitized
accepted output is 3,961,843 bytes with SHA-256
`EFCED1AF66F99EC2064D14F30A5F018D90E5C169027672BE9E3C0110122CB421`.
It contains `E001`, contains no private evidence path, and custody matched.

The full accepted output is retained content-addressably. The deterministic
delivery-path check produced a 65,536-byte candidate investigator view
containing 55,732 native-order prefix characters, the complete accepted byte
count and SHA-256, and `model_view_complete=false`. No investigator or model
received that payload because no model was invoked. The audit and fresh-review
receipt uses a separate exact prefix capped at 2,048 bytes.

The private worker recursively applies the same path scrub to successful values
and exception strings. Matching is case-insensitive so Windows case variants
cannot leak. A subprocess regression proves the error path replaces a
case-variant private path with the sealed public evidence ID before the parent
accepts the receipt. This deterministic test invokes no investigator, model, or
API.

The archive, extracted image, and smoke artifacts remain outside the
repository. This is local pre-freeze Gate A proof, not a public proof bundle or
scored model run. No model or API was used for the native smokes.

The preferred Windows memory route remains the existing reviewed typed adapter
over the cross-platform `vol` console command. Do not mandate a direct
Volatility Python API rewrite unless a real smoke test first reproduces a
blocking incompatibility in that route.

## Verify a finalized proof bundle

Base integrity verification accepts the terminal state the bundle honestly
declares:

```powershell
& $python -m unchained verify-run C:\path\to\run-bundle
```

Submission-strength verification additionally requires a complete lifecycle
and authentic provider-returned GPT-5.6 receipts:

```powershell
& $python -m unchained verify-run C:\path\to\run-bundle `
    --require-complete --require-live-gpt56
```

The retained empty-evidence synthetic bundle passes base integrity as
`INVALID` and correctly fails the strict command. It is not an authentic or
complete run.

## Regenerate the platform lock

Regenerate only from a clean CPython 3.11 Windows AMD64 environment:

```powershell
& $python -m pip lock ".[dev]" -o pylock.toml
Move-Item .\pylock.toml .\requirements\pylock.windows-amd64-cp311.toml -Force
```

pip 25.3 records the local project relative to the output file. After moving
the generated file into `requirements/`, change only the generated
`[packages.directory] path` from `"."` to `".."`; leave every resolved URL,
VCS commit ID, version, and hash untouched. This narrow path adjustment is
required because pip 25.3 errors when asked to emit the local-project lock
directly into a child directory.

Acceptance requires successful clean resolution, `pip check`, the full test
suite, Ruff check and format, wheel build, a second-environment install check,
catalog discovery, `vol -h`, and one real Windows memory plugin. Every item is
now locally green. Public timestamping, experiment freeze, API/model execution,
disclosed frozen-reference scoring, and submission remain separate gates.

A future Ubuntu lock must be resolved and verified on the named Ubuntu/Python
target and committed as a distinct file. Never generate a claimed Windows or
Ubuntu lock from a mixed global environment.
