param(
    [string]$BackendDir = "${PSScriptRoot}\..\backend",
    [string]$DesktopBackendDir = "${PSScriptRoot}\..\desktop\backend",
    [string]$RuntimeDir = "${PSScriptRoot}\..\desktop\backend\runtime",
    [string]$PythonExe = "python"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path $BackendDir)) {
    throw "backend 目录不存在：$BackendDir"
}

if (-not (Test-Path $DesktopBackendDir)) {
    New-Item -ItemType Directory -Path $DesktopBackendDir | Out-Null
}

if (-not (Test-Path $RuntimeDir)) {
    New-Item -ItemType Directory -Path $RuntimeDir | Out-Null
}
Copy-Item -Path (Join-Path $BackendDir "*") -Destination $DesktopBackendDir -Recurse -Force

Write-Host "后端代码已同步 -> $DesktopBackendDir"

if ($PythonExe -eq "python") {
    $candidate = "C:\Users\KN\AppData\Local\Programs\Python\Python311\python.exe"
    if (Test-Path $candidate) {
        $PythonExe = $candidate
    }
}

Push-Location $BackendDir
try {
    & $PythonExe -m venv $RuntimeDir
    $basePrefix = (& $PythonExe -c "import sys; print(sys.base_prefix)").Trim()
    if ($basePrefix) {
        $baseDlls = Join-Path $basePrefix "DLLs"
        $runtimeDlls = Join-Path $RuntimeDir "DLLs"
        if (-not (Test-Path $runtimeDlls)) {
            New-Item -ItemType Directory -Path $runtimeDlls | Out-Null
        }
        if (Test-Path $baseDlls) {
            Copy-Item -Path (Join-Path $baseDlls "*") -Destination $runtimeDlls -Recurse -Force
        }
        Copy-Item -Path (Join-Path $basePrefix "*.dll") -Destination $RuntimeDir -Force -ErrorAction SilentlyContinue
    }
    & (Join-Path $RuntimeDir "Scripts\python.exe") -m pip install --upgrade pip
    $runtimePython = Join-Path $RuntimeDir "Scripts\python.exe"
    & $runtimePython -m pip install -r requirements.txt
    $lxmlOk = $true
    try {
        & $runtimePython -c "from lxml import etree" 2>$null
        if ($LASTEXITCODE -ne 0) { $lxmlOk = $false }
    } catch {
        $lxmlOk = $false
    }
    if (-not $lxmlOk) {
        Write-Host "检测到 lxml 异常，尝试重新安装 lxml..."
        & $runtimePython -m pip install --force-reinstall --no-cache-dir lxml==6.0.2
    }
} finally {
    Pop-Location
}

Write-Host "后端依赖已安装到 runtime -> $RuntimeDir"