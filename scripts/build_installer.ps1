param(
	[string]$DesktopDir = "${PSScriptRoot}\..\desktop",
	[string]$FrontendScript = "${PSScriptRoot}\build_frontend.ps1",
	[string]$BackendScript = "${PSScriptRoot}\build_backend.ps1"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path $DesktopDir)) {
	throw "Desktop directory not found: $DesktopDir"
}

if (Test-Path $FrontendScript) {
	& $FrontendScript
} else {
	throw "Frontend build script not found: $FrontendScript"
}

if (Test-Path $BackendScript) {
	& $BackendScript
} else {
	throw "Backend build script not found: $BackendScript"
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

Write-Host "Installer build completed -> $DesktopDir\dist"
