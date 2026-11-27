# Start both FastAPI backend (127.0.0.1:8000) and Next.js frontend (127.0.0.1:3000)
# with live hot-reload for fast local development on Windows.

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "Starting FastAPI backend on http://127.0.0.1:8000 ..." -ForegroundColor Cyan
$backend = Start-Process -FilePath "$root\backend\.venv\Scripts\uvicorn.exe" `
    -ArgumentList "app.main:create_app", "--factory", "--host", "127.0.0.1", "--port", "8000", "--reload" `
    -WorkingDirectory "$root\backend" `
    -PassThru

Write-Host "Starting Next.js frontend on http://127.0.0.1:3000 ..." -ForegroundColor Green
$frontend = Start-Process -FilePath "npm.cmd" `
    -ArgumentList "run", "dev" `
    -WorkingDirectory "$root\frontend" `
    -PassThru

Write-Host ""
Write-Host "Both servers launched! Press Ctrl+C or close their windows to stop." -ForegroundColor Yellow
Write-Host "  Frontend: http://127.0.0.1:3000"
Write-Host "  Backend:  http://127.0.0.1:8000/docs"
Write-Host ""

try {
    Wait-Process -Id $backend.Id, $frontend.Id
} finally {
    if (-not $backend.HasExited) { Stop-Process -Id $backend.Id -Force -ErrorAction SilentlyContinue }
    if (-not $frontend.HasExited) { Stop-Process -Id $frontend.Id -Force -ErrorAction SilentlyContinue }
}
