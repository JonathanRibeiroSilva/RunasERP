# Exemplos Práticos - Runas API

> **Casos de uso reais** com exemplos completos de código

---

## 🎯 Cenários Comuns

### 1. Cadastrar Cliente Completo

```bash
#!/bin/bash
TOKEN="seu_token_aqui"
BASE_URL="http://localhost:8000"

# 1. Criar cliente
CLIENTE_ID=$(curl -s -X POST "$BASE_URL/clientes" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "cpf": "12345678909",
    "nome": "João Silva",
    "telefone": "+5511999999999",
    "email": "joao@email.com",
    "limite_credito": 1000.00,
    "dia_vencimento": 10
  }' | jq -r '.id')

echo "Cliente criado: $CLIENTE_ID"

# 2. Adicionar endereço
curl -s -X POST "$BASE_URL/clientes/$CLIENTE_ID/enderecos" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "cep": "01310-100",
    "logradouro": "Av. Paulista",
    "numero": "1000",
    "bairro": "Bela Vista",
    "cidade": "São Paulo",
    "uf": "SP",
    "principal": true
  }'

echo "Endereço adicionado!"
```

---

### 2. Criar Produto com Variantes

```python
import requests

TOKEN = "seu_token_aqui"
BASE_URL = "http://localhost:8000"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# 1. Criar categoria
categoria = requests.post(
    f"{BASE_URL}/categorias",
    headers=headers,
    json={"nome": "Bebidas", "descricao": "Bebidas em geral"}
).json()

# 2. Criar produto
produto = requests.post(
    f"{BASE_URL}/produtos",
    headers=headers,
    json={
        "categoria_id": categoria["id"],
        "nome": "Coca-Cola",
        "descricao": "Refrigerante"
    }
).json()

# 3. Adicionar variantes
variantes = [
    {"tamanho": "2L", "preco_custo": 5.00, "markup": 40},
    {"tamanho": "1L", "preco_custo": 3.00, "markup": 45},
    {"tamanho": "600ml", "preco_custo": 2.00, "markup": 50}
]

for v in variantes:
    requests.post(
        f"{BASE_URL}/produtos/{produto['id']}/variantes",
        headers=headers,
        json={
            "sku": f"COCA-{v['tamanho']}",
            "preco_custo": v["preco_custo"],
            "markup_pct": v["markup"],
            "atributos": [{"chave": "tamanho", "valor": v["tamanho"]}]
        }
    )

print(f"Produto criado com 3 variantes!")
```

---

### 3. Fluxo Completo de Venda

```typescript
// Frontend - Fluxo de compra no catálogo

class CheckoutFlow {
  private carrinhoToken: string;

  // 1. Criar carrinho
  async criarCarrinho() {
    const response = await fetch('http://localhost:8000/carrinho', {
      method: 'POST'
    });
    const data = await response.json();
    this.carrinhoToken = data.token;
    return data;
  }

  // 2. Adicionar produtos
  async adicionarProduto(varianteId: string, quantidade: number) {
    await fetch(`http://localhost:8000/carrinho/${this.carrinhoToken}/itens`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        variante_id: varianteId,
        quantidade: quantidade
      })
    });
  }

  // 3. Finalizar compra
  async finalizarCompra(dados: CheckoutData) {
    const response = await fetch(
      `http://localhost:8000/carrinho/${this.carrinhoToken}/checkout`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          nome_comprador: dados.nome,
          telefone_comprador: dados.telefone,
          modalidade_pagto: 'A_VISTA',
          modalidade_entrega: 'ENTREGA',
          metodo: 'PIX',
          endereco_entrega: dados.endereco
        })
      }
    );

    const pedido = await response.json();
    
    // Se PIX, mostrar QR Code
    if (pedido.pagamento.qr_code) {
      this.mostrarQRCode(pedido.pagamento.qr_code_base64);
    }

    return pedido;
  }

  mostrarQRCode(base64: string) {
    const img = document.createElement('img');
    img.src = `data:image/png;base64,${base64}`;
    document.body.appendChild(img);
  }
}

// Uso
const checkout = new CheckoutFlow();
await checkout.criarCarrinho();
await checkout.adicionarProduto('uuid-variante', 2);
await checkout.finalizarCompra({
  nome: 'João Silva',
  telefone: '+5511999999999',
  endereco: {
    logradouro: 'Av. Paulista',
    numero: '1000',
    bairro: 'Bela Vista',
    cidade: 'São Paulo',
    uf: 'SP',
    cep: '01310-100'
  }
});
```

---

### 4. Gestão de Estoque

```python
# Script para receber mercadoria do fornecedor

import requests
from typing import List, Dict

TOKEN = "seu_token_aqui"
BASE_URL = "http://localhost:8000"

def receber_mercadoria(nota_fiscal: str, itens: List[Dict]):
    """
    Registra entrada de mercadoria no estoque
    
    Args:
        nota_fiscal: Número da nota fiscal
        itens: Lista de dicts com variante_id e quantidade
    """
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    
    for item in itens:
        response = requests.post(
            f"{BASE_URL}/estoque/{item['variante_id']}/entrada",
            headers=headers,
            json={
                "quantidade": item["quantidade"],
                "motivo": f"NF {nota_fiscal}",
                "referencia_id": nota_fiscal
            }
        )
        
        if response.status_code == 201:
            print(f"✅ {item['sku']}: +{item['quantidade']} unidades")
        else:
            print(f"❌ Erro ao registrar {item['sku']}: {response.text}")

# Uso
receber_mercadoria("NF-12345", [
    {"variante_id": "uuid-1", "sku": "COCA-2L", "quantidade": 100},
    {"variante_id": "uuid-2", "sku": "COCA-1L", "quantidade": 150},
    {"variante_id": "uuid-3", "sku": "COCA-600ML", "quantidade": 200}
])
```

---

### 5. Relatório de Vendas

```python
# Gerar relatório de vendas do mês

import requests
from datetime import datetime, timedelta
import pandas as pd

TOKEN = "seu_token_aqui"
BASE_URL = "http://localhost:8000"

def relatorio_vendas_mes():
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    # Buscar pedidos do mês
    hoje = datetime.now()
    primeiro_dia = hoje.replace(day=1)
    
    pedidos = []
    page = 1
    
    while True:
        response = requests.get(
            f"{BASE_URL}/pedidos",
            headers=headers,
            params={
                "page": page,
                "size": 100,
                "data_inicio": primeiro_dia.isoformat(),
                "data_fim": hoje.isoformat()
            }
        )
        
        data = response.json()
        pedidos.extend(data["items"])
        
        if page >= data["pages"]:
            break
        page += 1
    
    # Criar DataFrame
    df = pd.DataFrame(pedidos)
    
    # Análises
    print(f"📊 Relatório de Vendas - {hoje.strftime('%B/%Y')}")
    print(f"Total de pedidos: {len(df)}")
    print(f"Valor total: R$ {df['total'].sum():.2f}")
    print(f"Ticket médio: R$ {df['total'].mean():.2f}")
    print(f"\nPor status:")
    print(df.groupby('status')['total'].agg(['count', 'sum']))
    
    # Exportar para Excel
    df.to_excel(f"vendas_{hoje.strftime('%Y%m')}.xlsx", index=False)
    print(f"\n✅ Relatório exportado: vendas_{hoje.strftime('%Y%m')}.xlsx")

relatorio_vendas_mes()
```

---

### 6. Cobrança Automática

```python
# Script para enviar lembretes de cobrança

import requests
from datetime import datetime, timedelta

TOKEN = "seu_token_aqui"
BASE_URL = "http://localhost:8000"

def enviar_lembretes_cobranca():
    """
    Busca contas que vencem em 3 dias e envia lembretes
    """
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    # Buscar contas a vencer
    tres_dias = (datetime.now() + timedelta(days=3)).date()
    
    response = requests.get(
        f"{BASE_URL}/contas/vencer",
        headers=headers,
        params={"dias": 3}
    )
    
    contas = response.json()
    
    print(f"📧 Enviando {len(contas)} lembretes de cobrança...")
    
    for conta in contas:
        # Buscar dados do cliente
        cliente = requests.get(
            f"{BASE_URL}/clientes/{conta['cliente_id']}",
            headers=headers
        ).json()
        
        print(f"  → {cliente['nome']}: R$ {conta['saldo_devedor']:.2f}")
        
        # O sistema já envia WhatsApp automaticamente via evento
        # Este script é apenas para monitoramento
    
    print("✅ Lembretes processados!")

enviar_lembretes_cobranca()
```

---

### 7. Integração com Sistema Externo

```javascript
// Webhook para receber notificações do Mercado Pago

const express = require('express');
const crypto = require('crypto');

const app = express();
app.use(express.json());

// Webhook do Mercado Pago
app.post('/webhooks/mercadopago', async (req, res) => {
  // 1. Validar assinatura
  const signature = req.headers['x-signature'];
  const secret = process.env.MP_WEBHOOK_SECRET;
  
  const hash = crypto
    .createHmac('sha256', secret)
    .update(JSON.stringify(req.body))
    .digest('hex');
  
  if (hash !== signature) {
    return res.status(401).json({ error: 'Invalid signature' });
  }
  
  // 2. Processar evento
  const { type, data } = req.body;
  
  if (type === 'payment') {
    // Consultar status do pagamento
    const payment = await fetch(
      `https://api.mercadopago.com/v1/payments/${data.id}`,
      {
        headers: {
          'Authorization': `Bearer ${process.env.MP_ACCESS_TOKEN}`
        }
      }
    ).then(r => r.json());
    
    // Atualizar pedido no Runas
    if (payment.status === 'approved') {
      await fetch(`http://localhost:8000/pagamentos/${payment.external_reference}/confirmar`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${process.env.RUNAS_TOKEN}`,
          'Content-Type': 'application/json'
        },
        json: {
          mp_payment_id: payment.id
        }
      });
      
      console.log(`✅ Pagamento confirmado: ${payment.external_reference}`);
    }
  }
  
  res.status(200).json({ ok: true });
});

app.listen(3000, () => {
  console.log('Webhook server running on port 3000');
});
```

---

## 📚 Coleções Postman

### Importar Coleção

1. Baixe a coleção: [runas-api.postman_collection.json](./postman/runas-api.postman_collection.json)
2. Abra o Postman
3. File → Import → Selecione o arquivo
4. Configure as variáveis de ambiente

### Variáveis de Ambiente

```json
{
  "base_url": "http://localhost:8000",
  "access_token": "",
  "refresh_token": ""
}
```

---

## 🔧 Scripts Úteis

### Backup de Dados

```bash
#!/bin/bash
# backup.sh - Exportar dados via API

TOKEN="seu_token_aqui"
BASE_URL="http://localhost:8000"
DATA=$(date +%Y%m%d)

# Exportar clientes
curl -s -X GET "$BASE_URL/clientes?size=1000" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.items' > "backup_clientes_$DATA.json"

# Exportar produtos
curl -s -X GET "$BASE_URL/produtos?size=1000" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.items' > "backup_produtos_$DATA.json"

echo "✅ Backup concluído: $DATA"
```

---

## 📚 Documentação Relacionada

- [Guia de Autenticação](./guia-autenticacao.md)
- [API de Clientes](./clientes-api.md)
- [API de Produtos](./produtos-api.md)
- [OpenAPI Specification](./openapi.yaml)

---

**Projeto:** Runas  
**Equipe:** Equipe DenebCorp  
**Data:** 26 de Maio de 2026  
**Versão:** 1.0.0
