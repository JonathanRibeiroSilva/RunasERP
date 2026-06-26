# ============================================
# Deploy do Runas ERP em Produção
# ============================================
# Este script automatiza o processo de deploy
# do sistema ERP com SSL/HTTPS em produção
# ============================================

param(
    [switch]$SkipSSL,
    [switch]$SkipBackup,
    [switch]$SkipMigrations,
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"

# Cores para output
function Write-Info { Write-Host "ℹ️  $args" -ForegroundColor Cyan }
function Write-Success { Write-Host "✅ $args" -ForegroundColor Green }
function Write-Error { Write-Host "❌ $args" -ForegroundColor Red }
function Write-Warning { Write-Host "⚠️  $args" -ForegroundColor Yellow }

# Banner
Write-Host @"

╔════════════════════════════════════════╗
║   Runas ERP - Deploy em Produção      ║
║   Domínio: runaserp.com.br            ║
╚════════════════════════════════════════╝

"@ -ForegroundColor Magenta

# ============================================
# 1. Verificações Pré-Deploy
# ============================================
Write-Info "Verificando pré-requisitos..."

# Verificar se Docker está rodando
try {
    docker ps | Out-Null
    Write-Success "Docker está rodando"
} catch {
    Write-Error "Docker não está rodando. Inicie o Docker Desktop e tente novamente."
    exit 1
}

# Verificar se .env existe
if (-not (Test-Path ".env")) {
    Write-Error "Arquivo .env não encontrado. Copie .env.example e configure as variáveis."
    exit 1
}
Write-Success "Arquivo .env encontrado"

# Verificar se network existe
$networkExists = docker network ls | Select-String "runaserp_erp-network"
if (-not $networkExists) {
    Write-Info "Criando network Docker..."
    docker network create runaserp_erp-network
    Write-Success "Network criada"
} else {
    Write-Success "Network já existe"
}

# ============================================
# 2. Gerar Certificado SSL (Opcional)
# ============================================
if (-not $SkipSSL) {
    Write-Info "Verificando certificado SSL..."
    
    $certsVolumeExists = docker volume ls | Select-String "letsencrypt-certs"
    
    if (-not $certsVolumeExists) {
        Write-Warning "Certificado SSL não encontrado."
        Write-Info "Para gerar o certificado SSL, execute:"
        Write-Host @"

docker volume create letsencrypt-certs
docker volume create letsencrypt-www

docker run --rm `
  -v letsencrypt-certs:/etc/letsencrypt `
  -v letsencrypt-www:/var/www/certbot `
  -p 80:80 -p 443:443 `
  certbot/certbot certonly --standalone `
  -d runaserp.com.br `
  -d www.runaserp.com.br `
  --email seu-email@example.com `
  --agree-tos `
  --non-interactive

"@ -ForegroundColor Yellow
        
        $continue = Read-Host "Deseja continuar sem SSL? (s/N)"
        if ($continue -ne "s" -and $continue -ne "S") {
            Write-Info "Deploy cancelado. Configure o SSL e execute novamente."
            exit 0
        }
    } else {
        Write-Success "Certificado SSL encontrado"
    }
} else {
    Write-Warning "Verificação de SSL ignorada (--SkipSSL)"
}

# ============================================
# 3. Backup do Banco de Dados
# ============================================
if (-not $SkipBackup) {
    Write-Info "Fazendo backup do banco de dados..."
    
    $dbRunning = docker ps | Select-String "erp-db"
    if ($dbRunning) {
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $backupFile = "backup_$timestamp.sql"
        
        try {
            docker exec erp-db pg_dump -U erp -d erp > $backupFile
            Write-Success "Backup salvo em: $backupFile"
        } catch {
            Write-Warning "Não foi possível fazer backup. Continuando..."
        }
    } else {
        Write-Warning "Container do banco não está rodando. Pulando backup."
    }
} else {
    Write-Warning "Backup ignorado (--SkipBackup)"
}

# ============================================
# 4. Parar Containers de Desenvolvimento
# ============================================
Write-Info "Parando containers de desenvolvimento..."

try {
    docker-compose -f docker-compose.dev.yml down
    Write-Success "Containers de desenvolvimento parados"
} catch {
    Write-Warning "Não havia containers de desenvolvimento rodando"
}

# ============================================
# 5. Build das Imagens de Produção
# ============================================
Write-Info "Buildando imagens de produção..."

if ($Verbose) {
    docker-compose -f docker-compose.prod.yml build --no-cache
} else {
    docker-compose -f docker-compose.prod.yml build --no-cache --quiet
}

if ($LASTEXITCODE -ne 0) {
    Write-Error "Erro ao buildar imagens. Verifique os logs."
    exit 1
}
Write-Success "Imagens buildadas com sucesso"

# ============================================
# 6. Subir Serviços de Produção
# ============================================
Write-Info "Subindo serviços de produção..."

docker-compose -f docker-compose.prod.yml up -d

if ($LASTEXITCODE -ne 0) {
    Write-Error "Erro ao subir serviços. Verifique os logs."
    exit 1
}
Write-Success "Serviços em produção rodando"

# Aguardar containers iniciarem
Write-Info "Aguardando containers iniciarem (30s)..."
Start-Sleep -Seconds 30

# ============================================
# 7. Executar Migrations
# ============================================
if (-not $SkipMigrations) {
    Write-Info "Executando migrations..."
    
    $services = @(
        "erp-api-gateway-prod",
        "erp-empresas-prod",
        "erp-clientes-prod",
        "erp-produtos-prod",
        "erp-estoque-prod",
        "erp-vendas-prod",
        "erp-financeiro-prod",
        "erp-notificacoes-prod"
    )
    
    foreach ($service in $services) {
        Write-Info "Migration: $service"
        try {
            docker exec -it $service alembic upgrade head
            Write-Success "Migration concluída: $service"
        } catch {
            Write-Warning "Erro na migration de $service. Continuando..."
        }
    }
} else {
    Write-Warning "Migrations ignoradas (--SkipMigrations)"
}

# ============================================
# 8. Criar Usuário Admin
# ============================================
Write-Info "Criando usuário administrador..."

try {
    docker exec -it erp-api-gateway-prod python seed.py
    Write-Success "Usuário admin criado"
} catch {
    Write-Warning "Não foi possível criar usuário admin. Pode já existir."
}

# ============================================
# 9. Verificar Saúde dos Containers
# ============================================
Write-Info "Verificando saúde dos containers..."

docker-compose -f docker-compose.prod.yml ps

$unhealthy = docker ps --filter "health=unhealthy" --format "{{.Names}}"
if ($unhealthy) {
    Write-Warning "Containers com problemas de saúde:"
    Write-Host $unhealthy -ForegroundColor Yellow
} else {
    Write-Success "Todos os containers saudáveis"
}

# ============================================
# 10. Testes de Verificação
# ============================================
Write-Info "Executando testes de verificação..."

# Teste 1: Health endpoint
Write-Info "Testando endpoint de saúde..."
try {
    $response = Invoke-WebRequest -Uri "http://localhost/api/health" -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Success "API Health OK (HTTP)"
    }
} catch {
    Write-Warning "API Health não respondeu via HTTP"
}

# Teste 2: HTTPS (se certificado existe)
if (-not $SkipSSL) {
    try {
        $response = Invoke-WebRequest -Uri "https://localhost/api/health" -UseBasicParsing -SkipCertificateCheck
        if ($response.StatusCode -eq 200) {
            Write-Success "API Health OK (HTTPS)"
        }
    } catch {
        Write-Warning "API Health não respondeu via HTTPS. Verifique o certificado SSL."
    }
}

# ============================================
# Resumo Final
# ============================================
Write-Host @"

╔════════════════════════════════════════╗
║         DEPLOY CONCLUÍDO! 🚀          ║
╚════════════════════════════════════════╝

"@ -ForegroundColor Green

Write-Info "Próximos passos:"
Write-Host @"

1. Verificar logs dos serviços:
   docker-compose -f docker-compose.prod.yml logs -f

2. Testar aplicação:
   - HTTP:  http://runaserp.com.br
   - HTTPS: https://runaserp.com.br

3. Atualizar OAuth2 Redirect URIs:
   - Google: https://console.cloud.google.com/apis/credentials
   - Microsoft: https://portal.azure.com

4. Configurar Webhooks do Mercado Pago:
   URL: https://runaserp.com.br/api/vendas/webhook/mercadopago

5. Configurar monitoring:
   - UptimeRobot: https://uptimerobot.com
   - SSL Labs: https://www.ssllabs.com/ssltest/

"@ -ForegroundColor Cyan

Write-Success "Deploy finalizado com sucesso!"
