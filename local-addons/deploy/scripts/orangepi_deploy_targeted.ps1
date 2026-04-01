#!/usr/bin/env pwsh
<##
.SYNOPSIS
Deploy only the local addon files to the Orange Pi and restart the addon overlay.

.DESCRIPTION
This script copies a curated set of local addon files to the remote ~/open-notebook
and restarts Docker Compose using the base Orange Pi compose plus the addon overlay.
It prefers rsync via WSL if available, otherwise falls back to scp.

.PARAMETER RemoteHost
Remote host (default root@192.168.2.129)

.PARAMETER SshKey
SSH private key path (optional)

.PARAMETER Files
Array of files or directories relative to the repo root.

.PARAMETER DryRun
If set, prints commands without executing them.

.EXAMPLE
PS> .\local-addons\deploy\scripts\orangepi_deploy_targeted.ps1 -RemoteHost root@192.168.2.129 -SshKey C:\Users\you\.ssh\id_rsa
#>

param(
    [string]$RemoteHost = "root@192.168.2.129",
    [string]$SshKey = "",
    [switch]$DryRun = $false,
    [string[]]$Files = @(
        "local-addons/cdisc",
        "local-addons/deploy/docker-compose.orangepi.addons.yml",
        "local-addons/deploy/Caddyfile.lan.cdisc"
    )
)

function ConvertTo-BashQuotedString {
    param([string]$Value)

    if ($null -eq $Value -or $Value -eq "") {
        return "''"
    }

    $singleQuoteEscape = [string][char]39 + [char]34 + [char]39 + [char]34 + [char]39
    $escapedValue = $Value.Replace("'", $singleQuoteEscape)
    return "'" + $escapedValue + "'"
}

function ConvertTo-WslPath {
    param([string]$WindowsPath)

    if ($WindowsPath -match '^[A-Za-z]:\\') {
        $driveLetter = $WindowsPath.Substring(0, 1).ToLower()
        $pathRemainder = $WindowsPath.Substring(2).Replace([char]92, [char]47)
        return "/mnt/$driveLetter$pathRemainder"
    }

    return $WindowsPath.Replace([char]92, [char]47)
}

function Invoke-ShellCommand {
    param([string]$Command)

    if ($DryRun) {
        Write-Host "DRY-RUN: $Command"
        return
    }

    Write-Host "RUN: $Command"
    Invoke-Expression $Command
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $scriptDir "..\..\.."))
$remoteRoot = "~/open-notebook"

Write-Host "Targeted addon deploy to $RemoteHost"

$existingFiles = @()
foreach ($relativePath in $Files) {
    $localPath = Join-Path $repoRoot $relativePath
    if (Test-Path $localPath) {
        $existingFiles += $relativePath
    } else {
        Write-Warning "Skipping missing path: $relativePath"
    }
}

if ($existingFiles.Count -eq 0) {
    Write-Error "No files found to copy. Exiting."
    exit 2
}

if (Get-Command wsl -ErrorAction SilentlyContinue) {
    Write-Host "Using WSL and rsync for transfer"
    $wslRepoRoot = ConvertTo-WslPath $repoRoot
    $rsyncArgs = @("-av", "--prune-empty-dirs", "--relative")
    if ($SshKey) {
        $wslSshKey = ConvertTo-WslPath ([System.IO.Path]::GetFullPath($SshKey))
        $rsyncArgs += "-e"
        $rsyncArgs += ("ssh -i " + (ConvertTo-BashQuotedString $wslSshKey))
    }

    $quotedArgs = $rsyncArgs | ForEach-Object { ConvertTo-BashQuotedString $_ }
    $quotedFiles = $existingFiles | ForEach-Object { ConvertTo-BashQuotedString $_ }
    $rsyncDestination = "${RemoteHost}:$remoteRoot/"
    $rsyncCommand = "cd " + (ConvertTo-BashQuotedString $wslRepoRoot) + " && rsync " + ($quotedArgs -join ' ') + " " + ($quotedFiles -join ' ') + " " + (ConvertTo-BashQuotedString $rsyncDestination)

    if ($DryRun) {
        Write-Host "DRY-RUN: wsl bash -lc $rsyncCommand"
    } else {
        Write-Host "RUN: wsl bash -lc $rsyncCommand"
        & wsl bash -lc $rsyncCommand
        if ($LASTEXITCODE -ne 0) {
            exit $LASTEXITCODE
        }
    }
} else {
    Write-Host "WSL not found. Falling back to scp"
    foreach ($relativePath in $existingFiles) {
        $localPath = Join-Path $repoRoot $relativePath
        $remoteParent = Split-Path $relativePath -Parent
        if ([string]::IsNullOrEmpty($remoteParent)) {
            $remoteParent = "."
        }

        $mkdirRemote = "ssh "
        if ($SshKey) {
            $mkdirRemote += "-i `"$SshKey`" "
        }
        $mkdirRemote += "$RemoteHost bash -lc " + (ConvertTo-BashQuotedString ("mkdir -p $remoteRoot/$remoteParent"))
        Invoke-ShellCommand $mkdirRemote

        $scpCommand = "scp "
        if (Test-Path $localPath -PathType Container) {
            $scpCommand += "-r "
        }
        if ($SshKey) {
            $scpCommand += "-i `"$SshKey`" "
        }
        $scpCommand += "`"$localPath`" ${RemoteHost}:$remoteRoot/$remoteParent/"
        Invoke-ShellCommand $scpCommand
    }
}

$sshPrefix = ""
if ($SshKey) {
    $sshPrefix = "-i `"$SshKey`""
}

$remoteComposeCmd = "set -e; mkdir -p $remoteRoot/local-addons/deploy; cd $remoteRoot; if command -v docker >/dev/null 2>&1; then docker compose -f docker-compose.orangepi.dev.yml -f local-addons/deploy/docker-compose.orangepi.addons.yml up -d --remove-orphans; else echo 'Docker not found on remote' >&2; exit 2; fi"
$sshCompose = "ssh $sshPrefix $RemoteHost bash -lc " + (ConvertTo-BashQuotedString $remoteComposeCmd)
Invoke-ShellCommand $sshCompose

Write-Host "Targeted addon deploy complete."
exit 0
