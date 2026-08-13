<#
Usage:
  .\erp.ps1                          # interactive menu
  .\erp.ps1 up                       # everything (12 containers)
  .\erp.ps1 up vendas                # gateway + frontend + vendas + its deps
  .\erp.ps1 up vendas,estoque        # several at once
  .\erp.ps1 up clientes -NoFrontend  # backend only, skips Vite (the heaviest one)
  .\erp.ps1 up vendas -Cloudflare    # add the Cloudflare Tunnel overlay
  .\erp.ps1 down|restart|ps|health|rebuild|prune
  .\erp.ps1 logs vendas              # follow one service (or all if omitted)
  .\erp.ps1 shell erp-vendas-dev

Postgres, Redis and RabbitMQ are never listed: every service declares them under
depends_on, so compose starts them automatically.
#>
param(
    [Parameter(Position = 0)]
    [ValidateSet('up', 'down', 'restart', 'logs', 'ps', 'health', 'rebuild', 'prune', 'shell', 'menu')]
    [string]$Command = 'menu',

    [Parameter(Position = 1)]
    [string[]]$Service,

    [switch]$Cloudflare,
    [switch]$NoFrontend
)

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

$composeArgs = @('-f', 'docker-compose.dev.yml')
if ($Cloudflare) {
    $composeArgs += @('-f', 'docker-compose.cloudflare.yml', '--profile', 'proxy')
}

$MicroServices = @(
    'api-gateway', 'empresas', 'clientes', 'produtos',
    'estoque', 'vendas', 'financeiro', 'notificacoes'
)

# The gateway is the only entry point, so it is always needed.
$Core = @('api-gateway')
if (-not $NoFrontend) { $Core += 'frontend-dev' }

# Runtime service-to-service calls, taken from the *_URL vars in the compose.
# Only vendas fans out; the others talk through events, not HTTP.
$Needs = @{
    vendas = @('clientes', 'produtos', 'estoque', 'financeiro')
}

function Resolve-Services {
    param([string[]]$Wanted)

    if (-not $Wanted -or $Wanted.Count -eq 0) { return @() }   # empty = everything

    $set = New-Object 'System.Collections.Generic.HashSet[string]'
    foreach ($s in $Core) { [void]$set.Add($s) }

    foreach ($s in $Wanted) {
        $name = $s.Trim()
        if ($MicroServices -notcontains $name -and $name -ne 'frontend-dev') {
            Write-Host "Servico desconhecido: $name" -ForegroundColor Red
            Write-Host "Validos: $($MicroServices -join ', ')" -ForegroundColor Yellow
            exit 1
        }
        [void]$set.Add($name)
        if ($Needs.ContainsKey($name)) {
            foreach ($dep in $Needs[$name]) { [void]$set.Add($dep) }
        }
    }
    return @($set)
}

function Show-Target {
    param([string[]]$Svc)
    if ($Svc.Count -eq 0) {
        Write-Host 'Alvo: TUDO (12 containers)' -ForegroundColor Yellow
        return
    }
    Write-Host "Alvo: $($Svc -join ', ')  (+ db, redis, rabbitmq)" -ForegroundColor Cyan
}

function Invoke-Up {
    $svc = Resolve-Services $Service
    Show-Target $svc
    docker compose @composeArgs up -d @svc
}

function Invoke-Rebuild {
    $svc = Resolve-Services $Service
    Show-Target $svc
    docker compose @composeArgs up -d --build @svc
}

function Invoke-Restart {
    $svc = Resolve-Services $Service
    docker compose @composeArgs restart @svc
}

function Invoke-Logs {
    $svc = Resolve-Services $Service
    docker compose @composeArgs logs -f @svc
}

function Invoke-Down { docker compose @composeArgs down }
function Invoke-Ps { docker compose @composeArgs ps }
function Invoke-Prune { docker system prune -f }

function Invoke-Health {
    docker ps --format "table {{.Names}}`t{{.Status}}"
    Write-Host ''
    Write-Host 'Consumo (Ctrl+C para sair):' -ForegroundColor Cyan
    docker stats --no-stream --format "table {{.Name}}`t{{.CPUPerc}}`t{{.MemUsage}}"
}

function Invoke-Shell {
    param([string[]]$Service)
    $target = ''
    if ($Service -and $Service.Count -gt 0) { $target = $Service[0] }
    if (-not $target) { $target = Read-Host 'Container name' }
    docker exec -it $target sh
}

function Select-Services {
    Write-Host ''
    for ($i = 0; $i -lt $MicroServices.Count; $i++) {
        Write-Host ("  {0} - {1}" -f ($i + 1), $MicroServices[$i])
    }
    Write-Host ''
    $pick = Read-Host 'Numeros separados por virgula (enter = tudo)'
    if (-not $pick) { return @() }

    $chosen = @()
    foreach ($n in $pick -split ',') {
        $idx = 0
        if ([int]::TryParse($n.Trim(), [ref]$idx) -and $idx -ge 1 -and $idx -le $MicroServices.Count) {
            $chosen += $MicroServices[$idx - 1]
        }
    }
    return $chosen
}

function Show-Menu {
    while ($true) {
        Clear-Host
        Write-Host '============================'
        Write-Host '     RUNAS ERP'
        Write-Host '============================'
        Write-Host ''
        Write-Host '1 - Up (tudo)'
        Write-Host '2 - Up (escolher microsservicos)'
        Write-Host '3 - Down'
        Write-Host '4 - Restart'
        Write-Host '5 - Logs'
        Write-Host '6 - Status'
        Write-Host '7 - Health + consumo'
        Write-Host '8 - Rebuild'
        Write-Host '9 - Docker System Prune'
        Write-Host 'S - Shell'
        Write-Host '0 - Exit'
        Write-Host ''
        $choice = Read-Host 'Choose'
        switch ($choice) {
            '1' { $script:Service = @(); Invoke-Up }
            '2' { $script:Service = Select-Services; Invoke-Up }
            '3' { Invoke-Down }
            '4' { Invoke-Restart }
            '5' { Invoke-Logs }
            '6' { Invoke-Ps }
            '7' { Invoke-Health }
            '8' { Invoke-Rebuild }
            '9' { Invoke-Prune }
            'S' { Invoke-Shell }
            's' { Invoke-Shell }
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
