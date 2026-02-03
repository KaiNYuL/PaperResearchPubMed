param(
    [string]$DesktopDir = "${PSScriptRoot}\..\desktop"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path $DesktopDir)) {
    throw "desktop 目录不存在：$DesktopDir"
}

Push-Location $DesktopDir
try {
    if (-not (Test-Path "node_modules")) {
        npm install
    }
    npm run build
} finally {
    Pop-Location
}

Write-Host "安装包已生成 -> $DesktopDir\dist"