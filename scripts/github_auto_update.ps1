param(
    [string]$RemoteUrl = "",
    [string]$Branch = "main",
    [string]$Message = ""
)

$ErrorActionPreference = "Stop"

function Write-Step($Text) {
    Write-Host "==> $Text" -ForegroundColor Cyan
}

if (-not (Test-Path "manage.py")) {
    throw "Run this script from the Django project root where manage.py exists."
}

if (-not (Test-Path ".git")) {
    Write-Step "Initializing git repository"
    git init
}

$currentBranch = git branch --show-current
if (-not $currentBranch) {
    Write-Step "Creating branch $Branch"
    git checkout -B $Branch
} elseif ($currentBranch -ne $Branch) {
    Write-Step "Switching to branch $Branch"
    git checkout -B $Branch
}

$origin = git remote get-url origin 2>$null
if (-not $origin) {
    if (-not $RemoteUrl) {
        throw "GitHub remote is missing. Run: .\scripts\github_auto_update.ps1 -RemoteUrl https://github.com/USER/REPO.git"
    }
    Write-Step "Adding GitHub remote"
    git remote add origin $RemoteUrl
} elseif ($RemoteUrl -and $origin -ne $RemoteUrl) {
    Write-Step "Updating GitHub remote"
    git remote set-url origin $RemoteUrl
}

Write-Step "Checking Django project"
python manage.py check

Write-Step "Staging safe project files"
git add .

$changes = git status --porcelain
if (-not $changes) {
    Write-Step "No changes to commit"
    exit 0
}

if (-not $Message) {
    $stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $Message = "Auto update MTU Forum $stamp"
}

Write-Step "Committing changes"
git commit -m $Message

Write-Step "Pushing to GitHub"
git push -u origin $Branch

Write-Step "GitHub update completed"
