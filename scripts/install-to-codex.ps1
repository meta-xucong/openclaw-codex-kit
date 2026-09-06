[CmdletBinding()]
param(
    [switch]$IncludeNonDefault,
    [switch]$Overwrite,
    [string]$PackRoot
)

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($PackRoot)) {
    $PackRoot = Join-Path $repoRoot 'installer-pack'
}
$PackRoot = (Resolve-Path -LiteralPath $PackRoot).Path
$packFile = Join-Path $PackRoot 'pack.json'
$dependencyFile = Join-Path $PackRoot 'dependencies.json'
$fileManifest = Join-Path $PackRoot 'file-manifest.json'
$checksumFile = Join-Path $PackRoot 'checksums.sha256'
foreach ($requiredFile in @($packFile, $dependencyFile, $fileManifest)) {
    if (-not (Test-Path -LiteralPath $requiredFile -PathType Leaf)) {
        throw "Invalid capability pack: missing $requiredFile"
    }
}

$pack = Get-Content -LiteralPath $packFile -Raw | ConvertFrom-Json
if ([int]$pack.schemaVersion -ne 2) { throw "Unsupported capability pack schema: $($pack.schemaVersion)" }
$manifest = Get-Content -LiteralPath $fileManifest -Raw | ConvertFrom-Json
function Resolve-PackOwnedFile([string]$RelativePath) {
    if ([string]::IsNullOrWhiteSpace($RelativePath) -or [IO.Path]::IsPathRooted($RelativePath) -or $RelativePath -match '(^|[\\/])\.\.([\\/]|$)') {
        throw "Unsafe pack path: $RelativePath"
    }
    $packRootFull = [IO.Path]::GetFullPath($PackRoot).TrimEnd('\') + '\'
    $candidate = [IO.Path]::GetFullPath((Join-Path $PackRoot ($RelativePath -replace '/', '\')))
    if (-not $candidate.StartsWith($packRootFull, [StringComparison]::OrdinalIgnoreCase)) { throw "Pack path escapes root: $RelativePath" }
    return $candidate
}
foreach ($entry in $manifest.files) {
    $source = Resolve-PackOwnedFile ([string]$entry.path)
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
        throw "Pack file missing: $($entry.path)"
    }
    $hash = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($hash -ne $entry.sha256.ToLowerInvariant()) {
        throw "Pack hash mismatch: $($entry.path)"
    }
}
if (-not (Test-Path -LiteralPath $checksumFile -PathType Leaf)) { throw 'Invalid capability pack: missing checksums.sha256' }
$checksumPaths = [System.Collections.Generic.HashSet[string]]::new()
foreach ($line in Get-Content -LiteralPath $checksumFile) {
    if ([string]::IsNullOrWhiteSpace($line)) { continue }
    $match = [regex]::Match($line, '^(?<hash>[0-9a-fA-F]{64}) \*(?<path>.+)$')
    if (-not $match.Success) { throw "Invalid pack checksum line: $line" }
    $relative = $match.Groups['path'].Value.Trim()
    if (-not $checksumPaths.Add($relative)) { throw "Duplicate pack checksum path: $relative" }
    $source = Resolve-PackOwnedFile $relative
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw "Checksum target missing: $relative" }
    $hash = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($hash -ne $match.Groups['hash'].Value.ToLowerInvariant()) { throw "Pack checksum mismatch: $relative" }
}

$agentTarget = Join-Path $env:USERPROFILE '.codex\agents'
$skillTarget = Join-Path $env:USERPROFILE '.agents\skills'
$ownershipRoot = Join-Path $env:USERPROFILE '.codex\codex-agent-kit'
$ownershipFile = Join-Path $ownershipRoot 'install-manifest.json'
New-Item -ItemType Directory -Force -Path $agentTarget, $skillTarget, $ownershipRoot | Out-Null

$agentFiles = @($pack.defaultEnabled.agents)
$skillNames = @($pack.defaultEnabled.skills)
if ($IncludeNonDefault) {
    $agentFiles = @(Get-ChildItem -LiteralPath (Join-Path $PackRoot 'agents') -Filter '*.toml' -File | ForEach-Object { "agents/$($_.Name)" })
    $skillNames = @(Get-ChildItem -LiteralPath (Join-Path $PackRoot 'skills') -Directory | ForEach-Object { $_.Name })
}

$installed = [System.Collections.Generic.List[object]]::new()
function Copy-OwnedFile([string]$Source, [string]$Destination, [string]$Kind) {
    if ((Test-Path -LiteralPath $Destination) -and -not $Overwrite) {
        Write-Warning "Skipped existing ${Kind}: $Destination (use -Overwrite to update)."
        return
    }
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Destination) | Out-Null
    Copy-Item -LiteralPath $Source -Destination $Destination -Force
    $hash = (Get-FileHash -LiteralPath $Destination -Algorithm SHA256).Hash.ToLowerInvariant()
    $installed.Add([pscustomobject]@{ kind = $Kind; path = $Destination; sha256 = $hash })
    Write-Host "Installed ${Kind}: $Destination"
}

Write-Host "Agents target: $agentTarget"
foreach ($relativeAgent in $agentFiles) {
    $relative = ([string]$relativeAgent) -replace '/', '\'
    if (-not $relative.StartsWith('agents\')) { $relative = Join-Path 'agents' $relative }
    $source = Join-Path $PackRoot $relative
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw "Missing agent in pack: $relative" }
    Copy-OwnedFile $source (Join-Path $agentTarget (Split-Path -Leaf $relative)) 'agent'
}

Write-Host "Skills target: $skillTarget"
foreach ($skillName in $skillNames) {
    $name = ([string]$skillName).Trim()
    if ($name -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]*$') { throw "Invalid skill name in pack: $name" }
    $source = Join-Path (Join-Path $PackRoot 'skills') $name
    $destination = Join-Path $skillTarget $name
    if (-not (Test-Path -LiteralPath (Join-Path $source 'SKILL.md') -PathType Leaf)) { throw "Missing SKILL.md in pack: $name" }
    if ((Test-Path -LiteralPath $destination) -and -not $Overwrite) {
        Write-Warning "Skipped existing skill: $destination (use -Overwrite to update)."
        continue
    }
    if (Test-Path -LiteralPath $destination) {
        Copy-Item -LiteralPath $source -Destination $destination -Recurse -Force
    } else {
        Copy-Item -LiteralPath $source -Destination $destination -Recurse
    }
    $skillHash = (Get-FileHash -LiteralPath (Join-Path $destination 'SKILL.md') -Algorithm SHA256).Hash.ToLowerInvariant()
    $installed.Add([pscustomobject]@{ kind = 'skill'; path = $destination; sha256 = $skillHash })
    Write-Host "Installed skill: $destination"
}

$record = [ordered]@{
    schemaVersion = 2
    packId = [string]$pack.id
    packVersion = [string]$pack.version
    sourceCommit = [string]$pack.sourceCommit
    installedAtUtc = [DateTime]::UtcNow.ToString('o')
    agentRoot = $agentTarget
    skillRoot = $skillTarget
    overwrite = [bool]$Overwrite
    files = @($installed)
    note = 'Ownership record contains paths and hashes only; it contains no credentials or user content.'
}
$record | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ownershipFile -Encoding UTF8
Write-Host "Ownership record: $ownershipFile"
Write-Host 'Done. Restart Codex or open a new task so the new agents and skills are reloaded.' -ForegroundColor Green
