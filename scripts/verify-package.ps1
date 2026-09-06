[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$agentSource = Join-Path $repoRoot 'agents'
$skillSource = Join-Path $repoRoot 'skills'
$skillManifest = Join-Path $repoRoot 'manifest/imported-skills.txt'

$agents = @(Get-ChildItem -LiteralPath $agentSource -Filter '*.toml' -File)
$skills = @(Get-Content -LiteralPath $skillManifest | Where-Object { $_ -and -not $_.StartsWith('#') })
$missingSkills = @($skills | Where-Object { -not (Test-Path -LiteralPath (Join-Path $skillSource $_.Trim())) })
$missingSkillDocs = @($skills | Where-Object { -not (Test-Path -LiteralPath (Join-Path (Join-Path $skillSource $_.Trim()) 'SKILL.md')) })

Write-Host "Agents: $($agents.Count)"
Write-Host "Skills in manifest: $($skills.Count)"
Write-Host "Missing skill directories: $($missingSkills.Count)"
Write-Host "Missing SKILL.md files: $($missingSkillDocs.Count)"

if ($missingSkills.Count -gt 0) { $missingSkills | ForEach-Object { Write-Host "  $_" } }
if ($missingSkillDocs.Count -gt 0) { $missingSkillDocs | ForEach-Object { Write-Host "  $_" } }

if ($missingSkills.Count -gt 0 -or $missingSkillDocs.Count -gt 0 -or $agents.Count -ne 7) {
    throw 'Package verification failed.'
}

Write-Host 'Package verification passed.' -ForegroundColor Green

