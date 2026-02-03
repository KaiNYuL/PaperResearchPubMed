param(
    [string]$BackendDir = "${PSScriptRoot}\..\backend",
    [string]$PythonExe = "python"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path $BackendDir)) {
    throw "backend 目录不存在：$BackendDir"
}

$env:PYTHONPATH = $BackendDir
Push-Location $BackendDir
try {
    & $PythonExe -m unittest discover -s tests -p "test_*.py"
} finally {
    Pop-Location
}
