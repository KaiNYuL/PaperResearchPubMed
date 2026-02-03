param(
    [string]$FrontendDir = "${PSScriptRoot}\..\frontend",
    [string]$OutDir = "${PSScriptRoot}\..\desktop\renderer"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path $FrontendDir)) {
    throw "Frontend directory not found: $FrontendDir"
}

Push-Location $FrontendDir
try {
    $hasLock = Test-Path "package-lock.json"
    if (-not (Test-Path "node_modules")) {
        if ($hasLock) {
            npm ci
        } else {
            npm install
        }
    }

    if (Test-Path "dist") {
        Remove-Item "dist" -Recurse -Force
    }

    npm run build
} finally {
    Pop-Location
}

if (Test-Path $OutDir) {
    Remove-Item $OutDir -Recurse -Force
}
New-Item -ItemType Directory -Path $OutDir | Out-Null

$distDir = Join-Path $FrontendDir "dist"
if (-not (Test-Path $distDir)) {
    throw "Frontend build failed: dist folder not found."
}

Get-ChildItem -Path $distDir | Copy-Item -Destination $OutDir -Recurse -Force

Write-Host "Frontend build completed -> $OutDir"
