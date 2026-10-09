$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $projectRoot ".venv\Scripts\python.exe"
$logsPath = Join-Path $projectRoot "logs"

if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw "Virtual environment not found: $pythonPath"
}

New-Item -ItemType Directory -Path $logsPath -Force | Out-Null
& $pythonPath (Join-Path $projectRoot "manage.py") migrate --noinput

$djangoListener = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
if (-not $djangoListener) {
    Start-Process -FilePath $pythonPath `
        -ArgumentList @("manage.py", "runserver", "127.0.0.1:8000", "--noreload") `
        -WorkingDirectory $projectRoot `
        -RedirectStandardOutput (Join-Path $logsPath "django.out.log") `
        -RedirectStandardError (Join-Path $logsPath "django.error.log") `
        -WindowStyle Hidden
}

$botRunning = Get-CimInstance Win32_Process | Where-Object {
    $_.ExecutablePath -eq $pythonPath -and $_.CommandLine -like "*main.py*"
}
if (-not $botRunning) {
    Start-Process -FilePath $pythonPath `
        -ArgumentList @("main.py") `
        -WorkingDirectory (Join-Path $projectRoot "telegram_bot") `
        -RedirectStandardOutput (Join-Path $logsPath "telegram-bot.out.log") `
        -RedirectStandardError (Join-Path $logsPath "telegram-bot.error.log") `
        -WindowStyle Hidden
}

Write-Host "MTU FORUM: http://127.0.0.1:8000/"
Write-Host "Django and Telegram bot are running. Logs: $logsPath"
