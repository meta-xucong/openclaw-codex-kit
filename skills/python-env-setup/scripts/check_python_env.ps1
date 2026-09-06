[CmdletBinding()]
param(
    [switch]$Json,
    [switch]$RepairPath,
    [switch]$Install
)

$ErrorActionPreference = 'Stop'
$checks = @()

function Test-PythonCommand([string]$Label, [string]$Command, [string[]]$Arguments) {
    $commandInfo = Get-Command $Command -ErrorAction SilentlyContinue
    if (-not $commandInfo) { return $null }
    try {
        $output = (& $commandInfo.Source @Arguments '--version' 2>&1 | Out-String).Trim()
        if ($LASTEXITCODE -ne 0 -or $output -notmatch '(?i)^Python\s+3\.') { return $null }
        return [ordered]@{ command = $Label; path = $commandInfo.Source; version = $output }
    } catch {
        return [ordered]@{ command = $Label; path = $commandInfo.Source; error = $_.Exception.Message }
    }
}

$checks += Test-PythonCommand 'python' 'python' @()
$checks += Test-PythonCommand 'py -3' 'py' @('-3')
$checks += Test-PythonCommand 'python3' 'python3' @()
$match = $checks | Where-Object { $_ -and $_.version } | Select-Object -First 1
$result = [ordered]@{
    available = [bool]$match
    match = $match
    checked = @($checks | Where-Object { $_ })
    pathChanged = $false
    message = if ($match) { 'Python 3 is available.' } else { 'No Python 3 interpreter found; request approval before installing the approved offline runtime.' }
}
if ($RepairPath) { $result.message += ' PATH repair is intentionally manual in this package.' }
if ($Install) { $result.message += ' This checker never downloads or executes an installer.' }
if ($Json) { $result | ConvertTo-Json -Depth 8 } else { $result.message }
if (-not $match) { exit 1 }
