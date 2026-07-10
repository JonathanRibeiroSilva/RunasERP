<#
Usage:
  .\erp.ps1                 # interactive menu (local dev, no Cloudflare)
  .\erp.ps1 up|down|restart|logs|ps|health|rebuild|prune
  .\erp.ps1 shell <container-name>
  .\erp.ps1 up -Cloudflare  # add Cloudflare Tunnel overlay (public domain)
#>
param(
    [Parameter(Position = 0)]
    [ValidateSet('up', 'down', 'restart', 'logs', 'ps', 'health', 'rebuild', 'prune', 'shell', 'menu')]
    [string]$Command = 'menu',

    [Parameter(Position = 1)]
    [string]$Service,

    [switch]$Cloudflare
)

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

$composeArgs = @('-f', 'docker-compose.dev.yml')
if ($Cloudflare) {
    $composeArgs += @('-f', 'docker-compose.cloudflare.yml', '--profile', 'proxy')
}

function Invoke-Up { docker compose @composeArgs up -d }
function Invoke-Down { docker compose @composeArgs down }
function Invoke-Restart { docker compose @composeArgs restart }
function Invoke-Logs { docker compose @composeArgs logs -f }
function Invoke-Ps { docker compose @composeArgs ps }
function Invoke-Health { docker ps --format "table {{.Names}}`t{{.Status}}`t{{.Ports}}" }
function Invoke-Rebuild { docker compose @composeArgs up -d --build }
function Invoke-Prune { docker system prune -f }

function Invoke-Shell {
    param([string]$Service)
    if (-not $Service) { $Service = Read-Host 'Container name' }
    docker exec -it $Service sh
}

function Show-Menu {
    while ($true) {
        Clear-Host
        Write-Host '============================'
        Write-Host '     RUNAS ERP'
        Write-Host '============================'
        Write-Host ''
        Write-Host '1 - Up'
        Write-Host '2 - Down'
        Write-Host '3 - Restart'
        Write-Host '4 - Logs'
        Write-Host '5 - Status'
        Write-Host '6 - Health'
        Write-Host '7 - Rebuild'
        Write-Host '8 - Docker System Prune'
        Write-Host '9 - Shell'
        Write-Host '0 - Exit'
        Write-Host ''
        $choice = Read-Host 'Choose'
        switch ($choice) {
            '1' { Invoke-Up }
            '2' { Invoke-Down }
            '3' { Invoke-Restart }
            '4' { Invoke-Logs }
            '5' { Invoke-Ps }
            '6' { Invoke-Health }
            '7' { Invoke-Rebuild }
            '8' { Invoke-Prune }
            '9' { Invoke-Shell }
            '0' { return }
        }
        if ($choice -ne '0') { Read-Host 'Press Enter to continue' | Out-Null }
    }
}

switch ($Command) {
    'up' { Invoke-Up }
    'down' { Invoke-Down }
    'restart' { Invoke-Restart }
    'logs' { Invoke-Logs }
    'ps' { Invoke-Ps }
    'health' { Invoke-Health }
    'rebuild' { Invoke-Rebuild }
    'prune' { Invoke-Prune }
    'shell' { Invoke-Shell -Service $Service }
    'menu' { Show-Menu }
}
