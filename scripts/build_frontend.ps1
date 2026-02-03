param(
    [string]$FrontendDir = "${PSScriptRoot}\..\frontend",
    [string]$OutDir = "${PSScriptRoot}\..\desktop\renderer"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path $FrontendDir)) {
    throw "frontend 目录不存在：$FrontendDir"
}

Push-Location $FrontendDir
try {
    if (-not (Test-Path "node_modules")) {
        npm install
    }
    npm run build
} finally {
    Pop-Location
}

if (Test-Path $OutDir) {
    Remove-Item $OutDir -Recurse -Force
}
New-Item -ItemType Directory -Path $OutDir | Out-Null
Copy-Item -Path (Join-Path $FrontendDir "dist\*") -Destination $OutDir -Recurse -Force

Write-Host "前端构建完成 -> $OutDir"