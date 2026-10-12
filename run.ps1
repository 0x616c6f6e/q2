param(
    [string]$Python = 'python',
    [string]$CMake = 'cmake',
    [string]$Compiler = '',
    [string]$Ninja = '',
    [string]$Config = '',
    [ValidateSet('x86','host','kernel','esp32s31','esp32s3')][string]$Target = '',
    [string]$Profile = '',
    [string]$BuildDir = '',
    [string]$AppName = '',
    [switch]$Headless,
    [switch]$SingleApp,
    [switch]$DisableWeb,
    [int]$Frames = 0,
    [string]$Capture = '',
    [string]$Port = '',
    [int]$Baud = 0,
    [int]$MonitorBaud = 0,
    [switch]$FlashOnly,
    [switch]$MonitorOnly,
    [switch]$Test
)
$ErrorActionPreference = 'Stop'
$q2Action = 'run'
if ($Test) { $q2Action = 'test' }
$q2Args = @((Join-Path $PSScriptRoot 'q2.py'), $q2Action, '--cmake', $CMake)
if ($Target) { $q2Args += @('--target', $Target) }
if ($Profile) { $q2Args += @('--profile', $Profile) }
if ($Config) { $q2Args += @('--config', $Config) }
if ($Compiler) { $q2Args += @('--compiler', $Compiler) }
if ($Ninja) { $q2Args += @('--ninja', $Ninja) }
if ($BuildDir) { $q2Args += @('--build-dir', $BuildDir) }
if ($AppName) { $q2Args += @('--app', $AppName) }
if ($Headless) { $q2Args += '--headless' }
if ($SingleApp) { $q2Args += '--single-app' }
if ($DisableWeb) { $q2Args += '--disable-web' }
if ($Frames) { $q2Args += @('--frames', "$Frames") }
if ($Capture) { $q2Args += @('--capture', $Capture) }
if ($Port) { $q2Args += @('--port', $Port) }
if ($Baud) { $q2Args += @('--baud', "$Baud") }
if ($MonitorBaud) { $q2Args += @('--monitor-baud', "$MonitorBaud") }
if ($FlashOnly) { $q2Args += '--flash-only' }
if ($MonitorOnly) { $q2Args += '--monitor-only' }
& $Python @q2Args
if ($LASTEXITCODE -ne 0) { throw "Q2 $q2Action failed ($LASTEXITCODE)" }
