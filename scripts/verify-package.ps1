[CmdletBinding()]
param(
    [switch]$SkipRebuild
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $repoRoot

if (-not $SkipRebuild) {
    $python = Get-Command python -ErrorAction SilentlyContinue
    if (-not $python) { throw 'Verification requires Python 3. The installer itself does not.' }
    & $python.Source (Join-Path $repoRoot 'scripts\build-pack.py') --check
    if ($LASTEXITCODE -ne 0) { throw 'Pack build failed.' }
}

$audit = Get-Content -LiteralPath (Join-Path $repoRoot 'manifest\skill-audit.json') -Encoding UTF8 -Raw | ConvertFrom-Json
$agentAudit = Get-Content -LiteralPath (Join-Path $repoRoot 'manifest\agent-audit.json') -Encoding UTF8 -Raw | ConvertFrom-Json
$pack = Get-Content -LiteralPath (Join-Path $repoRoot 'installer-pack\pack.json') -Encoding UTF8 -Raw | ConvertFrom-Json
$dependencies = Get-Content -LiteralPath (Join-Path $repoRoot 'installer-pack\dependencies.json') -Encoding UTF8 -Raw | ConvertFrom-Json
$fileManifest = Get-Content -LiteralPath (Join-Path $repoRoot 'installer-pack\file-manifest.json') -Encoding UTF8 -Raw | ConvertFrom-Json

$manifestSkills = @(Get-Content -LiteralPath (Join-Path $repoRoot 'manifest\imported-skills.txt') -Encoding UTF8 | Where-Object { $_.Trim() -and -not $_.Trim().StartsWith('#') } | ForEach-Object { $_.Trim() })
$auditSkills = @($audit.skills | ForEach-Object { $_.id })
$packSkills = @(Get-ChildItem -LiteralPath (Join-Path $repoRoot 'installer-pack\skills') -Directory | ForEach-Object { $_.Name })
$agents = @(Get-ChildItem -LiteralPath (Join-Path $repoRoot 'agents') -Filter '*.toml' -File)
$packAgents = @(Get-ChildItem -LiteralPath (Join-Path $repoRoot 'installer-pack\agents') -Filter '*.toml' -File)

Write-Host "Source skills: $($manifestSkills.Count)"
Write-Host "Audited skills: $($auditSkills.Count)"
Write-Host "Pack skills: $($packSkills.Count)"
Write-Host "Source agents: $($agents.Count)"
Write-Host "Pack agents: $($packAgents.Count)"

if ($manifestSkills.Count -ne 50 -or $auditSkills.Count -ne 50 -or $packSkills.Count -ne 50) { throw 'Expected exactly 50 skills.' }
if (@(Compare-Object ($manifestSkills | Sort-Object) ($auditSkills | Sort-Object)).Count -gt 0) { throw 'Skill manifest and audit differ.' }
if (@(Compare-Object ($manifestSkills | Sort-Object) ($packSkills | Sort-Object)).Count -gt 0) { throw 'Skill manifest and pack differ.' }
if ($agents.Count -ne 7 -or $packAgents.Count -ne 7) { throw 'Expected exactly 7 agents.' }

$names = [System.Collections.Generic.HashSet[string]]::new()
foreach ($skill in $manifestSkills) {
    $doc = Join-Path (Join-Path $repoRoot 'skills') (Join-Path $skill 'SKILL.md')
    if (-not (Test-Path -LiteralPath $doc -PathType Leaf)) { throw "Missing SKILL.md: $skill" }
    $content = Get-Content -LiteralPath $doc -Encoding UTF8 -Raw
    $nameMatch = [regex]::Match($content, '(?m)^name:\s*([A-Za-z0-9][A-Za-z0-9._-]*)\s*$')
    $descriptionMatch = [regex]::Match($content, '(?m)^description:\s*(.+)')
    if (-not $nameMatch.Success -or $nameMatch.Groups[1].Value.Trim() -ne $skill) { throw "Skill name mismatch: $skill" }
    if (-not $descriptionMatch.Success -or [string]::IsNullOrWhiteSpace($descriptionMatch.Groups[1].Value.Trim().Trim('"'))) { throw "Skill description missing: $skill" }
    if (-not $names.Add($nameMatch.Groups[1].Value.Trim())) { throw "Duplicate skill name: $skill" }
    $packDoc = Join-Path (Join-Path $repoRoot 'installer-pack\skills') (Join-Path $skill 'SKILL.md')
    if (-not (Test-Path -LiteralPath $packDoc -PathType Leaf)) { throw "Pack SKILL.md missing: $skill" }
}

$forbidden = '(?i)(open' + 'claw|claw' + 'dbot|ran' + 'claw|\.open' + 'claw)'
$secretLike = '(?i)(sk-[A-Za-z0-9]{20,}|Bearer\s+[A-Za-z0-9._-]{20,})'
$scanRoots = @('README.md', 'ENVIRONMENT-MCP-INVENTORY.md', 'agents', 'manifest', 'scripts', 'skills')
foreach ($scanRoot in $scanRoots) {
    $absolute = Join-Path $repoRoot $scanRoot
    $files = if (Test-Path -LiteralPath $absolute -PathType Leaf) { @((Get-Item -LiteralPath $absolute)) } else { @(Get-ChildItem -LiteralPath $absolute -Recurse -File) }
    foreach ($file in $files) {
        if ($file.Name -eq '.DS_Store' -or $file.Name -like '*_tasks.json' -or $file.Name -like '*.json.lock' -or $file.Name -like '*-market.json' -or $file.DirectoryName -match '\\.cache(\\|$)|\\drafts(\\|$)|\\output(\\|$)') { continue }
        if ($file.Extension.ToLowerInvariant() -notin @('.md','.py','.js','.ts','.json','.toml','.ps1','.sh','.txt')) { continue }
        $text = Get-Content -LiteralPath $file.FullName -Encoding UTF8 -Raw
        if ($text -match $forbidden) { throw "Legacy marker found: $($file.FullName)" }
        if ($text -match $secretLike) { throw "Secret-like value found: $($file.FullName)" }
    }
}

$dependencySkills = @($dependencies.skills | ForEach-Object { $_.id })
if (@(Compare-Object ($manifestSkills | Sort-Object) ($dependencySkills | Sort-Object)).Count -gt 0) { throw 'dependencies.json and skill manifest differ.' }
$defaultSkills = @($pack.defaultEnabled.skills)
foreach ($skill in $defaultSkills) {
    $item = @($audit.skills | Where-Object { $_.id -eq $skill })[0]
    if (-not $item -or $item.status -ne 'ready' -or -not $item.defaultEnabled) { throw "Invalid default skill status: $skill" }
}
if ($defaultSkills.Count -ne @($audit.skills | Where-Object { $_.defaultEnabled }).Count) { throw 'Default skill count differs.' }

foreach ($entry in $fileManifest.files) {
    $path = Join-Path (Join-Path $repoRoot 'installer-pack') ($entry.path -replace '/', '\')
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Manifest file missing: $($entry.path)" }
    $hash = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($hash -ne $entry.sha256.ToLowerInvariant()) { throw "Hash mismatch: $($entry.path)" }
}

$python = Get-Command python -ErrorAction SilentlyContinue
if ($python) {
    $pyFiles = @(Get-ChildItem -LiteralPath (Join-Path $repoRoot 'skills') -Recurse -Filter '*.py' -File)
    foreach ($pyFile in $pyFiles) {
        & $python.Source -m py_compile $pyFile.FullName
        if ($LASTEXITCODE -ne 0) { throw "Python syntax check failed: $($pyFile.FullName)" }
    }
    & $python.Source -c "import tomllib, pathlib; [tomllib.loads(p.read_text(encoding='utf-8')) for p in pathlib.Path('agents').glob('*.toml')]"
    if ($LASTEXITCODE -ne 0) { throw 'Agent TOML parse failed.' }
}

Write-Host 'Status counts:' -ForegroundColor Cyan
$audit.skills | Group-Object status | Sort-Object Name | ForEach-Object { Write-Host ("  {0}: {1}" -f $_.Name, $_.Count) }
Write-Host "Default skills: $($defaultSkills.Count)"
Write-Host 'Package verification passed.' -ForegroundColor Green
