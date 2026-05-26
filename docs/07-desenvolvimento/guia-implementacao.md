# Guia de Implementação - ERP Runas MVP

Guia passo a passo para implementar cada componente do ERP Runas.

## 📋 Índice

1. [Preparação do Ambiente](#1-preparação-do-ambiente)
2. [Implementação do API Gateway](#2-implementação-do-api-gateway)
3. [Implementação dos Microsserviços](#3-implementação-dos-microsserviços)
4. [Integrações Externas](#4-integrações-externas)
5. [Testes](#5-testes)
6. [Deploy](#6-deploy)

---

## 1. Preparação do Ambiente

### 1.1 Pré-requisitos

```bash
# Verificar versões
python --version  # 3.12+
docker --version  # 20.10+
docker-compose --version  # 2.0+
make --version
```

### 1.2 Configuração Inicial

```bash
# 1. Clonar repositório
git clone <repo-url>
cd erp-runas

# 2. Configurar variáveis de ambiente
cp .env.example .env

# 3. Gerar SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Copiar output para SECRET_KEY no .env

# 4. Configurar credenciais do Mercado Pago (sandbox)
# Obter em: https://www.mercadopago.com.br/developers/panel/credentials
# Adicionar no .env:
# MP_ACCESS_TOKEN=TEST-...
# MP_PUBLIC_KEY=TEST-...
# MP_WEBHOOK_SECRET=...

# 5. Configurar Evolution API
# Seguir instruções em docs/EVOLUTION-API-SETUP.md
```

### 1.3 Subir Infraestrutura

```bash
# Subir apenas infraestrutura para desenvolvimento
make dev

# Verificar se tudo está rodando
docker-compose ps

# Acessar pgAdmin
# http://localhost:5050
# Login: admin@runas.local / admin123
```

---

## 2. Implementação do API Gateway

### 2.1 Estrutura Já Criada

A estrutura base já foi gerada. Agora implemente:

### 2.2 Seed de Usuário Admin

Criar `api-gateway/seed.py`:

```python
"""Seed de usuário admin."""
import asyncio
from database import AsyncSessionLocal
from repositories.usuario_repository import UsuarioRepository
from schemas.usuario import UsuarioCreate
from models.usuario import RoleEnum
import os


async def seed_admin():
    """Cria usuário admin padrão."""
    async with AsyncSessionLocal() as session:
        repo = UsuarioRepository(session)
        
        # Verificar se admin já existe
        admin = await repo.buscar_por_email(os.getenv("ADMIN_EMAIL", "admin@runas.com"))
        
        if not admin:
            admin_data = UsuarioCreate(
                nome=os.getenv("ADMIN_NAME", "Administrador"),
                email=os.getenv("ADMIN_EMAIL", "admin@runas.com"),
                senha=os.getenv("ADMIN_PASSWORD", "Admin@123"),
                role=RoleEnum.ADMIN
            )
            
            admin = await repo.criar(admin_data)
            print(f"✓ Admin criado: {admin.email}")
        else:
            print(f"✓ Admin já existe: {admin.email}")


if __name__ == "__main__":
    asyncio.run(seed_admin())
```

### 2.3 Testar API Gateway

```bash
# 1. Subir o gateway
docker-compose up -d api-gateway

# 2. Executar migrations
docker-compose exec api-gateway alembic upgrade head

# 3. Criar usuário admin
docker-compose exec api-gateway python seed.py

# 4. Testar login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@runas.com&password=Admin@123"

# Deve retornar access_token e refresh_token
```

---

## 3. Implementação dos Microsserviços

### 3.1 Ordem de Implementação Recomendada

1. **Clientes** (base para outros serviços)
2. **Produtos** (necessário para estoque e vendas)
3. **Estoque** (necessário para vendas)
4. **Vendas** (core do negócio)
5. **Financeiro** (depende de vendas)
6. **Notificações** (consome eventos dos outros)

---

### 3.2 Serviço de Clientes

#### 3.2.1 Implementar Modelos

Criar `services/clientes/models/cliente.py`:

```python
"""Modelos de Cliente e Endereco."""
from datetime import datetime
from decimal import Decimal
from uuid import uuid4
from sqlalchemy import Boolean, Date, DateTime, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class Cliente(Base):
    """Modelo de Cliente."""
    
    __tablename__ = "clientes"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    cpf: Mapped[str] = mapped_column(String(11), unique=True, nullable=False, index=True)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    telefone: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255))
    data_nasc: Mapped[datetime | None] = mapped_column(Date)
    limite_credito: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
    credito_disponivel: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
    dia_vencimento: Mapped[int | None] = mapped_column(Integer)
    bloqueado: Mapped[bool] = mapped_column(Boolean, default=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    enderecos: Mapped[list["Endereco"]] = relationship(
        "Endereco",
        back_populates="cliente",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Cliente(id={self.id}, nome={self.nome}, cpf={self.cpf})>"


class Endereco(Base):
    """Modelo de Endereço."""
    
    __tablename__ = "enderecos"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    cliente_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("clientes.id", ondelete="CASCADE"))
    cep: Mapped[str] = mapped_column(String(8), nullable=False)
    logradouro: Mapped[str] = mapped_column(String(255), nullable=False)
    numero: Mapped[str] = mapped_column(String(20), nullable=False)
    complemento: Mapped[str | None] = mapped_column(String(255))
    bairro: Mapped[str] = mapped_column(String(100), nullable=False)
    cidade: Mapped[str] = mapped_column(String(100), nullable=False)
    uf: Mapped[str] = mapped_column(String(2), nullable=False)
    principal: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relacionamentos
    cliente: Mapped["Cliente"] = relationship("Cliente", back_populates="enderecos")
    
    def __repr__(self) -> str:
        return f"<Endereco(id={self.id}, cliente_id={self.cliente_id})>"
```

#### 3.2.2 Implementar Validações

Criar `services/clientes/utils/validators.py`:

```python
"""Validadores de CPF e telefone."""
from validate_docbr import CPF
import re


cpf_validator = CPF()


def validar_cpf(cpf: str) -> bool:
    """
    Valida CPF usando algoritmo dos dígitos verificadores.
    
    Args:
        cpf: CPF com ou sem formatação
        
    Returns:
        True se válido, False caso contrário
    """
    return cpf_validator.validate(cpf)


def normalizar_cpf(cpf: str) -> str:
    """
    Remove formatação do CPF.
    
    Args:
        cpf: CPF formatado
        
    Returns:
        CPF apenas com números
    """
    return re.sub(r'\D', '', cpf)


def validar_telefone_e164(telefone: str) -> bool:
    """
    Valida se telefone está no formato E.164.
    
    Args:
        telefone: Telefone a validar
        
    Returns:
        True se válido
    """
    pattern = r'^\+[1-9]\d{1,14}$'
    return bool(re.match(pattern, telefone))


def normalizar_telefone(telefone: str) -> str:
    """
    Normaliza telefone para formato E.164.
    
    Args:
        telefone: Telefone em qualquer formato
        
    Returns:
        Telefone no formato E.164
        
    Raises:
        ValueError: Se não conseguir normalizar
    """
    # Remove tudo que não é número
    apenas_numeros = re.sub(r'\D', '', telefone)
    
    # Se começa com 0, remove
    if apenas_numeros.startswith('0'):
        apenas_numeros = apenas_numeros[1:]
    
    # Se não começa com código do país, adiciona +55 (Brasil)
    if not telefone.startswith('+'):
        if len(apenas_numeros) == 11:  # DDD + 9 dígitos
            return f"+55{apenas_numeros}"
        elif len(apenas_numeros) == 10:  # DDD + 8 dígitos
            return f"+55{apenas_numeros}"
    
    # Se já tem +, valida
    if validar_telefone_e164(telefone):
        return telefone
    
    raise ValueError(f"Não foi possível normalizar o telefone: {telefone}")
```

#### 3.2.3 Implementar Schemas

Criar `services/clientes/schemas/cliente.py`:

```python
"""Schemas Pydantic para Cliente."""
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field, field_validator
from utils.validators import validar_cpf, normalizar_cpf, normalizar_telefone


class ClienteBase(BaseModel):
    """Schema base de cliente."""
    nome: str = Field(..., min_length=3, max_length=255)
    cpf: str = Field(..., min_length=11, max_length=14)
    telefone: str
    email: str | None = None
    data_nasc: date | None = None
    
    @field_validator('cpf')
    @classmethod
    def validate_cpf(cls, v: str) -> str:
        """Valida e normaliza CPF."""
        cpf_limpo = normalizar_cpf(v)
        if not validar_cpf(cpf_limpo):
            raise ValueError('CPF inválido')
        return cpf_limpo
    
    @field_validator('telefone')
    @classmethod
    def validate_telefone(cls, v: str) -> str:
        """Normaliza telefone para E.164."""
        try:
            return normalizar_telefone(v)
        except ValueError as e:
            raise ValueError(str(e))


class ClienteCreate(ClienteBase):
    """Schema para criação de cliente."""
    pass


class ClienteUpdate(BaseModel):
    """Schema para atualização de cliente."""
    nome: str | None = Field(None, min_length=3, max_length=255)
    telefone: str | None = None
    email: str | None = None
    data_nasc: date | None = None
    
    @field_validator('telefone')
    @classmethod
    def validate_telefone(cls, v: str | None) -> str | None:
        """Normaliza telefone para E.164."""
        if v is None:
            return None
        try:
            return normalizar_telefone(v)
        except ValueError as e:
            raise ValueError(str(e))


class ClienteResponse(ClienteBase):
    """Schema de resposta de cliente."""
    id: UUID
    limite_credito: Decimal
    credito_disponivel: Decimal
    dia_vencimento: int | None
    bloqueado: bool
    ativo: bool
    criado_em: datetime
    
    model_config = {"from_attributes": True}


class CreditoUpdate(BaseModel):
    """Schema para atualização de crédito."""
    limite_credito: Decimal = Field(..., ge=0)
    dia_vencimento: int = Field(..., ge=1, le=28)


class CreditoDelta(BaseModel):
    """Schema para ajuste de crédito (usado internamente)."""
    delta: Decimal  # Positivo = crédito, Negativo = débito
```

#### 3.2.4 Próximos Passos

Continue implementando:
1. Repository
2. Service com regras de negócio
3. Routers
4. Testes

**Repita o processo para cada microsserviço seguindo a ordem recomendada.**

---

## 4. Integrações Externas

### 4.1 Mercado Pago

Criar `services/vendas/integrations/mercadopago.py`:

```python
"""Cliente para integração com Mercado Pago."""
import httpx
import hmac
import hashlib
from typing import Any
from config import settings
import structlog


log = structlog.get_logger()


class MercadoPagoClient:
    """Cliente para API do Mercado Pago."""
    
    BASE_URL = "https://api.mercadopago.com"
    
    def __init__(self):
        self.access_token = settings.MP_ACCESS_TOKEN
        self.webhook_secret = settings.MP_WEBHOOK_SECRET
    
    async def criar_pagamento_pix(
        self,
        transaction_amount: float,
        description: str,
        payer_email: str,
        external_reference: str
    ) -> dict[str, Any]:
        """
        Cria um pagamento PIX.
        
        Returns:
            Dict com qr_code, qr_code_base64 e payment_id
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/v1/payments",
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                },
                json={
                    "transaction_amount": transaction_amount,
                    "description": description,
                    "payment_method_id": "pix",
                    "payer": {
                        "email": payer_email
                    },
                    "external_reference": external_reference
                }
            )
            
            response.raise_for_status()
            data = response.json()
            
            log.info("mercadopago.payment_created", payment_id=data["id"])
            
            return {
                "payment_id": data["id"],
                "qr_code": data["point_of_interaction"]["transaction_data"]["qr_code"],
                "qr_code_base64": data["point_of_interaction"]["transaction_data"]["qr_code_base64"]
            }
    
    async def consultar_pagamento(self, payment_id: str) -> dict[str, Any]:
        """Consulta status de um pagamento."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/v1/payments/{payment_id}",
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            
            response.raise_for_status()
            return response.json()
    
    def validar_webhook_signature(self, signature: str, data: str) -> bool:
        """
        Valida assinatura HMAC-SHA256 do webhook.
        
        Args:
            signature: Assinatura do header x-signature
            data: Corpo da requisição (string)
            
        Returns:
            True se válida
        """
        expected = hmac.new(
            self.webhook_secret.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected)
```

### 4.2 Evolution API

Criar `services/notificacoes/integrations/evolution.py`:

```python
"""Cliente para Evolution API (WhatsApp)."""
import httpx
from typing import Any
from config import settings
import structlog


log = structlog.get_logger()


class EvolutionAPIClient:
    """Cliente para Evolution API."""
    
    def __init__(self):
        self.base_url = settings.EVOLUTION_URL
        self.api_key = settings.EVOLUTION_API_KEY
        self.instance = settings.EVOLUTION_INSTANCE
    
    async def enviar_mensagem(
        self,
        numero: str,
        mensagem: str
    ) -> dict[str, Any]:
        """
        Envia mensagem via WhatsApp.
        
        Args:
            numero: Número no formato E.164
            mensagem: Texto da mensagem
            
        Returns:
            Resposta da API
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/message/sendText/{self.instance}",
                headers={
                    "apikey": self.api_key,
                    "Content-Type": "application/json"
                },
                json={
                    "number": numero,
                    "text": mensagem
                }
            )
            
            response.raise_for_status()
            data = response.json()
            
            log.info("evolution.message_sent", numero=numero)
            
            return data
```

---

## 5. Testes

### 5.1 Estrutura de Testes

Cada serviço deve ter:

```
tests/
├── conftest.py          # Fixtures compartilhadas
├── test_models.py       # Testes de modelos
├── test_repositories.py # Testes de repositories
├── test_services.py     # Testes de services
├── test_routers.py      # Testes de endpoints
└── test_integration.py  # Testes de integração
```

### 5.2 Exemplo de Teste

```python
"""Teste de criação de cliente."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_criar_cliente_valido(client: AsyncClient):
    """Testa criação de cliente com dados válidos."""
    response = await client.post(
        "/clientes",
        json={
            "nome": "João Silva",
            "cpf": "12345678909",
            "telefone": "+5511999999999",
            "email": "joao@example.com"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["nome"] == "João Silva"
    assert data["cpf"] == "12345678909"


@pytest.mark.asyncio
async def test_criar_cliente_cpf_invalido(client: AsyncClient):
    """Testa criação com CPF inválido."""
    response = await client.post(
        "/clientes",
        json={
            "nome": "João Silva",
            "cpf": "11111111111",
            "telefone": "+5511999999999"
        }
    )
    
    assert response.status_code == 422
```

---

## 6. Deploy

### 6.1 Build de Produção

```bash
# 1. Build de todas as imagens
make build

# 2. Tag para registry
docker tag erp-api-gateway:latest registry.example.com/erp-api-gateway:v1.0.0

# 3. Push para registry
docker push registry.example.com/erp-api-gateway:v1.0.0
```

### 6.2 Deploy em Produção

Ver [docs/DEPLOY.md](./DEPLOY.md) para instruções detalhadas.

---

## ✅ Checklist de Implementação

### API Gateway
- [x] Estrutura base
- [x] Autenticação JWT
- [x] Middlewares
- [ ] Roteamento para serviços
- [ ] Testes completos

### Serviço de Clientes
- [ ] Modelos
- [ ] Validações
- [ ] Repositories
- [ ] Services
- [ ] Routers
- [ ] Testes

### Serviço de Produtos
- [ ] Modelos
- [ ] Validações
- [ ] Repositories
- [ ] Services
- [ ] Routers
- [ ] Testes

### Serviço de Estoque
- [ ] Modelos
- [ ] Repositories
- [ ] Services
- [ ] Routers
- [ ] Eventos
- [ ] Testes

### Serviço de Vendas
- [ ] Modelos
- [ ] Repositories
- [ ] Services
- [ ] Routers
- [ ] Integração MP
- [ ] Testes

### Serviço Financeiro
- [ ] Modelos
- [ ] Repositories
- [ ] Services
- [ ] Jobs Celery
- [ ] Routers
- [ ] Testes

### Serviço de Notificações
- [ ] Modelos
- [ ] Consumer RabbitMQ
- [ ] Integração Evolution
- [ ] Deduplicação
- [ ] Testes

---

**Próximo**: Continue com a implementação seguindo este guia!
