#!/usr/bin/env pwsh
<##
.SYNOPSIS
Native PowerShell deploy for local Orange Pi addons using scp and ssh.

.DESCRIPTION
Uploads the addon compose overlay and addon Caddy config, optionally copies local secrets,
and starts the base Orange Pi stack plus the separated addon overlay on the remote host.

.PARAMETER RemoteHost
Remote host (default root@192.168.2.129)

.PARAMETER LocalSecretsDir
Local secrets directory relative to the repo root (default ./.secrets)

.PARAMETER RepoUrl
Optional repository URL for a remote clone or pull step

.PARAMETER SshKey
Optional path to SSH private key

.PARAMETER Compose
Path to the addon compose overlay relative to the repo root

.PARAMETER Caddyfile
Path to the addon Caddyfile relative to the repo root

.PARAMETER DryRun
If set, prints commands without executing them

.EXAMPLE
PS> .\local-addons\deploy\scripts\orangepi_deploy_native.ps1 -RemoteHost root@192.168.2.129 -SshKey C:\Users\you\.ssh\id_rsa -DryRun
#>

param(
    [string]$RemoteHost = "root@192.168.2.129",
    [string]$LocalSecretsDir = ".\.secrets",
    [string]$RepoUrl = "",
    [string]$SshKey = "",
    [string]$Compose = ".\local-addons\deploy\docker-compose.orangepi.addons.yml",
    [string]$Caddyfile = ".\local-addons\deploy\Caddyfile.lan.cdisc",
    [switch]$DryRun = $false
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
$remoteAddonsDir = "$remoteRoot/local-addons/deploy"

$sshPrefix = ""
if ($SshKey) {
    $sshPrefix = "-i `"$SshKey`""
}

Write-Host "Addon deploy starting: $RemoteHost (dry-run=$DryRun)"

$mkdirRemote = "ssh $sshPrefix $RemoteHost bash -lc " + (ConvertTo-BashQuotedString "mkdir -p $remoteRoot $remoteAddonsDir")
Invoke-ShellCommand $mkdirRemote

$localSecretsPath = Join-Path $repoRoot $LocalSecretsDir
if (Test-Path $localSecretsPath) {
    $scpSecrets = "scp -r $sshPrefix `"$localSecretsPath`" ${RemoteHost}:$remoteRoot/"
    Invoke-ShellCommand $scpSecrets
} else {
    Write-Warning "Local secrets dir $LocalSecretsDir not found; skipping copy."
}

$composePath = Join-Path $repoRoot $Compose
if (Test-Path $composePath) {
    $scpCompose = "scp $sshPrefix `"$composePath`" ${RemoteHost}:$remoteAddonsDir/docker-compose.orangepi.addons.yml"
    Invoke-ShellCommand $scpCompose
} else {
    Write-Warning "Compose file $Compose not found locally; remote addon compose will be used if present."
}

$caddyPath = Join-Path $repoRoot $Caddyfile
if (Test-Path $caddyPath) {
    $scpCaddy = "scp $sshPrefix `"$caddyPath`" ${RemoteHost}:$remoteAddonsDir/Caddyfile.lan.cdisc"
    Invoke-ShellCommand $scpCaddy
} else {
    Write-Warning "Caddyfile $Caddyfile not found locally; remote addon Caddyfile will be used if present."
}

if ($RepoUrl) {
    $quotedRepoUrl = ConvertTo-BashQuotedString $RepoUrl
    $remoteGitCmd = "set -e; mkdir -p $remoteRoot; cd $remoteRoot; if [ -d .git ]; then git fetch --all --prune; git reset --hard origin/main || true; git pull || true; else git clone $quotedRepoUrl . || true; fi"
    $sshGit = "ssh $sshPrefix $RemoteHost bash -lc " + (ConvertTo-BashQuotedString $remoteGitCmd)
    Invoke-ShellCommand $sshGit
}

$remoteComposeCmd = "set -e; cd $remoteRoot; if command -v docker >/dev/null 2>&1; then docker compose -f docker-compose.orangepi.dev.yml -f local-addons/deploy/docker-compose.orangepi.addons.yml up -d --remove-orphans; else echo 'Docker not found on remote' >&2; exit 2; fi"
$sshCompose = "ssh $sshPrefix $RemoteHost bash -lc " + (ConvertTo-BashQuotedString $remoteComposeCmd)
Invoke-ShellCommand $sshCompose

Write-Host "Addon deploy finished."
exit 0
