<#
.SYNOPSIS
    Preflight and, only with -Execute, run the frozen Windows-memory flagship.

.DESCRIPTION
    This wrapper is intentionally stricter than the general Unchained CLI. It
    requires explicit evidence, credential-file, and output-directory inputs;
    enforces the frozen DC01 profile and digest; requires a clean Git worktree
    whose HEAD is the experiment freeze tag; fixes bounded completion caps; and
    suppresses private paths and credentials from console output.

    Without -Execute it performs preflight only. The hidden test-fixture seam
    can exercise validation without reading evidence or credentials, but is
    categorically forbidden from executing a model run.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$EvidenceDirectory,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$OpenAIKeyFile,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$OutputDirectory,

    [string]$PythonPath = "",

    [ValidatePattern("^[A-Za-z0-9._-]+$")]
    [string]$FreezeTag = "experiment-freeze-v1",

    [switch]$Execute,
    [switch]$OpenViewer,

    [Parameter(DontShow = $true)]
    [string]$TestFixtureDirectory = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ExpectedPythonImplementation = "CPython"
$ExpectedPythonVersion = "3.11.9"
$ExpectedModel = "gpt-5.6"
$ExpectedEvidenceId = "E001"
$ExpectedEvidenceBytes = 2147483648
$ExpectedEvidenceSha256 = "8079a7459b1739caf7d4fbf6dde5eb0ae7a9d24dbde657debf4d5202c8dc6b62"
$ExpectedDependencyLockPath = "requirements/pylock.windows-amd64-cp311.toml"
$ExpectedDependencyLockSha256 = "2ab5957a30eba0ebaa24775b8e78d381800ef003be201e6acf932aba724dfef7"
$ExpectedDependencyLockTarget = "windows-amd64-cp311"
$ExpectedCanonicalOriginUrl = "https://github.com/3sk1nt4n/Unchained.git"
$RemoteVisibilityClaim = (
    "public remote tag visibility is chronology evidence only; it does not authenticate " +
    "server time, provide a signed timestamp, or establish cryptographic provenance"
)
$MetricsRelativePath = "docs/runs/dc01-sol-complete-metrics.json"
$FrozenCaps = [ordered]@{
    max_tool_calls = 60
    max_total_tokens = 400000
    max_wall_seconds = 1800.0
    max_cost_usd = 10.0
}

$RepositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
$AllowedFlagshipProgress = [Collections.Generic.HashSet[string]]::new(
    [StringComparer]::Ordinal
)
foreach ($line in @(
    "[sentinel] checking GPT-5.6 configuration before evidence I/O",
    "[sentinel] profiling and hashing the evidence set",
    "[sentinel] route ready: windows/memory-only; 1 evidence item(s)",
    "[sentinel] loading route-valid typed forensic tools",
    (
        "[sentinel] starting GPT-5.6 opening book; bounded profile and observations may be " +
        "sent to OpenAI, original evidence bytes stay local"
    ),
    "[sentinel] performing final full SHA-256 custody verification",
    "[sentinel] content-addressed proof bundle verified"
)) {
    [void]$AllowedFlagshipProgress.Add($line)
}

function Assert-FlagshipCondition {
    param(
        [Parameter(Mandatory = $true)]
        [bool]$Condition,
        [Parameter(Mandatory = $true)]
        [string]$Message
    )

    if (-not $Condition) {
        throw [InvalidOperationException]::new($Message)
    }
}

function ConvertFrom-FlagshipJson {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Text,
        [Parameter(Mandatory = $true)]
        [string]$Label
    )

    try {
        return $Text | ConvertFrom-Json -ErrorAction Stop
    }
    catch {
        throw [InvalidOperationException]::new("$Label did not return valid JSON.")
    }
}

function Write-SanitizedFlagshipProgress {
    param(
        [Parameter(Mandatory = $false)]
        [AllowNull()]
        $Record
    )

    if ($null -eq $Record) {
        return
    }
    if ($Record -is [Management.Automation.ErrorRecord]) {
        $line = [string]$Record.Exception.Message
    }
    else {
        $line = [string]$Record
    }
    $line = $line.TrimEnd([char[]]"`r`n")
    if (
        $AllowedFlagshipProgress.Contains($line) -or
        $line -match '^\[sentinel\] model pipeline finished with status (COMPLETE|PARTIAL|FATAL|INVALID)$'
    ) {
        Write-Output $line
    }
}

function Read-FlagshipJsonFile {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        [string]$Label
    )

    try {
        $raw = Get-Content -LiteralPath $Path -Raw -Encoding UTF8 -ErrorAction Stop
    }
    catch {
        throw [InvalidOperationException]::new("$Label fixture is unavailable.")
    }
    return ConvertFrom-FlagshipJson -Text $raw -Label $Label
}

function Invoke-CapturedPython {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Executable,
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments,
        [Parameter(Mandatory = $true)]
        [string]$FailureMessage
    )

    try {
        $lines = @(& $Executable @Arguments 2>$null)
        $exitCode = $LASTEXITCODE
    }
    catch {
        throw [InvalidOperationException]::new($FailureMessage)
    }
    if ($exitCode -ne 0) {
        throw [InvalidOperationException]::new($FailureMessage)
    }
    return ($lines -join [Environment]::NewLine)
}

function Resolve-ExistingLeafFile {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Value,
        [Parameter(Mandatory = $true)]
        [string]$FailureMessage
    )

    try {
        $resolved = (Resolve-Path -LiteralPath $Value -ErrorAction Stop).Path
        $item = Get-Item -LiteralPath $resolved -Force -ErrorAction Stop
    }
    catch {
        throw [InvalidOperationException]::new($FailureMessage)
    }
    if (-not $item.PSIsContainer -and -not ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
        return $resolved
    }
    throw [InvalidOperationException]::new($FailureMessage)
}

function Resolve-ExistingRealDirectory {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Value,
        [Parameter(Mandatory = $true)]
        [string]$FailureMessage
    )

    try {
        $resolved = (Resolve-Path -LiteralPath $Value -ErrorAction Stop).Path
        $item = Get-Item -LiteralPath $resolved -Force -ErrorAction Stop
    }
    catch {
        throw [InvalidOperationException]::new($FailureMessage)
    }
    if ($item.PSIsContainer -and -not ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
        return $resolved
    }
    throw [InvalidOperationException]::new($FailureMessage)
}

function Resolve-OutputRoot {
    param([Parameter(Mandatory = $true)][string]$Value)

    try {
        if ([IO.Path]::IsPathRooted($Value)) {
            $resolved = [IO.Path]::GetFullPath($Value)
        }
        else {
            $resolved = [IO.Path]::GetFullPath((Join-Path (Get-Location).Path $Value))
        }
        if (Test-Path -LiteralPath $resolved) {
            $item = Get-Item -LiteralPath $resolved -Force -ErrorAction Stop
            if (-not $item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
                throw [InvalidOperationException]::new("invalid output target")
            }
        }
        return $resolved
    }
    catch {
        throw [InvalidOperationException]::new(
            "OutputDirectory must resolve to a real directory target."
        )
    }
}

function Assert-NoReparseAncestors {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$FailureMessage
    )

    try {
        $probe = [IO.Path]::GetFullPath($Path)
        while (-not (Test-Path -LiteralPath $probe)) {
            $parent = [IO.Directory]::GetParent($probe)
            if ($null -eq $parent) {
                throw [InvalidOperationException]::new("no existing path ancestor")
            }
            $probe = $parent.FullName
        }
        while ($true) {
            $item = Get-Item -LiteralPath $probe -Force -ErrorAction Stop
            if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
                throw [InvalidOperationException]::new("reparse ancestor")
            }
            $parent = [IO.Directory]::GetParent($probe)
            if ($null -eq $parent) {
                break
            }
            $probe = $parent.FullName
        }
    }
    catch {
        throw [InvalidOperationException]::new($FailureMessage)
    }
}

function Test-IsSameOrChildPath {
    param(
        [Parameter(Mandatory = $true)][string]$Candidate,
        [Parameter(Mandatory = $true)][string]$Parent
    )

    $candidateFull = [IO.Path]::GetFullPath($Candidate).TrimEnd(
        [IO.Path]::DirectorySeparatorChar,
        [IO.Path]::AltDirectorySeparatorChar
    )
    $parentFull = [IO.Path]::GetFullPath($Parent).TrimEnd(
        [IO.Path]::DirectorySeparatorChar,
        [IO.Path]::AltDirectorySeparatorChar
    )
    if ($candidateFull.Equals($parentFull, [StringComparison]::OrdinalIgnoreCase)) {
        return $true
    }
    $parentPrefix = $parentFull + [IO.Path]::DirectorySeparatorChar
    return $candidateFull.StartsWith($parentPrefix, [StringComparison]::OrdinalIgnoreCase)
}

function Get-ActualGitGate {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string]$Tag
    )

    $headLines = @(& git -C $Root rev-parse HEAD 2>$null)
    Assert-FlagshipCondition ($LASTEXITCODE -eq 0 -and $headLines.Count -eq 1) `
        "Git HEAD is unavailable; freeze gate failed."
    $tagLines = @(& git -C $Root rev-parse --verify "$Tag^{commit}" 2>$null)
    Assert-FlagshipCondition ($LASTEXITCODE -eq 0 -and $tagLines.Count -eq 1) `
        "The required experiment freeze tag is unavailable."
    $statusLines = @(& git -C $Root status --porcelain=v1 --untracked-files=all 2>$null)
    Assert-FlagshipCondition ($LASTEXITCODE -eq 0) "Git worktree status is unavailable."
    return [pscustomobject]@{
        clean = ($statusLines.Count -eq 0)
        head = [string]$headLines[0]
        freeze_tag = $Tag
        tag_commit = [string]$tagLines[0]
    }
}

function Assert-PythonPreflight {
    param([Parameter(Mandatory = $true)]$PythonInfo)

    Assert-FlagshipCondition ($PythonInfo.implementation -eq $ExpectedPythonImplementation) `
        "Flagship requires the exact supported CPython implementation."
    Assert-FlagshipCondition ($PythonInfo.version -eq $ExpectedPythonVersion) `
        "Flagship requires exact CPython 3.11.9."
}

function Assert-FrozenSourcePreflight {
    param([Parameter(Mandatory = $true)]$SourceIdentity)

    Assert-FlagshipCondition (
        $SourceIdentity.implementation -eq $ExpectedPythonImplementation -and
        $SourceIdentity.version -eq $ExpectedPythonVersion -and
        $SourceIdentity.module_matches_frozen_repo -eq $true -and
        $SourceIdentity.distribution_source_matches_frozen_repo -eq $true -and
        $SourceIdentity.distribution_editable -eq $true
    ) "The imported Unchained package or installed distribution does not resolve to the frozen repository."
}

function Assert-DependencyLockPreflight {
    param([Parameter(Mandatory = $true)]$DependencyLock)

    Assert-FlagshipCondition (
        $DependencyLock.path -eq $ExpectedDependencyLockPath -and
        ([string]$DependencyLock.sha256).ToLowerInvariant() -eq
            $ExpectedDependencyLockSha256 -and
        $DependencyLock.target -eq $ExpectedDependencyLockTarget -and
        $DependencyLock.installed_versions_match -eq $true
    ) "Dependency lock path, digest, target, or installed-version parity differs from the freeze."
}

function Assert-DoctorPreflight {
    param([Parameter(Mandatory = $true)]$Doctor)

    Assert-FlagshipCondition ($Doctor.ready_for_live_run -eq $true) `
        "Doctor JSON is not ready for a live run."
    Assert-FlagshipCondition ($Doctor.configured_model -eq $ExpectedModel) `
        "Doctor did not confirm requested model gpt-5.6."
    Assert-FlagshipCondition ($Doctor.openai_api_key_source -eq "file") `
        "Doctor did not confirm the explicit credential-file source."
    Assert-FlagshipCondition ($Doctor.python -eq $ExpectedPythonVersion) `
        "Doctor did not run under exact CPython 3.11.9."
    Assert-FlagshipCondition ($Doctor.secrets_printed -eq $false) `
        "Doctor did not preserve the secret-output invariant."
}

function Assert-ProfilePreflight {
    param([Parameter(Mandatory = $true)]$ProfileEnvelope)

    $profile = $ProfileEnvelope.profile
    $evidence = @($profile.evidence)
    Assert-FlagshipCondition ($ProfileEnvelope.openai_called -eq $false) `
        "Profile preflight did not attest zero OpenAI calls."
    Assert-FlagshipCondition ($ProfileEnvelope.custody.match -eq $true) `
        "Profile preflight custody recheck failed."
    Assert-FlagshipCondition ($profile.os -eq "windows" -and $profile.shape -eq "memory-only") `
        "Flagship evidence must profile as Windows memory-only."
    Assert-FlagshipCondition ($evidence.Count -eq 1) `
        "Flagship evidence must contain exactly one public evidence item."
    $item = $evidence[0]
    Assert-FlagshipCondition (
        $item.evidence_id -eq $ExpectedEvidenceId -and
        $item.kind -eq "memory" -and
        $item.os_hint -eq "windows" -and
        [int64]$item.size -eq $ExpectedEvidenceBytes -and
        $item.available -eq $true -and
        $item.health -eq "ready" -and
        $item.symbols -eq "ready"
    ) "E001 is not a ready Windows-memory route with ready symbols."
    Assert-FlagshipCondition (
        ([string]$item.sha256).ToLowerInvariant() -eq $ExpectedEvidenceSha256 -and
        ([string]$profile.hashes.E001).ToLowerInvariant() -eq $ExpectedEvidenceSha256 -and
        ([string]$ProfileEnvelope.custody.hashes.E001).ToLowerInvariant() -eq
            $ExpectedEvidenceSha256
    ) "Evidence SHA-256 does not match the frozen flagship digest."
    Assert-FlagshipCondition (
        $profile.health.E001 -eq "ready" -and $profile.symbols.E001 -eq "ready"
    ) "The public E001 health/symbol maps are not ready."
}

function Assert-BenchmarkFreezePreflight {
    param([Parameter(Mandatory = $true)]$Freeze)

    Assert-FlagshipCondition (
        $Freeze.schema_version -eq 1 -and
        $Freeze.freeze_id -eq "sentinel-dc01-sol-v1" -and
        $Freeze.status -eq "READY" -and
        $Freeze.ready -eq $true -and
        @($Freeze.issues).Count -eq 0
    ) "Benchmark freeze gate did not authorize the scored primary."
}

function Assert-RemoteAnchorPreflight {
    param(
        [Parameter(Mandatory = $true)]$Freeze,
        [Parameter(Mandatory = $true)]$GitGate
    )

    Assert-BenchmarkFreezePreflight $Freeze
    $remote = $Freeze.remote_anchor
    Assert-FlagshipCondition (
        $remote.checked -eq $true -and
        $remote.visible -eq $true -and
        $remote.canonical_origin_url -eq $ExpectedCanonicalOriginUrl -and
        $remote.tag -eq $FreezeTag -and
        ([string]$remote.tag_object) -match "^[0-9a-f]{40}$" -and
        ([string]$remote.peeled_commit) -match "^[0-9a-f]{40}$" -and
        $remote.peeled_commit -eq $GitGate.head -and
        $remote.claim -eq $RemoteVisibilityClaim
    ) "The annotated freeze tag is not visibly bound to canonical origin."
}

function Assert-CapPreflight {
    param([Parameter(Mandatory = $true)]$Caps)

    Assert-FlagshipCondition (
        [int64]$Caps.max_tool_calls -eq $FrozenCaps.max_tool_calls -and
        [int64]$Caps.max_total_tokens -eq $FrozenCaps.max_total_tokens -and
        [double]$Caps.max_wall_seconds -eq $FrozenCaps.max_wall_seconds -and
        [double]$Caps.max_cost_usd -eq $FrozenCaps.max_cost_usd
    ) "Runtime cap configuration differs from the frozen bounded flagship caps."
}

function Assert-GitPreflight {
    param([Parameter(Mandatory = $true)]$GitGate)

    Assert-FlagshipCondition ($GitGate.clean -eq $true) `
        "Freeze gate requires a clean worktree with no uncommitted or untracked files."
    Assert-FlagshipCondition ($GitGate.freeze_tag -eq $FreezeTag) `
        "Freeze gate tag identity differs from the required experiment tag."
    Assert-FlagshipCondition (
        ([string]$GitGate.head) -match "^[0-9a-f]{40}$" -and
        $GitGate.head -eq $GitGate.tag_commit
    ) "Freeze gate requires committed HEAD to equal the experiment freeze tag."
}

function Assert-OnlyMetricsCreatedAfterValidation {
    param([Parameter(Mandatory = $true)]$GitGate)

    $headLines = @(& git -C $RepositoryRoot rev-parse HEAD 2>$null)
    $tagLines = @(& git -C $RepositoryRoot rev-parse --verify "$FreezeTag^{commit}" 2>$null)
    $statusLines = @(
        & git -C $RepositoryRoot status --porcelain=v1 --untracked-files=all 2>$null
    )
    $expectedStatus = "?? " + $MetricsRelativePath.Replace("\", "/")
    Assert-FlagshipCondition (
        $LASTEXITCODE -eq 0 -and
        $headLines.Count -eq 1 -and
        $tagLines.Count -eq 1 -and
        $headLines[0] -eq $GitGate.head -and
        $tagLines[0] -eq $GitGate.head -and
        $statusLines.Count -eq 1 -and
        $statusLines[0] -eq $expectedStatus
    ) "Repository changed after validation beyond the wrapper-created metrics artifact."
}

function Write-PreflightSummary {
    param([Parameter(Mandatory = $true)]$GitGate)

    Write-Output "FLAGSHIP PREFLIGHT"
    Write-Output "PASS  Runtime: CPython 3.11.9"
    Write-Output "PASS  Doctor JSON: ready; credential source=file; secrets printed=false"
    Write-Output "PASS  Model request: gpt-5.6"
    Write-Output (
        "PASS  Dependency lock: {0}; sha256={1}; target={2}; installed versions match" -f
        $ExpectedDependencyLockPath,
        $ExpectedDependencyLockSha256,
        $ExpectedDependencyLockTarget
    )
    Write-Output "PASS  Evidence route: windows / memory-only / E001 / health ready / symbols ready"
    Write-Output "PASS  Evidence bytes: $ExpectedEvidenceBytes"
    Write-Output "PASS  Evidence SHA-256: $ExpectedEvidenceSha256"
    Write-Output (
        "PASS  Freeze gate: tag={0}; commit={1}; worktree=clean" -f
        $GitGate.freeze_tag,
        $GitGate.head
    )
    $capLine = (
        "PASS  Frozen bounded caps: tools={0}; total_tokens={1}; wall_seconds={2}; " +
        "max_cost_usd={3}"
    ) -f @(
        $FrozenCaps.max_tool_calls,
        $FrozenCaps.max_total_tokens,
        $FrozenCaps.max_wall_seconds,
        $FrozenCaps.max_cost_usd
    )
    Write-Output $capLine
}

function Get-RunDirectoryNames {
    param([Parameter(Mandatory = $true)][string]$RunParent)

    try {
        if (-not (Test-Path -LiteralPath $RunParent)) {
            return @()
        }
        return @(
            Get-ChildItem -LiteralPath $RunParent -Directory -Force -ErrorAction Stop |
                ForEach-Object { $_.Name }
        )
    }
    catch {
        throw [InvalidOperationException]::new(
            "Output run inventory could not be read safely."
        )
    }
}

function Assert-BundleProfile {
    param([Parameter(Mandatory = $true)]$Profile)

    $envelope = [pscustomobject]@{
        profile = $Profile
        custody = [pscustomobject]@{ match = $true; hashes = $Profile.hashes }
        openai_called = $false
    }
    Assert-ProfilePreflight $envelope
}

function Write-SanitizedMetrics {
    param(
        [Parameter(Mandatory = $true)][string]$BundleDirectory,
        [Parameter(Mandatory = $true)]$Verification,
        [Parameter(Mandatory = $true)]$GitGate,
        [Parameter(Mandatory = $true)]$RemoteAnchor
    )

    $summary = Read-FlagshipJsonFile (Join-Path $BundleDirectory "summary.json") "Summary"
    $profile = Read-FlagshipJsonFile (Join-Path $BundleDirectory "profile.json") "Profile"
    $environment = Read-FlagshipJsonFile (Join-Path $BundleDirectory "environment.json") `
        "Environment"
    $manifest = Read-FlagshipJsonFile (Join-Path $BundleDirectory "manifest.json") "Manifest"

    Assert-BundleProfile $profile
    Assert-FlagshipCondition (
        $Verification.passed -eq $true -and
        $Verification.terminal.status -eq "COMPLETE" -and
        [int]$Verification.terminal.exit_code -eq 0
    ) "Strict live verification did not establish COMPLETE with exit code zero."
    Assert-FlagshipCondition (
        $summary.terminal.status -eq "COMPLETE" -and
        [int]$summary.terminal.exit_code -eq 0 -and
        $summary.custody.match -eq $true -and
        $summary.custody.mount_released -eq $true
    ) "Verified summary does not establish COMPLETE custody-safe termination."
    Assert-FlagshipCondition (
        $manifest.run_id -eq $Verification.run_id -and
        $summary.run_id -eq $Verification.run_id -and
        $manifest.terminal.status -eq "COMPLETE" -and
        [int]$manifest.terminal.exit_code -eq 0
    ) "Bundle identifiers or terminal metadata disagree after verification."
    Assert-FlagshipCondition (
        @($summary.model.requested_models).Count -eq 1 -and
        @($summary.model.requested_models)[0] -eq $ExpectedModel
    ) "Verified summary did not retain exactly the requested gpt-5.6 alias."
    Assert-FlagshipCondition (
        $environment.runtime.implementation -eq $ExpectedPythonImplementation -and
        $environment.runtime.python_version -eq $ExpectedPythonVersion -and
        $environment.project.git_commit -eq $GitGate.head -and
        $environment.project.git_dirty -eq $false -and
        $environment.model_configuration.requested_model -eq $ExpectedModel
    ) "Environment artifact differs from the frozen runtime or commit."
    Assert-CapPreflight $environment.caps
    Assert-DependencyLockPreflight $environment.dependency_lock

    try {
        $manifestPath = Join-Path $BundleDirectory "manifest.json"
        $manifestSha256 = (
            Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256 -ErrorAction Stop
        ).Hash.ToLowerInvariant()
        [int64]$bundleBytes = 0
        foreach (
            $file in Get-ChildItem -LiteralPath $BundleDirectory -File -Recurse -Force `
                -ErrorAction Stop
        ) {
            $bundleBytes += [int64]$file.Length
        }
    }
    catch {
        throw [InvalidOperationException]::new(
            "Verified bundle metrics could not be derived safely."
        )
    }

    $metrics = [ordered]@{
        schema_version = 1
        qualification = "VERIFIED_COMPLETE_RECORDED_LIVE_GPT56_LIFECYCLE"
        semantic_evaluation = "pending_frozen_two_axis_adjudication"
        run_id = $Verification.run_id
        freeze = [ordered]@{
            tag = $GitGate.freeze_tag
            commit = $GitGate.head
            worktree_clean_at_start = $true
            worktree_clean_after_run = $true
            canonical_origin_url = $RemoteAnchor.canonical_origin_url
            remote_tag_object = $RemoteAnchor.tag_object
            remote_peeled_commit = $RemoteAnchor.peeled_commit
            remote_visibility_checked_immediately_before_run = $true
            remote_visibility_claim = $RemoteAnchor.claim
        }
        dependency_lock = [ordered]@{
            path = $ExpectedDependencyLockPath
            sha256 = $ExpectedDependencyLockSha256
            target = $ExpectedDependencyLockTarget
            installed_versions_match = $true
        }
        evidence = [ordered]@{
            evidence_id = $ExpectedEvidenceId
            bytes = $ExpectedEvidenceBytes
            sha256 = $ExpectedEvidenceSha256
            os = "windows"
            shape = "memory-only"
            health = "ready"
            symbols = "ready"
        }
        model = $summary.model
        usage = $summary.usage
        tools = $summary.tools
        investigation = $summary.investigation
        time = $summary.time
        custody = $summary.custody
        caps = [ordered]@{
            profile = "default"
            max_tool_calls = $FrozenCaps.max_tool_calls
            max_total_tokens = $FrozenCaps.max_total_tokens
            max_wall_seconds = $FrozenCaps.max_wall_seconds
            max_cost_usd = $FrozenCaps.max_cost_usd
        }
        proof = [ordered]@{
            manifest_sha256 = $manifestSha256
            retained_bundle_bytes = $bundleBytes
            verified_artifacts = [int]$Verification.verified_artifacts
            verified_audit_entries = [int]$Verification.verified_audit_entries
            strict_complete = $true
            strict_recorded_live_gpt56 = $true
            provider_receipts_externally_authenticated = $false
            original_evidence_rehashed_by_offline_verifier = $false
        }
        privacy = [ordered]@{
            input_paths_recorded = $false
            credential_recorded = $false
        }
    }

    $metricsPath = Join-Path $RepositoryRoot $MetricsRelativePath
    Assert-FlagshipCondition (-not (Test-Path -LiteralPath $metricsPath)) `
        "Primary metrics artifact already exists; refusing to overwrite it."
    $metricsParent = Split-Path -Parent $metricsPath
    $temporary = "$metricsPath.$([Guid]::NewGuid().ToString('N')).tmp"
    try {
        New-Item -ItemType Directory -Path $metricsParent -Force -ErrorAction Stop | Out-Null
        $json = $metrics | ConvertTo-Json -Depth 12
        [IO.File]::WriteAllText($temporary, "$json`n", [Text.UTF8Encoding]::new($false))
        Move-Item -LiteralPath $temporary -Destination $metricsPath -ErrorAction Stop
    }
    catch {
        throw [InvalidOperationException]::new(
            "Sanitized primary metrics could not be written atomically."
        )
    }
    finally {
        if (Test-Path -LiteralPath $temporary) {
            Remove-Item -LiteralPath $temporary -Force -ErrorAction SilentlyContinue
        }
    }
}

if ($TestFixtureDirectory) {
    Assert-FlagshipCondition (-not $Execute) `
        "The test fixture seam cannot be used with -Execute."
    Assert-FlagshipCondition (-not $OpenViewer) `
        "The test fixture seam cannot open a viewer."
    $fixture = Resolve-ExistingRealDirectory $TestFixtureDirectory `
        "Test fixture directory is unavailable."
    $pythonInfo = Read-FlagshipJsonFile (Join-Path $fixture "python.json") "Python"
    $dependencyLock = Read-FlagshipJsonFile (Join-Path $fixture "dependency-lock.json") `
        "Dependency lock"
    $doctor = Read-FlagshipJsonFile (Join-Path $fixture "doctor.json") "Doctor"
    $profileEnvelope = Read-FlagshipJsonFile (Join-Path $fixture "profile.json") "Profile"
    $caps = Read-FlagshipJsonFile (Join-Path $fixture "caps.json") "Caps"
    $gitGate = Read-FlagshipJsonFile (Join-Path $fixture "git.json") "Git"

    Assert-PythonPreflight $pythonInfo
    Assert-DependencyLockPreflight $dependencyLock
    Assert-DoctorPreflight $doctor
    Assert-ProfilePreflight $profileEnvelope
    Assert-CapPreflight $caps
    Assert-GitPreflight $gitGate
    Write-PreflightSummary $gitGate
    $progressFixturePath = Join-Path $fixture "progress.json"
    if (Test-Path -LiteralPath $progressFixturePath) {
        $progressFixture = Read-FlagshipJsonFile $progressFixturePath "Progress"
        foreach ($record in @($progressFixture.lines)) {
            Write-SanitizedFlagshipProgress $record
        }
    }
    Write-Output "STOP  Test-only dry run complete; no evidence, credential, or model was accessed."
    return
}

if ($OpenViewer -and -not $Execute) {
    throw [InvalidOperationException]::new("-OpenViewer requires -Execute.")
}

if (-not $PythonPath) {
    Assert-FlagshipCondition ([string]::IsNullOrWhiteSpace($env:LOCALAPPDATA) -eq $false) `
        "PythonPath is required when the validated local environment cannot be located."
    $PythonPath = Join-Path $env:LOCALAPPDATA "venvs\sentinel-unchained-py311\Scripts\python.exe"
}

$pythonExecutable = Resolve-ExistingLeafFile $PythonPath `
    "PythonPath must name the validated CPython executable."
$sourceIdentityRaw = Invoke-CapturedPython $pythonExecutable @(
    "-I",
    "-c",
    (
        "import importlib.metadata as m,json,os,platform,sys,unchained; from pathlib import Path; " +
        "r=Path(sys.argv[1]).resolve(); d=m.distribution('sentinel-unchained'); " +
        "u=json.loads(d.read_text('direct_url.json') or '{}'); " +
        "same=lambda a,b: os.path.normcase(str(Path(a).resolve()))==" +
        "os.path.normcase(str(Path(b).resolve())); " +
        "print(json.dumps({'implementation': platform.python_implementation(), " +
        "'version': platform.python_version(), 'module_matches_frozen_repo': " +
        "same(unchained.__file__, r/'src'/'unchained'/'__init__.py'), " +
        "'distribution_source_matches_frozen_repo': " +
        "u.get('url','').rstrip('/')==r.as_uri().rstrip('/'), " +
        "'distribution_editable': u.get('dir_info',{}).get('editable') is True}, " +
        "sort_keys=True))"
    ),
    $RepositoryRoot
) "Frozen Unchained source-identity preflight failed."
$sourceIdentity = ConvertFrom-FlagshipJson $sourceIdentityRaw "Frozen source identity"
Assert-FrozenSourcePreflight $sourceIdentity
$evidenceRoot = Resolve-ExistingRealDirectory $EvidenceDirectory `
    "EvidenceDirectory must name one real, non-reparse directory."
$keyFile = Resolve-ExistingLeafFile $OpenAIKeyFile `
    "OpenAIKeyFile must name one real, non-reparse credential file."
$outputRoot = Resolve-OutputRoot $OutputDirectory
$dependencyLockFile = Resolve-ExistingLeafFile (
    Join-Path $RepositoryRoot $ExpectedDependencyLockPath
) "Frozen dependency lock is unavailable."
Assert-NoReparseAncestors $pythonExecutable `
    "PythonPath must not traverse a reparse-point ancestor."
Assert-NoReparseAncestors $evidenceRoot `
    "EvidenceDirectory must not traverse a reparse-point ancestor."
Assert-NoReparseAncestors $keyFile `
    "OpenAIKeyFile must not traverse a reparse-point ancestor."
Assert-NoReparseAncestors $outputRoot `
    "OutputDirectory must not traverse a reparse-point ancestor."
Assert-FlagshipCondition (-not (Test-IsSameOrChildPath $outputRoot $evidenceRoot)) `
    "OutputDirectory must not be the evidence directory or one of its descendants."
Assert-FlagshipCondition (-not (Test-IsSameOrChildPath $outputRoot $RepositoryRoot)) `
    "OutputDirectory must be outside the frozen repository worktree."

$pythonInfluenceNames = @(
    "PYTHONPATH",
    "PYTHONHOME",
    "PYTHONSTARTUP",
    "PYTHONINSPECT",
    "PYTHONWARNINGS",
    "PYTHONUSERBASE",
    "PYTHONCASEOK",
    "PYTHONEXECUTABLE",
    "PYTHONBREAKPOINT",
    "PYTHONSAFEPATH",
    "PYTHONPLATLIBDIR"
)
$environmentNames = @(
    "OPENAI_API_KEY",
    "OPENAI_API_KEY_FILE",
    "UNCHAINED_MODEL",
    "MAX_TOOL_CALLS",
    "MAX_TOTAL_TOKENS",
    "MAX_WALL_SECONDS",
    "MAX_COST_USD",
    "PYTHONNOUSERSITE",
    "PYTHONUTF8"
) + $pythonInfluenceNames
$savedEnvironment = @{}
foreach ($name in $environmentNames) {
    $savedEnvironment[$name] = [Environment]::GetEnvironmentVariable($name, "Process")
}

try {
    foreach ($name in $pythonInfluenceNames) {
        [Environment]::SetEnvironmentVariable($name, $null, "Process")
    }
    $env:OPENAI_API_KEY = $null
    $env:OPENAI_API_KEY_FILE = $keyFile
    $env:UNCHAINED_MODEL = $ExpectedModel
    $env:MAX_TOOL_CALLS = [string]$FrozenCaps.max_tool_calls
    $env:MAX_TOTAL_TOKENS = [string]$FrozenCaps.max_total_tokens
    $env:MAX_WALL_SECONDS = [string]$FrozenCaps.max_wall_seconds
    $env:MAX_COST_USD = [string]$FrozenCaps.max_cost_usd
    $env:PYTHONNOUSERSITE = "1"
    $env:PYTHONUTF8 = "1"

    $pythonInfoRaw = Invoke-CapturedPython $pythonExecutable @(
        "-I",
        "-c",
        "import json,platform,sys; print(json.dumps({'implementation': platform.python_implementation(), 'version': platform.python_version(), 'version_info': list(sys.version_info[:3])}))"
    ) "Exact Python runtime preflight failed."
    $pythonInfo = ConvertFrom-FlagshipJson $pythonInfoRaw "Python preflight"

    $dependencyLockRaw = Invoke-CapturedPython $pythonExecutable @(
        "-I",
        "-c",
        (
            "import hashlib,json,sys; from pathlib import Path; " +
            "from unchained.artifacts import _installed_versions_match_lock; " +
            "p=Path(sys.argv[1]); print(json.dumps({'path': " +
            "'requirements/pylock.windows-amd64-cp311.toml', " +
            "'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), " +
            "'target': 'windows-amd64-cp311', " +
            "'installed_versions_match': _installed_versions_match_lock(p)}, sort_keys=True))"
        ),
        $dependencyLockFile
    ) "Dependency lock parity preflight failed."
    $dependencyLock = ConvertFrom-FlagshipJson $dependencyLockRaw "Dependency lock preflight"

    $gitGate = Get-ActualGitGate $RepositoryRoot $FreezeTag

    $freezeGatePath = Join-Path $RepositoryRoot "scripts\benchmark_freeze_gate.py"
    $freezeRaw = Invoke-CapturedPython $pythonExecutable @(
        "-I", $freezeGatePath, "--require-tag", "--json"
    ) "Benchmark freeze gate is not READY; the flagship run is not authorized."
    $freeze = ConvertFrom-FlagshipJson $freezeRaw "Benchmark freeze gate"
    Assert-BenchmarkFreezePreflight $freeze

    $doctorRaw = Invoke-CapturedPython $pythonExecutable @(
        "-I", "-m", "unchained", "doctor", "--json"
    ) "Doctor JSON preflight failed."
    $doctor = ConvertFrom-FlagshipJson $doctorRaw "Doctor preflight"

    $profileRaw = Invoke-CapturedPython $pythonExecutable @(
        "-I", "-m", "unchained", "profile", $evidenceRoot, "--json"
    ) "Evidence profile preflight failed."
    $profileEnvelope = ConvertFrom-FlagshipJson $profileRaw "Profile preflight"

    $capsRaw = Invoke-CapturedPython $pythonExecutable @(
        "-I",
        "-c",
        "import json; from dataclasses import asdict; from unchained.caps import CapConfig; value=asdict(CapConfig.from_env('default')); value['profile']='default'; print(json.dumps(value, sort_keys=True))"
    ) "Cap configuration preflight failed."
    $caps = ConvertFrom-FlagshipJson $capsRaw "Cap preflight"

    Assert-PythonPreflight $pythonInfo
    Assert-DependencyLockPreflight $dependencyLock
    Assert-DoctorPreflight $doctor
    Assert-ProfilePreflight $profileEnvelope
    Assert-CapPreflight $caps
    Assert-GitPreflight $gitGate
    Write-PreflightSummary $gitGate

    if (-not $Execute) {
        Write-Output "STOP  -Execute not supplied; preflight completed with no model call."
        return
    }

    $metricsTarget = Join-Path $RepositoryRoot $MetricsRelativePath
    Assert-FlagshipCondition (-not (Test-Path -LiteralPath $metricsTarget)) `
        "Primary metrics artifact already exists; refusing to run or overwrite it."
    try {
        if (-not (Test-Path -LiteralPath $outputRoot)) {
            New-Item -ItemType Directory -Path $outputRoot -Force -ErrorAction Stop | Out-Null
        }
    }
    catch {
        throw [InvalidOperationException]::new(
            "OutputDirectory could not be created safely."
        )
    }
    $runParent = Join-Path $outputRoot "unchained-runs"
    $beforeNames = @(Get-RunDirectoryNames $runParent)
    $beforeSet = [Collections.Generic.HashSet[string]]::new(
        [StringComparer]::OrdinalIgnoreCase
    )
    foreach ($name in $beforeNames) {
        [void]$beforeSet.Add($name)
    }

    $remoteFreezeRaw = Invoke-CapturedPython $pythonExecutable @(
        "-I", $freezeGatePath, "--require-tag", "--require-remote-tag", "--json"
    ) "The annotated freeze tag is not visible on canonical origin; execution is refused."
    $remoteFreeze = ConvertFrom-FlagshipJson $remoteFreezeRaw "Remote freeze gate"
    Assert-RemoteAnchorPreflight $remoteFreeze $gitGate
    Write-Output (
        "PASS  Remote freeze tag visible on canonical origin; chronology evidence only."
    )

    $priorErrorActionPreference = $ErrorActionPreference
    $priorErrorCount = $Error.Count
    $runExitCode = $null
    try {
        Push-Location $outputRoot
        try {
            # Windows PowerShell 5.1 converts native stderr into ErrorRecord objects
            # and would stop under the script-wide preference. Continue only for
            # this pipeline, normalize each record, and emit an exact code-owned
            # allowlist. All other controller, provider, and path-bearing text is
            # consumed without being retained or printed.
            $ErrorActionPreference = "Continue"
            & $pythonExecutable -I -m unchained run $evidenceRoot --caps default 2>&1 |
                ForEach-Object { Write-SanitizedFlagshipProgress $_ }
            $runExitCode = $LASTEXITCODE
        }
        finally {
            $ErrorActionPreference = $priorErrorActionPreference
            while ($Error.Count -gt $priorErrorCount) {
                $Error.RemoveAt(0)
            }
            Pop-Location
        }
    }
    catch {
        throw [InvalidOperationException]::new(
            "Flagship controller invocation failed before a result could be classified."
        )
    }
    Assert-FlagshipCondition ($null -ne $runExitCode) `
        "Flagship controller exit status was unavailable; retained output requires review."

    $afterNames = @(Get-RunDirectoryNames $runParent)
    $newNames = @($afterNames | Where-Object { -not $beforeSet.Contains($_) })
    Assert-FlagshipCondition ($newNames.Count -eq 1) `
        "Run output discovery did not identify exactly one new proof bundle."
    Assert-FlagshipCondition ($newNames[0] -match "^\d{8}T\d{6}Z-[0-9a-f]{8}$") `
        "New proof bundle identifier does not match the controller contract."
    $bundleDirectory = Join-Path $runParent $newNames[0]
    Assert-FlagshipCondition ($runExitCode -eq 0) `
        "Flagship controller did not finish COMPLETE; retained bundle requires review."

    $verifyRaw = Invoke-CapturedPython $pythonExecutable @(
        "-I", "-m", "unchained", "verify", $bundleDirectory,
        "--require-complete", "--require-live-gpt56", "--json"
    ) "Strict COMPLETE/live GPT-5.6 verification failed."
    $verification = ConvertFrom-FlagshipJson $verifyRaw "Strict verification"
    Assert-FlagshipCondition (
        $verification.passed -eq $true -and
        $verification.run_id -eq $newNames[0] -and
        $verification.terminal.status -eq "COMPLETE" -and
        [int]$verification.terminal.exit_code -eq 0
    ) "Strict verification did not bind the exact new COMPLETE live GPT-5.6 bundle."

    $postRunGitGate = Get-ActualGitGate $RepositoryRoot $FreezeTag
    Assert-GitPreflight $postRunGitGate
    Assert-FlagshipCondition ($postRunGitGate.head -eq $gitGate.head) `
        "Frozen repository commit changed during the flagship run."

    Write-SanitizedMetrics $bundleDirectory $verification $gitGate $remoteFreeze.remote_anchor
    Assert-OnlyMetricsCreatedAfterValidation $gitGate
    Write-Output "PASS  COMPLETE recorded live GPT-5.6 bundle passed strict verification."
    Write-Output "PASS  Verified run ID: $($verification.run_id)"
    Write-Output "PASS  Sanitized primary-run metrics emitted; private paths and key omitted."

    if ($OpenViewer) {
        try {
            $viewLines = @(& $pythonExecutable -I -m unchained view $bundleDirectory 2>&1)
            $viewExitCode = $LASTEXITCODE
        }
        catch {
            throw [InvalidOperationException]::new(
                "Verified bundle was retained, but the optional viewer could not be invoked."
            )
        }
        $null = $viewLines
        Assert-FlagshipCondition ($viewExitCode -eq 0) `
            "Verified bundle was retained, but the optional viewer did not open."
        Write-Output "PASS  Optional verified viewer opened."
    }
}
finally {
    foreach ($name in $environmentNames) {
        [Environment]::SetEnvironmentVariable($name, $savedEnvironment[$name], "Process")
    }
}
