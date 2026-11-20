# Install Witnis on Windows. Default: full CLI via pip. Optional core binary.
param(
    [switch]$CoreBinary,
    [switch]$FromGit
)

$ErrorActionPreference = "Stop"

$pipTarget = if ($FromGit) {
    "git+https://github.com/L00PLeGeNd/Witnis.git"
} else {
    "witnis"
}

$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) {
    Write-Error "Python 3.11+ required for the full witnis CLI (pip fallback)."
}

Write-Host "==> pip install $pipTarget"
& python -m pip install -U $pipTarget
try {
    Write-Host "==> witnis version: $(witnis version)"
} catch {
    Write-Host "==> witnis version: $(python -m witnis version)"
}

if ($CoreBinary) {
    $artifact = "witnis-core-x86_64-pc-windows-msvc.exe"
    $destDir = if ($env:WITNIS_CORE_DIR) { $env:WITNIS_CORE_DIR } else {
        Join-Path $env:LOCALAPPDATA "Witnis\bin"
    }
    New-Item -ItemType Directory -Force -Path $destDir | Out-Null
    $dest = Join-Path $destDir "witnis-core.exe"
    $url = "https://github.com/L00PLeGeNd/Witnis/releases/latest/download/$artifact"
    Write-Host "==> download $url"
    try {
        Invoke-WebRequest -Uri $url -OutFile $dest -UseBasicParsing
        Write-Host "==> installed $dest"
        Write-Host "Add to PATH if needed: $destDir"
    } catch {
        Write-Warning "Download failed (no release asset yet?). Build locally: cargo build -p witnis-cli --release"
    }
}

Write-Host "Done. Docs: docs/BINARY.md · loop: witnis loop-init"
