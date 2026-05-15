#!/bin/bash

# Script para corrigir problemas do MVP
# Data: 2026-05-14

echo "🔧 Corrigindo problemas do MVP..."
echo ""

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para verificar se comando foi bem-sucedido
check_status() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ $1${NC}"
    else
        echo -e "${RED}✗ $1${NC}"
        exit 1
    fi
}

echo "📋 Passo 1: Parando containers..."
docker-compose down
check_status "Containers parados"

echo ""
echo "🔨 Passo 2: Rebuild do API Gateway..."
docker-compose build api-gateway
check_status "API Gateway reconstruído"

echo ""
echo "🚀 Passo 3: Subindo todos os serviços..."
docker-compose up -d
check_status "Serviços iniciados"

echo ""
echo "⏳ Passo 4: Aguardando inicialização (30 segundos)..."
sleep 30
echo -e "${GREEN}✓ Aguardado${NC}"

echo ""
echo "🔍 Passo 5: Verificando status dos containers..."
docker-compose ps

echo ""
echo "📊 Passo 6: Verificando seed do admin..."
docker logs erp-api-gateway 2>&1 | grep "seed.admin"

echo ""
echo "🧪 Passo 7: Testando health checks..."

# API Gateway
echo -n "  - API Gateway: "
HEALTH=$(curl -s http://localhost:8000/health)
if [[ $HEALTH == *"healthy"* ]]; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${RED}✗ FALHOU${NC}"
fi

# Clientes
echo -n "  - Clientes: "
HEALTH=$(curl -s http://localhost:8001/health)
if [[ $HEALTH == *"healthy"* ]]; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${RED}✗ FALHOU${NC}"
fi

# Produtos
echo -n "  - Produtos: "
HEALTH=$(curl -s http://localhost:8002/health)
if [[ $HEALTH == *"healthy"* ]]; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${RED}✗ FALHOU${NC}"
fi

echo ""
echo "🔐 Passo 8: Testando login..."
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@runas.com&password=Admin@123")

if [[ $LOGIN_RESPONSE == *"access_token"* ]]; then
    echo -e "${GREEN}✓ Login funcionando!${NC}"
    echo ""
    echo "📝 Token de acesso:"
    echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4 | head -c 50
    echo "..."
else
    echo -e "${RED}✗ Login falhou!${NC}"
    echo "Resposta: $LOGIN_RESPONSE"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ Correções aplicadas!"
echo ""
echo "📋 Próximos passos:"
echo "  1. Execute: bash test-mvp.sh"
echo "  2. Consulte: docs/mvp/CHECKLIST-VALIDACAO.md"
echo "  3. Acesse: http://localhost:8000/docs"
echo ""
echo "🔗 URLs úteis:"
echo "  - API Gateway: http://localhost:8000"
echo "  - Swagger UI: http://localhost:8000/docs"
echo "  - pgAdmin: http://localhost:5050"
echo "  - RabbitMQ: http://localhost:15672"
echo ""
echo "🔐 Credenciais:"
echo "  - Admin: admin@runas.com / Admin@123"
echo "  - pgAdmin: admin@runas.com / admin123"
echo "  - RabbitMQ: guest / guest"
echo ""
