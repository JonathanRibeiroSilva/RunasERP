<#
.SYNOPSIS
Wrapper inteligente para Graphify com filtros

.EXAMPLE
.\graphify-smart.ps1 query "webhook payment" -Layer backend
.\graphify-smart.ps1 explain "MercadoPagoService"
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true, Position=0)]
    [ValidateSet("query", "path", "explain")]
    [string]$Command,
    
    [Parameter(Mandatory=$true, Position=1)]
    [string]$Query,
    
    [Parameter(Position=2)]
    [string]$Target = "",
    
    [ValidateSet("backend", "frontend", "docs", "services", "routers", "all")]
    [string]$Layer = "all",
    
    [string[]]$Exclude = @(),
    
    [switch]$CodeOnly
)

# Keywords para expandir queries
$KeywordMap = @{
    "mercadopago" = "MercadoPagoService mercadopago_service criar_preferencia processar_webhook_payment"
    "webhook" = "webhook_mercadopago MercadoPagoService.processar_webhook_payment"
    "carrinho" = "CarrinhoService carrinho_service limpar_carrinho adicionar_item"
    "checkout" = "LojaService.processar_checkout CheckoutPage loja_service"
    "pagamento" = "MercadoPagoService PagamentoVenda ConfiguracaoPagamento"
}

# Expandir query com keywords
$EnhancedQuery = $Query
foreach ($key in $KeywordMap.Keys) {
    if ($Query -match $key) {
        $EnhancedQuery = "$Query $($KeywordMap[$key])"
        break
    }
}

Write-Host "Graphify Smart Query" -ForegroundColor Green
Write-Host "Command: $Command | Query: $Query" -ForegroundColor Cyan
if ($Layer -ne "all") { Write-Host "Layer Filter: $Layer" -ForegroundColor Yellow }
Write-Host ""

# Executar graphify
switch ($Command) {
    "query" {
        $output = graphify query $EnhancedQuery 2>&1 | Out-String
    }
    "path" {
        if ([string]::IsNullOrEmpty($Target)) {
            Write-Host "Erro: comando 'path' requer dois argumentos" -ForegroundColor Red
            exit 1
        }
        $output = graphify path $Query $Target 2>&1 | Out-String
    }
    "explain" {
        $output = graphify explain $Query 2>&1 | Out-String
    }
}

# Filtrar resultados
if ($Command -eq "query") {
    $lines = $output -split "`n"
    $backendNodes = @()
    $frontendNodes = @()
    $docNodes = @()
    $otherLines = @()
    
    foreach ($line in $lines) {
        # Filtrar nodes backend Python
        if ($line -match "^NODE .*services/.*\.py") {
            $include = $true
            
            # Aplicar filtros
            if ($Layer -eq "backend" -or $Layer -eq "services" -or $Layer -eq "all") {
                if ($Layer -eq "services" -and $line -notmatch "services/[^/]+/services/") {
                    $include = $false
                }
                foreach ($ex in $Exclude) {
                    if ($line -match $ex) { $include = $false; break }
                }
                if ($include) { $backendNodes += $line }
            }
        }
        # Filtrar nodes frontend
        elseif ($line -match "^NODE .*frontend/") {
            if ($Layer -eq "frontend" -or $Layer -eq "all") {
                if (-not $CodeOnly) { $frontendNodes += $line }
            }
        }
        # Filtrar docs
        elseif ($line -match "^NODE .*\.md") {
            if ($Layer -eq "docs" -or ($Layer -eq "all" -and -not $CodeOnly)) {
                $docNodes += $line
            }
        }
        # Outras linhas (header, edges, etc)
        else {
            $otherLines += $line
        }
    }
    
    # Reorganizar: backend primeiro
    $output = ""
    $output += ($otherLines -join "`n") + "`n`n"
    
    if ($backendNodes.Count -gt 0) {
        $output += "--- BACKEND (Python Services) ---`n"
        $output += ($backendNodes -join "`n") + "`n`n"
    }
    
    if ($frontendNodes.Count -gt 0) {
        $output += "--- FRONTEND (React/TypeScript) ---`n"
        $output += ($frontendNodes -join "`n") + "`n`n"
    }
    
    if ($docNodes.Count -gt 0) {
        $output += "--- DOCUMENTACAO ---`n"
        $output += ($docNodes -join "`n") + "`n"
    }
    
    $totalNodes = $backendNodes.Count + $frontendNodes.Count + $docNodes.Count
    Write-Host $output
    Write-Host "`nResultados: $totalNodes nodes encontrados" -ForegroundColor Green
} else {
    Write-Host $output
}
