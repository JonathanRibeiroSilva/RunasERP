# Script de Teste: Recuperação de Carrinho
# Uso: .\test-carrinho-recovery.ps1 [-Domain https://www.runaserp.com.br]
param([string]$Domain = "http://localhost:3000")

$domain = $Domain
$empresaSlug = "empresa-teste"  # Ajustar conforme necessário

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Teste: Recuperação de Carrinho" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Cenário 1: Criar carrinho e fazer checkout
Write-Host "Cenário 1: Criar Carrinho + Checkout" -ForegroundColor Yellow
Write-Host "--------------------" -ForegroundColor Gray

# 1.1 Obter ou criar carrinho (sem cookie)
Write-Host "1.1 Obtendo carrinho (primeira vez)..." -ForegroundColor White
$response1 = Invoke-WebRequest -Uri "$domain/api/loja/carrinho?empresa_slug=$empresaSlug" -Method GET -UseBasicParsing -SessionVariable session
$carrinho1 = $response1.Content | ConvertFrom-Json
$sessaoId = $carrinho1.sessao_id

Write-Host "  Sessão ID: $sessaoId" -ForegroundColor Green
Write-Host "  Itens no carrinho: $($carrinho1.quantidade_itens)" -ForegroundColor Green
Write-Host ""

# 1.2 Adicionar produto ao carrinho
Write-Host "1.2 Adicionando produto ao carrinho..." -ForegroundColor White
$produtoId = "produto-uuid-aqui"  # Ajustar
$body = @{
    produto_id = $produtoId
    quantidade = 2
} | ConvertTo-Json

try {
    $response2 = Invoke-WebRequest `
        -Uri "$domain/api/loja/carrinho/itens?empresa_slug=$empresaSlug" `
        -Method POST `
        -Body $body `
        -ContentType "application/json" `
        -WebSession $session `
        -UseBasicParsing
    
    $carrinho2 = $response2.Content | ConvertFrom-Json
    Write-Host "  Produto adicionado!" -ForegroundColor Green
    Write-Host "  Subtotal: R$ $($carrinho2.subtotal)" -ForegroundColor Green
} catch {
    Write-Host "  Erro ao adicionar produto: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# 1.3 Fazer checkout (criar venda)
Write-Host "1.3 Fazendo checkout..." -ForegroundColor White
$checkoutBody = @{
    cliente_novo = @{
        nome = "Cliente Teste"
        telefone = "11999999999"
        email = "teste@exemplo.com"
    }
    tipo_entrega = "RETIRADA"
    pagamentos = @(
        @{
            forma_pagamento = "PIX"
            valor_pago = $carrinho2.subtotal
        }
    )
} | ConvertTo-Json -Depth 10

try {
    $response3 = Invoke-WebRequest `
        -Uri "$domain/api/loja/checkout?empresa_slug=$empresaSlug" `
        -Method POST `
        -Body $checkoutBody `
        -ContentType "application/json" `
        -WebSession $session `
        -UseBasicParsing
    
    $checkout = $response3.Content | ConvertFrom-Json
    $numeroVenda = $checkout.numero_venda
    
    Write-Host "  Venda criada!" -ForegroundColor Green
    Write-Host "  Número: $numeroVenda" -ForegroundColor Green
    Write-Host "  Status: $($checkout.status)" -ForegroundColor Green
    Write-Host "  Link MP: $($checkout.mercadopago_init_point.Substring(0, 50))..." -ForegroundColor Green
} catch {
    Write-Host "  Erro no checkout: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Cenário 2: Simular perda de sessão
Write-Host "Cenário 2: Simular Perda de Sessão" -ForegroundColor Yellow
Write-Host "--------------------" -ForegroundColor Gray

# 2.1 Criar nova sessão (simula novo navegador)
Write-Host "2.1 Criando nova sessão (simulando novo navegador)..." -ForegroundColor White
$response4 = Invoke-WebRequest -Uri "$domain/api/loja/carrinho?empresa_slug=$empresaSlug" -Method GET -UseBasicParsing -SessionVariable session2
$carrinho3 = $response4.Content | ConvertFrom-Json
$novaSessaoId = $carrinho3.sessao_id

Write-Host "  Nova Sessão ID: $novaSessaoId" -ForegroundColor Green
Write-Host "  Itens no carrinho: $($carrinho3.quantidade_itens)" -ForegroundColor Magenta
Write-Host "  Carrinho está VAZIO (esperado)" -ForegroundColor Magenta
Write-Host ""

# Cenário 3: Verificar se endpoint de pedidos pendentes existe
Write-Host "Cenário 3: Buscar Pedidos Pendentes" -ForegroundColor Yellow
Write-Host "--------------------" -ForegroundColor Gray

Write-Host "3.1 Tentando buscar pedidos pendentes..." -ForegroundColor White
try {
    $response5 = Invoke-WebRequest `
        -Uri "$domain/api/loja/c/$empresaSlug/meus-pedidos-pendentes" `
        -Method GET `
        -WebSession $session2 `
        -UseBasicParsing
    
    $pedidos = $response5.Content | ConvertFrom-Json
    Write-Host "  Endpoint existe! Pedidos pendentes: $($pedidos.Count)" -ForegroundColor Green
    
    if ($pedidos.Count -gt 0) {
        Write-Host "  Pedido encontrado: $($pedidos[0].numero_venda)" -ForegroundColor Green
    }
} catch {
    Write-Host "  Endpoint NÃO implementado (404/405)" -ForegroundColor Red
    Write-Host "  Resposta: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Cenário 4: Verificar se endpoint de recuperação existe
Write-Host "Cenário 4: Recuperar Carrinho de Pedido" -ForegroundColor Yellow
Write-Host "--------------------" -ForegroundColor Gray

Write-Host "4.1 Tentando recuperar carrinho do pedido $numeroVenda..." -ForegroundColor White
try {
    $response6 = Invoke-WebRequest `
        -Uri "$domain/api/loja/c/$empresaSlug/pedidos/$numeroVenda/recuperar-carrinho" `
        -Method POST `
        -WebSession $session2 `
        -UseBasicParsing
    
    $carrinhoRecuperado = $response6.Content | ConvertFrom-Json
    Write-Host "  Carrinho recuperado!" -ForegroundColor Green
    Write-Host "  Itens: $($carrinhoRecuperado.quantidade_itens)" -ForegroundColor Green
    Write-Host "  Subtotal: R$ $($carrinhoRecuperado.subtotal)" -ForegroundColor Green
} catch {
    Write-Host "  Endpoint NÃO implementado (404/405)" -ForegroundColor Red
    Write-Host "  Resposta: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Cenário 5: Verificar se endpoint de retry payment existe
Write-Host "Cenário 5: Retentar Pagamento" -ForegroundColor Yellow
Write-Host "--------------------" -ForegroundColor Gray

Write-Host "5.1 Tentando retentar pagamento do pedido $numeroVenda..." -ForegroundColor White
try {
    $response7 = Invoke-WebRequest `
        -Uri "$domain/api/loja/$empresaSlug/pedidos/$numeroVenda/retry-payment" `
        -Method POST `
        -WebSession $session2 `
        -UseBasicParsing
    
    $retryResponse = $response7.Content | ConvertFrom-Json
    Write-Host "  Retry payment implementado!" -ForegroundColor Green
    Write-Host "  Novo link MP: $($retryResponse.mercadopago_init_point.Substring(0, 50))..." -ForegroundColor Green
} catch {
    Write-Host "  Endpoint NÃO implementado (404/405)" -ForegroundColor Red
    Write-Host "  Resposta: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# Resumo
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "RESUMO DOS TESTES" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Venda criada: $numeroVenda" -ForegroundColor White
Write-Host "Sessão original: $sessaoId" -ForegroundColor White
Write-Host "Nova sessão: $novaSessaoId" -ForegroundColor White
Write-Host ""
Write-Host "Endpoints testados:" -ForegroundColor White
Write-Host "  [ ] GET /c/{slug}/meus-pedidos-pendentes" -ForegroundColor Yellow
Write-Host "  [ ] POST /c/{slug}/pedidos/{numero}/recuperar-carrinho" -ForegroundColor Yellow
Write-Host "  [ ] POST /{slug}/pedidos/{numero}/retry-payment" -ForegroundColor Yellow
Write-Host ""
Write-Host "Legenda:" -ForegroundColor Gray
Write-Host "  [ ] = Não implementado" -ForegroundColor Red
Write-Host "  [✓] = Implementado e funcionando" -ForegroundColor Green
