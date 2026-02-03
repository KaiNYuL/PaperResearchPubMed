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

if (Test-Path $RuntimeDir) {
    $needsClean = $false
    if ($env:PAPER_AGENT_CLEAN_RUNTIME -eq "1") {
        $needsClean = $true
    } elseif (Test-Path (Join-Path $RuntimeDir "Lib\site-packages\numpy\setup.py")) {
        $needsClean = $true
    }
    if ($needsClean) {
        Remove-Item -Path $RuntimeDir -Recurse -Force
    }
}
if (-not (Test-Path $RuntimeDir)) {
    New-Item -ItemType Directory -Path $RuntimeDir | Out-Null
}
Copy-Item -Path (Join-Path $BackendDir "*") -Destination $DesktopBackendDir -Recurse -Force

Write-Host "后端代码已同步 -> $DesktopBackendDir"

if ($PythonExe -eq "python" -and $env:PAPER_AGENT_PYTHON) {
    if (Test-Path $env:PAPER_AGENT_PYTHON) {
        $PythonExe = $env:PAPER_AGENT_PYTHON
    }
}

Push-Location $BackendDir
try {
    & $PythonExe -m venv $RuntimeDir
    $requirementsFile = Join-Path $BackendDir "requirements.txt"
    $requirementsHashFile = Join-Path $RuntimeDir "requirements.sha256"
    $currentHash = (Get-FileHash $requirementsFile -Algorithm SHA256).Hash
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

        $condaBin = Join-Path $basePrefix "Library\bin"
        if (Test-Path $condaBin) {
            Get-ChildItem -Path $condaBin -Filter "*.dll" | Copy-Item -Destination $runtimeDlls -Force
        }

        $opensslDlls = @("libssl*.dll", "libcrypto*.dll")
        foreach ($pattern in $opensslDlls) {
            if (Test-Path $baseDlls) {
                Get-ChildItem -Path $baseDlls -Filter $pattern | Copy-Item -Destination $runtimeDlls -Force -ErrorAction SilentlyContinue
            }
            if (Test-Path $condaBin) {
                Get-ChildItem -Path $condaBin -Filter $pattern | Copy-Item -Destination $runtimeDlls -Force -ErrorAction SilentlyContinue
            }
            Get-ChildItem -Path $basePrefix -Filter $pattern | Copy-Item -Destination $runtimeDlls -Force -ErrorAction SilentlyContinue
        }
    }
    & (Join-Path $RuntimeDir "Scripts\python.exe") -m pip install --upgrade pip
    $runtimePython = Join-Path $RuntimeDir "Scripts\python.exe"

    $needsInstall = $true
    if (Test-Path $requirementsHashFile) {
        $savedHash = (Get-Content $requirementsHashFile -ErrorAction SilentlyContinue).Trim()
        if ($savedHash -and $savedHash -eq $currentHash) {
            $needsInstall = $false
        }
    }
    if ($needsInstall) {
        & $runtimePython -m pip install -r requirements.txt
        $currentHash | Set-Content -Path $requirementsHashFile -Encoding ASCII
    }
    $sslOk = $true
    try {
        & $runtimePython -c "import ssl" 2>$null
        if ($LASTEXITCODE -ne 0) { $sslOk = $false }
    } catch {
        $sslOk = $false
    }
    if (-not $sslOk) {
        Write-Host "SSL module check failed. Ensure your Python installation includes OpenSSL DLLs."
    }

    $pydanticCoreOk = $true
    try {
        & $runtimePython -c "import pydantic_core" 2>$null
        if ($LASTEXITCODE -ne 0) { $pydanticCoreOk = $false }
    } catch {
        $pydanticCoreOk = $false
    }
    if (-not $pydanticCoreOk) {
        Write-Host "pydantic_core check failed, reinstalling..."
        & $runtimePython -m pip install --force-reinstall --no-cache-dir pydantic-core==2.41.5
    }

    $numpyOk = $true
    try {
        & $runtimePython -c "import numpy" 2>$null
        if ($LASTEXITCODE -ne 0) { $numpyOk = $false }
    } catch {
        $numpyOk = $false
    }
    if (-not $numpyOk) {
        Write-Host "numpy check failed, reinstalling..."
        & $runtimePython -m pip install --force-reinstall --no-cache-dir numpy
    }

    $tiktokenOk = $true
    try {
        & $runtimePython -c "import tiktoken" 2>$null
        if ($LASTEXITCODE -ne 0) { $tiktokenOk = $false }
    } catch {
        $tiktokenOk = $false
    }
    if (-not $tiktokenOk) {
        Write-Host "tiktoken check failed, reinstalling..."
        & $runtimePython -m pip install --force-reinstall --no-cache-dir tiktoken
    }

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