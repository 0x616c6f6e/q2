param(
    [string]$Python = 'python',
    [string]$CMake = 'cmake',
    [string]$Compiler = 'zig',
    [string]$Ninja = '',
    [string]$Config = '',
    [ValidateSet('x86','host','kernel','esp32s31','esp32s3')][string]$Target = 'x86',
    [string]$BuildDir = '',
    [string]$AppName = '',
    [switch]$Headless,
    [switch]$SingleApp,
    [switch]$DisableWeb,
    [int]$Frames = 0,
    [string]$Capture = '',
    [switch]$Test
)
$ErrorActionPreference = 'Stop'
if (-not $Config) {
    $q2ConfigName = if ($Target -eq 'esp32s3') { 'q2.esp32s3.json' } else { 'q2.json' }
    $Config = Join-Path $PSScriptRoot $q2ConfigName
}
$q2Action = 'build' 
if ($Test) { $q2Action = 'test' }
$q2Args = @((Join-Path $PSScriptRoot 'q2.py'), $q2Action, '--target', $Target, '--config', $Config, '--cmake', $CMake)
if ($Compiler) { $q2Args += @('--compiler', $Compiler) }
if ($Ninja) { $q2Args += @('--ninja', $Ninja) }
if ($BuildDir) { $q2Args += @('--build-dir', $BuildDir) }
if ($AppName) { $q2Args += @('--app', $AppName) }
if ($Headless) { $q2Args += '--headless' }
if ($SingleApp) { $q2Args += '--single-app' }
if ($DisableWeb) { $q2Args += '--disable-web' }
if ($Frames) { $q2Args += @('--frames', "$Frames") }
if ($Capture) { $q2Args += @('--capture', $Capture) }
& $Python @q2Args
if ($LASTEXITCODE -ne 0) { throw "Q2 $q2Action failed ($LASTEXITCODE)" }
