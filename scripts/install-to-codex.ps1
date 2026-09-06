[CmdletBinding()]
param(
    [switch]$Overwrite
)

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$codexRoot = Join-Path $env:USERPROFILE '.codex'
$agentSource = Join-Path $repoRoot 'agents'
$skillSource = Join-Path $repoRoot 'skills'
$agentTarget = Join-Path $codexRoot 'agents'
$skillTarget = Join-Path $codexRoot 'skills'
$skillManifest = Join-Path $repoRoot 'manifest/imported-skills.txt'

New-Item -ItemType Directory -Force -Path $agentTarget, $skillTarget | Out-Null

Write-Host "Installing agents to $agentTarget"
Get-ChildItem -LiteralPath $agentSource -Filter '*.toml' -File | ForEach-Object {
    $destination = Join-Path $agentTarget $_.Name
    if ((Test-Path -LiteralPath $destination) -and -not $Overwrite) {
        Write-Warning "Skipped existing agent: $($_.Name). Use -Overwrite to replace it."
    } else {
        Copy-Item -LiteralPath $_.FullName -Destination $destination -Force
        Write-Host "Installed agent: $($_.Name)"
    }
}

Write-Host "Installing skills to $skillTarget"
Get-Content -LiteralPath $skillManifest | Where-Object { $_ -and -not $_.StartsWith('#') } | ForEach-Object {
    $skillName = $_.Trim()
    $source = Join-Path $skillSource $skillName
    $destination = Join-Path $skillTarget $skillName
    if (-not (Test-Path -LiteralPath $source)) {
        throw "Missing packaged skill: $skillName"
    }
    if ((Test-Path -LiteralPath $destination) -and -not $Overwrite) {
        Write-Warning "Skipped existing skill: $skillName. Use -Overwrite to replace it."
    } else {
        Copy-Item -LiteralPath $source -Destination $destination -Recurse -Force
        Write-Host "Installed skill: $skillName"
    }
}

Write-Host ''
Write-Host 'Done. Restart Codex or open a new task so the new agents and skills are reloaded.' -ForegroundColor Green

