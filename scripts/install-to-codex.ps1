[CmdletBinding()]
param(
    [switch]$IncludeNonDefault,
    [switch]$Overwrite,
    [string]$PackRoot
)

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($PackRoot)) { $PackRoot = Join-Path $repoRoot 'installer-pack' }
$PackRoot = (Resolve-Path -LiteralPath $PackRoot).Path
$packFile = Join-Path $PackRoot 'pack.json'
$dependencyFile = Join-Path $PackRoot 'dependencies.json'
$fileManifest = Join-Path $PackRoot 'file-manifest.json'
$checksumFile = Join-Path $PackRoot 'checksums.sha256'
foreach ($requiredFile in @($packFile, $dependencyFile, $fileManifest, $checksumFile)) {
    if (-not (Test-Path -LiteralPath $requiredFile -PathType Leaf)) { throw "Invalid capability pack: missing $requiredFile" }
}

$pack = Get-Content -LiteralPath $packFile -Raw | ConvertFrom-Json
if ([int]$pack.schemaVersion -ne 2) { throw "Unsupported capability pack schema: $($pack.schemaVersion)" }
$manifest = Get-Content -LiteralPath $fileManifest -Raw | ConvertFrom-Json
function Resolve-PackOwnedFile([string]$RelativePath) {
    if ([string]::IsNullOrWhiteSpace($RelativePath) -or [IO.Path]::IsPathRooted($RelativePath) -or $RelativePath -match '(^|[\/])\.\.([\/]|$)') { throw "Unsafe pack path: $RelativePath" }
    $packRootFull = [IO.Path]::GetFullPath($PackRoot).TrimEnd('\') + '\'
    $candidate = [IO.Path]::GetFullPath((Join-Path $PackRoot ($RelativePath -replace '/', '\')))
    if (-not $candidate.StartsWith($packRootFull, [StringComparison]::OrdinalIgnoreCase)) { throw "Pack path escapes root: $RelativePath" }
    return $candidate
}
foreach ($entry in $manifest.files) {
    $source = Resolve-PackOwnedFile ([string]$entry.path)
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw "Pack file missing: $($entry.path)" }
    $hash = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($hash -ne ([string]$entry.sha256).ToLowerInvariant()) { throw "Pack hash mismatch: $($entry.path)" }
}
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

$userProfile = [Environment]::GetEnvironmentVariable('USERPROFILE')
if ([string]::IsNullOrWhiteSpace($userProfile)) { throw 'USERPROFILE is required for a user-scoped installation.' }
$agentTarget = Join-Path $userProfile '.codex\agents'
$skillTarget = Join-Path $userProfile '.agents\skills'
$ownershipRoot = Join-Path $userProfile '.codex\codex-agent-kit'
$ownershipFile = Join-Path $ownershipRoot 'install-manifest.json'
New-Item -ItemType Directory -Force -Path $agentTarget, $skillTarget, $ownershipRoot | Out-Null

$previousFiles = @()
if (Test-Path -LiteralPath $ownershipFile -PathType Leaf) {
    try {
        $previousRecord = Get-Content -LiteralPath $ownershipFile -Raw | ConvertFrom-Json
        $previousFiles = @($previousRecord.files)
    } catch {
        Write-Warning "Could not read the previous ownership record; existing files will not be overwritten without a matching ownership entry."
    }
}
$installed = [System.Collections.Generic.List[object]]::new()
foreach ($entry in $previousFiles) {
    if ($entry.path -and (Test-Path -LiteralPath ([string]$entry.path))) { $installed.Add($entry) }
}

function Remove-RecordsUnder([string]$RootPath) {
    $prefix = [IO.Path]::GetFullPath($RootPath).TrimEnd('\') + '\'
    $keep = [System.Collections.Generic.List[object]]::new()
    foreach ($entry in @($installed)) {
        $path = if ($entry.path) { [IO.Path]::GetFullPath([string]$entry.path) } else { '' }
        if (-not $path.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase) -and $path -ne $RootPath) { $keep.Add($entry) }
    }
    $installed.Clear()
    foreach ($entry in $keep) { $installed.Add($entry) }
}

function Get-PreviousOwnership([string]$Path, [string[]]$Kinds) {
    foreach ($entry in $previousFiles) {
        if ($entry.path -and ([string]$entry.path).Equals($Path, [StringComparison]::OrdinalIgnoreCase) -and $Kinds -contains ([string]$entry.kind)) { return $entry }
    }
    return $null
}

function Add-OwnedRecord([string]$Kind, [string]$Path, [string]$Hash) {
    $old = Get-PreviousOwnership $Path @($Kind)
    if ($old) { Remove-RecordsUnder $Path }
    $installed.Add([pscustomobject]@{ kind = $Kind; path = $Path; sha256 = $Hash })
}

function Copy-OwnedFile([string]$Source, [string]$Destination, [string]$Kind) {
    $existing = Test-Path -LiteralPath $Destination -PathType Leaf
    if ($existing -and -not $Overwrite) { Write-Warning "Skipped existing ${Kind}: $Destination (use -Overwrite to update)."; return $false }
    if ($existing -and $Overwrite -and -not (Get-PreviousOwnership $Destination @($Kind))) {
        Write-Warning "Skipped unowned existing ${Kind}: $Destination (the installer only overwrites files recorded in its ownership manifest)."
        return $false
    }
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Destination) | Out-Null
    Copy-Item -LiteralPath $Source -Destination $Destination -Force
    $hash = (Get-FileHash -LiteralPath $Destination -Algorithm SHA256).Hash.ToLowerInvariant()
    Add-OwnedRecord $Kind $Destination $hash
    Write-Host "Installed ${Kind}: $Destination"
    return $true
}

function Remove-OwnedSkillTree([string]$Destination) {
    $targetRoot = [IO.Path]::GetFullPath($skillTarget).TrimEnd('\') + '\'
    $destinationFull = [IO.Path]::GetFullPath($Destination)
    if (-not $destinationFull.StartsWith($targetRoot, [StringComparison]::OrdinalIgnoreCase)) { throw "Refusing to mutate a path outside the Skill root: $Destination" }
    $ownedTree = Get-PreviousOwnership $Destination @('skill-tree','skill')
    if (-not $ownedTree) { return $false }
    foreach ($file in @(Get-ChildItem -LiteralPath $Destination -Recurse -File -Force)) { Remove-Item -LiteralPath $file.FullName -Force }
    foreach ($directory in @(Get-ChildItem -LiteralPath $Destination -Recurse -Directory -Force | Sort-Object FullName -Descending)) {
        if (@(Get-ChildItem -LiteralPath $directory.FullName -Force).Count -eq 0) { Remove-Item -LiteralPath $directory.FullName -Force }
    }
    Remove-RecordsUnder $Destination
    return $true
}

$agentFiles = @($pack.defaultEnabled.agents)
$skillNames = @($pack.defaultEnabled.skills)
if ($IncludeNonDefault) {
    $agentFiles = @(Get-ChildItem -LiteralPath (Join-Path $PackRoot 'agents') -Filter '*.toml' -File | ForEach-Object { "agents/$($_.Name)" })
    $skillNames = @(Get-ChildItem -LiteralPath (Join-Path $PackRoot 'skills') -Directory | ForEach-Object { $_.Name })
}

Write-Host "Agents target: $agentTarget"
foreach ($relativeAgent in $agentFiles) {
    $relative = ([string]$relativeAgent) -replace '/', '\'
    if (-not $relative.StartsWith('agents\')) { $relative = Join-Path 'agents' $relative }
    $source = Resolve-PackOwnedFile $relative
    $destination = Join-Path $agentTarget (Split-Path -Leaf $relative)
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw "Missing agent in pack: $relative" }
    Copy-OwnedFile $source $destination 'agent' | Out-Null
}

Write-Host "Skills target: $skillTarget"
foreach ($skillName in $skillNames) {
    $name = ([string]$skillName).Trim()
    if ($name -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]*$') { throw "Invalid skill name in pack: $name" }
    $source = Join-Path (Join-Path $PackRoot 'skills') $name
    $destination = Join-Path $skillTarget $name
    if (-not (Test-Path -LiteralPath (Join-Path $source 'SKILL.md') -PathType Leaf)) { throw "Missing SKILL.md in pack: $name" }
    if (Test-Path -LiteralPath $destination) {
        if (-not $Overwrite) { Write-Warning "Skipped existing skill: $destination (use -Overwrite to update)."; continue }
        if (-not (Remove-OwnedSkillTree $destination)) {
            Write-Warning "Skipped unowned existing skill: $destination (the installer only overwrites a tree recorded in its ownership manifest)."
            continue
        }
    }
    New-Item -ItemType Directory -Force -Path $destination | Out-Null
    $installed.Add([pscustomobject]@{ kind = 'skill-tree'; path = $destination; sha256 = $null })
    foreach ($file in @(Get-ChildItem -LiteralPath $source -Recurse -File -Force)) {
        $relativeFile = $file.FullName.Substring($source.Length).TrimStart('\')
        $targetFile = Join-Path $destination $relativeFile
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $targetFile) | Out-Null
        Copy-Item -LiteralPath $file.FullName -Destination $targetFile -Force
        $hash = (Get-FileHash -LiteralPath $targetFile -Algorithm SHA256).Hash.ToLowerInvariant()
        $installed.Add([pscustomobject]@{ kind = 'skill'; path = $targetFile; sha256 = $hash })
    }
    Write-Host "Installed skill tree: $destination"
}

$record = [ordered]@{
    schemaVersion = 3
    packId = [string]$pack.id
    packVersion = [string]$pack.version
    sourceCommit = [string]$pack.sourceCommit
    installedAtUtc = [DateTime]::UtcNow.ToString('o')
    agentRoot = $agentTarget
    skillRoot = $skillTarget
    overwrite = [bool]$Overwrite
    files = @($installed)
    note = 'Ownership record contains package-owned paths and hashes only; it contains no credentials or user content.'
}
$record | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ownershipFile -Encoding UTF8
Write-Host "Ownership record: $ownershipFile"
Write-Host 'Done. Restart Codex or open a new task so the new agents and skills are reloaded.' -ForegroundColor Green
