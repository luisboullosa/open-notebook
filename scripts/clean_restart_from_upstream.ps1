param(
    [string]$BackupBase = "local_backups",
    [string]$WorktreePath = "../open-notebook-clean",
    [string]$NewBranch = "restart/upstream-main",
    [string]$UpstreamRef = "upstream/main"
)

$ErrorActionPreference = 'Stop'

function Copy-IfExists {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Source,
        [Parameter(Mandatory = $true)]
        [string]$Destination
    )

    if (-not (Test-Path -LiteralPath $Source)) {
        return
    }

    $sourceItem = Get-Item -LiteralPath $Source
    if ($sourceItem.PSIsContainer) {
        New-Item -ItemType Directory -Path $Destination -Force | Out-Null
        Copy-Item -LiteralPath (Join-Path $Source '*') -Destination $Destination -Recurse -Force -ErrorAction SilentlyContinue
    }
    else {
        $parent = Split-Path -Parent $Destination
        if ($parent -and -not (Test-Path -LiteralPath $parent)) {
            New-Item -ItemType Directory -Path $parent -Force | Out-Null
        }
        Copy-Item -LiteralPath $Source -Destination $Destination -Force
    }
}

Set-Location (Split-Path -Parent $PSScriptRoot)

$repoRoot = (Get-Location).Path
$timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$backupRoot = Join-Path $repoRoot "$BackupBase/$timestamp"

New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null

$pathsToPreserve = @(
    '.secrets',
    'docker.env',
    'docker.orangepi.env',
    'duckdns.env',
    'letsencrypt',
    'setup_guide/docker.env',
    'data/uploads',
    'notebook_data',
    'surreal_data',
    'surreal_single_data',
    'anki',
    'rebase_preservation'
)

$manifestPath = Join-Path $backupRoot 'preserved_paths.txt'
$pathsToPreserve | Set-Content -Path $manifestPath

foreach ($relativePath in $pathsToPreserve) {
    $source = Join-Path $repoRoot $relativePath
    $dest = Join-Path $backupRoot $relativePath
    Copy-IfExists -Source $source -Destination $dest
}

git status --short | Set-Content -Path (Join-Path $backupRoot 'git_status_short.txt')
git branch --show-current | Set-Content -Path (Join-Path $backupRoot 'current_branch.txt')
git --no-pager log --oneline -n 30 | Set-Content -Path (Join-Path $backupRoot 'recent_commits.txt')

git fetch upstream --prune

git show-ref --verify --quiet "refs/heads/$NewBranch"
if ($LASTEXITCODE -ne 0) {
    git branch $NewBranch $UpstreamRef
}

if (Test-Path -LiteralPath $WorktreePath) {
    Write-Host "Worktree path already exists: $WorktreePath" -ForegroundColor Yellow
}
else {
    git worktree add $WorktreePath $NewBranch
}

Write-Host "Clean restart prep complete." -ForegroundColor Green
Write-Host "Backup created at: $backupRoot"
Write-Host "Fresh worktree: $WorktreePath (branch: $NewBranch, base: $UpstreamRef)"