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

function Read-JsonFile([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Missing JSON file: $Path" }
    return Get-Content -LiteralPath $Path -Encoding UTF8 -Raw | ConvertFrom-Json
}

function Resolve-PackFile([string]$RelativePath) {
    if ([string]::IsNullOrWhiteSpace($RelativePath) -or [IO.Path]::IsPathRooted($RelativePath) -or $RelativePath -match '(^|[\\/])\.\.([\\/]|$)') {
        throw "Unsafe pack path: $RelativePath"
    }
    $packRootFull = [IO.Path]::GetFullPath((Join-Path $repoRoot 'installer-pack')).TrimEnd('\') + '\'
    $candidate = [IO.Path]::GetFullPath((Join-Path $repoRoot (Join-Path 'installer-pack' ($RelativePath -replace '/', '\'))))
    if (-not $candidate.StartsWith($packRootFull, [StringComparison]::OrdinalIgnoreCase)) { throw "Pack path escapes root: $RelativePath" }
    return $candidate
}

$audit = Read-JsonFile (Join-Path $repoRoot 'manifest\skill-audit.json')
$agentAudit = Read-JsonFile (Join-Path $repoRoot 'manifest\agent-audit.json')
$pack = Read-JsonFile (Join-Path $repoRoot 'installer-pack\pack.json')
$dependencies = Read-JsonFile (Join-Path $repoRoot 'installer-pack\dependencies.json')
$fileManifest = Read-JsonFile (Join-Path $repoRoot 'installer-pack\file-manifest.json')
$runtimeArtifacts = Read-JsonFile (Join-Path $repoRoot 'manifest\runtime-artifacts.json')
$mcpServers = Read-JsonFile (Join-Path $repoRoot 'manifest\mcp-servers.json')
$apiServices = Read-JsonFile (Join-Path $repoRoot 'manifest\api-services.json')
$connectionFields = Read-JsonFile (Join-Path $repoRoot 'manifest\connection-fields.json')

if ([int]$pack.schemaVersion -ne 2) { throw 'Pack schema must be 2.' }
if ([string]$pack.version -ne '1.1.0') { throw "Unexpected pack version: $($pack.version)" }
if ([string]::IsNullOrWhiteSpace([string]$pack.sourceCommit)) { throw 'Pack source commit is missing.' }
if ([string]$pack.compatibleCodex.minCodexVersion -ne '0.144.0') { throw 'Minimum Codex version contract changed unexpectedly.' }
if ([string]$pack.compatibleCodex.testedCodexVersion -ne '0.144.1') { throw 'Tested Codex version contract changed unexpectedly.' }

$manifestSkills = @(Get-Content -LiteralPath (Join-Path $repoRoot 'manifest\imported-skills.txt') -Encoding UTF8 | Where-Object { $_.Trim() -and -not $_.Trim().StartsWith('#') } | ForEach-Object { $_.Trim() })
$auditSkills = @($audit.skills | ForEach-Object { [string]$_.id })
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

$statusCounts = @{}
$afterCounts = @{}
foreach ($skill in $audit.skills) {
    $status = [string]$skill.status
    $after = [string]$skill.afterRemediationStatus
    if (-not $statusCounts.ContainsKey($status)) { $statusCounts[$status] = 0 }
    if (-not $afterCounts.ContainsKey($after)) { $afterCounts[$after] = 0 }
    $statusCounts[$status]++
    $afterCounts[$after]++
    if ($skill.installByDefault -and $after -ne 'core-ready') { throw "Non-core skill installed by default: $($skill.id)" }
}
foreach ($expected in @{
    'core-ready' = 25
    'auto-installable-runtime' = 15
    'guided-config' = 7
    'unsupported' = 3
}.GetEnumerator()) {
    if (-not $afterCounts.ContainsKey($expected.Key) -or $afterCounts[$expected.Key] -ne $expected.Value) { throw "Unexpected after-remediation count for $($expected.Key)." }
}

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

$nonCore = @($audit.skills | Where-Object { $_.afterRemediationStatus -ne 'core-ready' })
foreach ($skill in $nonCore) {
    $yaml = Join-Path (Join-Path (Join-Path $repoRoot 'skills') $skill.id) 'agents\openai.yaml'
    if (-not (Test-Path -LiteralPath $yaml -PathType Leaf)) { throw "Non-core Skill metadata missing: $($skill.id)" }
    $yamlText = Get-Content -LiteralPath $yaml -Encoding UTF8 -Raw
    if ($yamlText -notmatch '(?m)^\s*allow_implicit_invocation:\s*false\s*$') { throw "Non-core Skill must disable implicit invocation: $($skill.id)" }
    $packYaml = Join-Path (Join-Path (Join-Path $repoRoot 'installer-pack\skills') $skill.id) 'agents\openai.yaml'
    if (-not (Test-Path -LiteralPath $packYaml -PathType Leaf)) { throw "Pack Skill metadata missing: $($skill.id)" }
}

$forbidden = '(?i)(open' + 'claw|claw' + 'dbot|ran' + 'claw|\.open' + 'claw)'
$secretLike = '(?i)(sk-[A-Za-z0-9]{20,}|Bearer\s+[A-Za-z0-9._-]{20,})'
function Scan-TextRoots([string[]]$Roots) {
    foreach ($scanRoot in $Roots) {
        $absolute = if ([IO.Path]::IsPathRooted($scanRoot)) { $scanRoot } else { Join-Path $repoRoot $scanRoot }
        if (-not (Test-Path -LiteralPath $absolute)) { continue }
        $files = if (Test-Path -LiteralPath $absolute -PathType Leaf) { @((Get-Item -LiteralPath $absolute)) } else { @(Get-ChildItem -LiteralPath $absolute -Recurse -File) }
        foreach ($file in $files) {
            if ($file.Name -eq '.DS_Store' -or $file.Name -like '*_tasks.json' -or $file.Name -like '*.json.lock' -or $file.Name -like '*-market.json' -or $file.FullName -match '\\(__pycache__|\.cache|drafts|output|codex-data)(\\|$)') { continue }
            if ($file.Extension.ToLowerInvariant() -notin @('.md','.py','.js','.ts','.json','.toml','.ps1','.sh','.txt','.yaml','.yml','.lock')) { continue }
            $text = Get-Content -LiteralPath $file.FullName -Encoding UTF8 -Raw
            if ($text -match $forbidden) { throw "Legacy marker found: $($file.FullName)" }
            if ($text -match $secretLike) { throw "Secret-like value found: $($file.FullName)" }
        }
    }
}
Scan-TextRoots @('README.md', 'ENVIRONMENT-MCP-INVENTORY.md', 'agents', 'manifest', 'scripts', 'skills', 'runtime', 'config-fragments')
Scan-TextRoots @((Join-Path $repoRoot 'installer-pack'))

if (-not (Test-Path -LiteralPath (Join-Path $repoRoot 'installer-pack\runtime\requirements-python-win-x64-py312.lock') -PathType Leaf)) { throw 'Pack Python lock file missing.' }
if (-not (Test-Path -LiteralPath (Join-Path $repoRoot 'installer-pack\runtime\wheelhouse-manifest.json') -PathType Leaf)) { throw 'Pack wheelhouse manifest missing.' }
if (-not (Test-Path -LiteralPath (Join-Path $repoRoot 'installer-pack\manifest\runtime-artifacts.json') -PathType Leaf)) { throw 'Pack runtime artifact manifest missing.' }
foreach ($requiredPackFile in @('mcp\mcp-servers.json','mcp\api-services.json','mcp\connection-fields.json','config-fragments\README.md')) {
    if (-not (Test-Path -LiteralPath (Join-Path $repoRoot ('installer-pack\' + $requiredPackFile)) -PathType Leaf)) { throw "Pack extension file missing: $requiredPackFile" }
}
if (@($runtimeArtifacts.artifacts).Count -ne 3) { throw 'Expected Python, wheelhouse and optional Node artifact records.' }
if (@($mcpServers.servers).Count -ne 1 -or [string]$mcpServers.servers[0].id -ne 'feishu') { throw 'MCP inventory must contain the guided Feishu server record.' }
if (@($apiServices.services).Count -ne 3) { throw 'Expected three direct API service records.' }
if (@($connectionFields.fields).Count -ne 10) { throw 'Expected ten guided connection fields.' }

if ([int]$dependencies.schemaVersion -ne 2) { throw 'Dependency schema must be 2.' }
$dependencyIds = [System.Collections.Generic.HashSet[string]]::new()
foreach ($dependency in $dependencies.dependencyCatalog) {
    if ([string]::IsNullOrWhiteSpace([string]$dependency.id) -or [string]::IsNullOrWhiteSpace([string]$dependency.kind)) { throw 'Dependency catalog entry lacks id/kind.' }
    if (-not $dependencyIds.Add([string]$dependency.id)) { throw "Duplicate dependency catalog id: $($dependency.id)" }
}
foreach ($skillEntry in $dependencies.skills) {
    foreach ($dependencyId in @($skillEntry.dependencies)) {
        if (-not $dependencyIds.Contains([string]$dependencyId)) { throw "Skill dependency not in catalog: $($skillEntry.id) -> $dependencyId" }
    }
}
if (@($dependencies.skills).Count -ne 50 -or @($dependencies.agents).Count -ne 7) { throw 'Dependency closure does not cover 50 skills and 7 agents.' }

$defaultSkills = @($pack.defaultEnabled.skills)
$auditDefaultSkills = @($audit.skills | Where-Object { $_.installByDefault } | ForEach-Object { $_.id })
if (@(Compare-Object ($defaultSkills | Sort-Object) ($auditDefaultSkills | Sort-Object)).Count -gt 0) { throw 'Pack default skills differ from audit installByDefault.' }
foreach ($skill in $defaultSkills) {
    $item = @($audit.skills | Where-Object { $_.id -eq $skill })[0]
    if (-not $item -or $item.afterRemediationStatus -ne 'core-ready' -or -not $item.installByDefault) { throw "Invalid default skill status: $skill" }
}

foreach ($entry in $fileManifest.files) {
    $path = Resolve-PackFile ([string]$entry.path)
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Manifest file missing: $($entry.path)" }
    $hash = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($hash -ne ([string]$entry.sha256).ToLowerInvariant()) { throw "Hash mismatch: $($entry.path)" }
}

$checksumFile = Join-Path $repoRoot 'installer-pack\checksums.sha256'
if (-not (Test-Path -LiteralPath $checksumFile -PathType Leaf)) { throw 'checksums.sha256 is missing.' }
$checksumPaths = [System.Collections.Generic.HashSet[string]]::new()
foreach ($line in Get-Content -LiteralPath $checksumFile -Encoding UTF8) {
    if ([string]::IsNullOrWhiteSpace($line)) { continue }
    $match = [regex]::Match($line, '^(?<hash>[0-9a-fA-F]{64}) \*(?<path>.+)$')
    if (-not $match.Success) { throw "Invalid checksum line: $line" }
    $relative = $match.Groups['path'].Value.Trim()
    if (-not $checksumPaths.Add($relative)) { throw "Duplicate checksum path: $relative" }
    $path = Resolve-PackFile $relative
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Checksum file missing: $relative" }
    $actual = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $match.Groups['hash'].Value.ToLowerInvariant()) { throw "Checksum mismatch: $relative" }
}
$allPackFiles = @(Get-ChildItem -LiteralPath (Join-Path $repoRoot 'installer-pack') -Recurse -File | ForEach-Object { $_.FullName.Substring((Join-Path $repoRoot 'installer-pack').Length + 1).Replace('\','/') } | Where-Object { $_ -ne 'checksums.sha256' })
if (@(Compare-Object ($allPackFiles | Sort-Object) (@($checksumPaths) | Sort-Object)).Count -gt 0) { throw 'checksums.sha256 does not cover every pack file.' }

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { throw 'Verification requires Python 3 for syntax checks.' }
$pyFiles = @(Get-ChildItem -LiteralPath (Join-Path $repoRoot 'skills') -Recurse -Filter '*.py' -File)
foreach ($pyFile in $pyFiles) {
    & $python.Source -m py_compile $pyFile.FullName
    if ($LASTEXITCODE -ne 0) { throw "Python syntax check failed: $($pyFile.FullName)" }
}
& $python.Source -c "import tomllib, pathlib; [tomllib.loads(p.read_text(encoding='utf-8')) for p in pathlib.Path('agents').glob('*.toml')]"
if ($LASTEXITCODE -ne 0) { throw 'Agent TOML parse failed.' }

$psParser = [System.Management.Automation.Language.Parser]
$psFiles = @(Get-ChildItem -LiteralPath (Join-Path $repoRoot 'skills') -Recurse -Filter '*.ps1' -File) + @(Get-ChildItem -LiteralPath (Join-Path $repoRoot 'scripts') -Filter '*.ps1' -File)
foreach ($psFile in $psFiles) {
    $tokens = $null
    $errors = $null
    $null = $psParser::ParseFile($psFile.FullName, [ref]$tokens, [ref]$errors)
    if ($errors.Count -gt 0) { throw "PowerShell syntax check failed: $($psFile.FullName)" }
}

$smokeRoot = Join-Path $repoRoot ('.verify-smoke-' + [guid]::NewGuid().ToString('N'))
$oldWeatherData = $env:WEATHER_DATA_DIR
$oldCodexData = $env:CODEX_DATA_DIR
try {
    New-Item -ItemType Directory -Force -Path $smokeRoot | Out-Null
    $ps = (Get-Command powershell -ErrorAction SilentlyContinue)
    if (-not $ps) { throw 'Windows PowerShell is required for the PowerShell smoke tests.' }
    & $ps.Source -NoProfile -ExecutionPolicy Bypass -File (Join-Path $repoRoot 'skills\python-env-setup\scripts\check_python_env.ps1') -Json | ConvertFrom-Json | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Python environment smoke test failed.' }
    $searchJson = & $ps.Source -NoProfile -ExecutionPolicy Bypass -File (Join-Path $repoRoot 'skills\skills-search\scripts\skills_search.ps1') -Keyword '视频' -Root $repoRoot -Json | ConvertFrom-Json
    if (@($searchJson).Count -lt 1) { throw 'Skill search smoke test returned no result.' }
    $env:WEATHER_DATA_DIR = Join-Path $smokeRoot 'weather'
    & $ps.Source -NoProfile -ExecutionPolicy Bypass -File (Join-Path $repoRoot 'skills\weather-forecast\scripts\weather_db.ps1') -Command set_city -City 'Shanghai' | Out-Null
    $city = & $ps.Source -NoProfile -ExecutionPolicy Bypass -File (Join-Path $repoRoot 'skills\weather-forecast\scripts\weather_db.ps1') -Command get_city
    if ([string]$city -ne 'Shanghai') { throw 'Weather persistence smoke test failed.' }
    $env:CODEX_DATA_DIR = $smokeRoot
    & $ps.Source -NoProfile -ExecutionPolicy Bypass -File (Join-Path $repoRoot 'skills\daily-reflection\scripts\reflection.ps1') -Command health | ConvertFrom-Json | Out-Null
    & $ps.Source -NoProfile -ExecutionPolicy Bypass -File (Join-Path $repoRoot 'skills\daily-reflection\scripts\reflection.ps1') -Command log -Text 'verification smoke test' -Energy 7 -Focus 8 | ConvertFrom-Json | Out-Null
    $summary = & $ps.Source -NoProfile -ExecutionPolicy Bypass -File (Join-Path $repoRoot 'skills\daily-reflection\scripts\reflection.ps1') -Command summary | ConvertFrom-Json
    if (@($summary).Count -lt 1) { throw 'Reflection storage smoke test failed.' }
    Write-Host 'PowerShell smoke tests passed.' -ForegroundColor Green
}
finally {
    $env:WEATHER_DATA_DIR = $oldWeatherData
    $env:CODEX_DATA_DIR = $oldCodexData
    if (Test-Path -LiteralPath $smokeRoot) { Remove-Item -LiteralPath $smokeRoot -Recurse -Force }
}

Write-Host 'Status counts:' -ForegroundColor Cyan
$audit.skills | Group-Object status | Sort-Object Name | ForEach-Object { Write-Host ("  {0}: {1}" -f $_.Name, $_.Count) }
Write-Host 'After-remediation counts:' -ForegroundColor Cyan
$audit.skills | Group-Object afterRemediationStatus | Sort-Object Name | ForEach-Object { Write-Host ("  {0}: {1}" -f $_.Name, $_.Count) }
Write-Host "Default skills: $($defaultSkills.Count)"
Write-Host "Runtime artifacts: $(@($runtimeArtifacts.artifacts).Count); MCP servers: $(@($mcpServers.servers).Count); API services: $(@($apiServices.services).Count)"
Write-Host 'Package verification passed.' -ForegroundColor Green
