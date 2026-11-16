$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location -LiteralPath $projectRoot
try {
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        throw 'Can cai uv truoc. Xem README.md hoac dung Python 3.12 + pip.'
    }
    $env:UV_CACHE_DIR = Join-Path $projectRoot '.cache\uv'
    $env:UV_PYTHON_INSTALL_DIR = Join-Path $projectRoot '.python'
    uv sync --python 3.12 --locked
    if ($LASTEXITCODE -ne 0) { throw 'Cai moi truong that bai' }
    Write-Output 'San sang. Chay .\.venv\Scripts\python.exe -m cvjd_gnn --help'
} finally {
    Pop-Location
}
