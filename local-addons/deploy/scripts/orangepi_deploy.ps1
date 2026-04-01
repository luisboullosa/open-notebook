#!/usr/bin/env pwsh
<##
.SYNOPSIS
PowerShell wrapper for the upstream Orange Pi shell deploy, resolved from the separated addon layout.

.PARAMETER RemoteHost
Remote host (default root@192.168.2.129)

.PARAMETER LocalSecretsDir
Local secrets directory (default ./.secrets)

.PARAMETER RepoUrl
Optional repository URL (will use git origin if empty)

.PARAMETER SshKey
Optional path to SSH private key

.PARAMETER Compose
Optional compose file path to pass to the upstream shell deploy

.EXAMPLE
PS> .\local-addons\deploy\scripts\orangepi_deploy.ps1 -RemoteHost root@192.168.2.129 -LocalSecretsDir ./.secrets
#>

param(
    [string]$RemoteHost = "root@192.168.2.129",
    [string]$LocalSecretsDir = ".\.secrets",
    [string]$RepoUrl = "",
    [string]$SshKey = "",
    [string]$Compose = "./docker-compose.orangepi.dev.yml"
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

Write-Host "Orange Pi deploy wrapper starting..."

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $scriptDir "..\..\.."))
$upstreamScript = "scripts/orangepi_deploy.sh"

if (Get-Command wsl -ErrorAction SilentlyContinue) {
    $wslRepoRoot = ConvertTo-WslPath $repoRoot

    $argsList = @()
    if ($SshKey) {
        $argsList += "--ssh-key"
        $argsList += (ConvertTo-BashQuotedString (ConvertTo-WslPath ([System.IO.Path]::GetFullPath($SshKey))))
    }
    if ($Compose) {
        $argsList += "--compose"
        $argsList += (ConvertTo-BashQuotedString $Compose)
    }
    $argsList += (ConvertTo-BashQuotedString $RemoteHost)
    $argsList += (ConvertTo-BashQuotedString $LocalSecretsDir)
    if ($RepoUrl) {
        $argsList += (ConvertTo-BashQuotedString $RepoUrl)
    }

    $command = "cd " + (ConvertTo-BashQuotedString $wslRepoRoot) + " && chmod +x $upstreamScript && ./$upstreamScript " + ($argsList -join ' ')
    Write-Host "Running in WSL: $command"
    & wsl bash -lc $command
    exit $LASTEXITCODE
}

if (Get-Command bash -ErrorAction SilentlyContinue) {
    $bashCommand = "./$upstreamScript"
    if ($SshKey) {
        $bashCommand += " --ssh-key " + (ConvertTo-BashQuotedString $SshKey)
    }
    if ($Compose) {
        $bashCommand += " --compose " + (ConvertTo-BashQuotedString $Compose)
    }
    $bashCommand += " " + (ConvertTo-BashQuotedString $RemoteHost)
    $bashCommand += " " + (ConvertTo-BashQuotedString $LocalSecretsDir)
    if ($RepoUrl) {
        $bashCommand += " " + (ConvertTo-BashQuotedString $RepoUrl)
    }

    Push-Location $repoRoot
    try {
        Write-Host "Running via bash: $bashCommand"
        bash -c $bashCommand
        exit $LASTEXITCODE
    } finally {
        Pop-Location
    }
}

Write-Error "Neither WSL nor bash were detected in PATH. Please run the script from WSL or Git Bash."
Write-Host "Example: Open WSL, cd to the repo and run: ./$upstreamScript 192.168.2.129 ./.secrets"
exit 1
