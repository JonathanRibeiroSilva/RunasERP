"""
Script para popular banco com dados de teste.
"""
import asyncio
from datetime import date
from decimal import Decimal
from database import AsyncSessionLocal
from models.cliente import Cliente, Endereco


async def seed_data():
    """Popula banco com dados de teste."""
    async with AsyncSessionLocal() as session:
        print("🌱 Iniciando seed de clientes...")
        
        # Verificar se já existem clientes
        from sqlalchemy import select, func
        result = await session.execute(select(func.count()).select_from(Cliente))
        count = result.scalar_one()
        
        if count > 0:
            print(f"⚠️  Já existem {count} clientes no banco. Pulando seed.")
            return
        
        # Criar clientes de teste para empresa 1
        clientes = [
            Cliente(
                empresa_id=1,
                cpf="12345678901",
                nome="João Silva",
                telefone="+5511999991111",
                email="joao@email.com",
                data_nasc=date(1985, 5, 15),
                limite_credito=Decimal("1000.00"),
                credito_disponivel=Decimal("1000.00"),
                dia_vencimento=10,
                bloqueado=False,
                ativo=True
            ),
            Cliente(
                empresa_id=1,
                cpf="98765432109",
                nome="Maria Santos",
                telefone="+5511999992222",
                email="maria@email.com",
                data_nasc=date(1990, 8, 20),
                limite_credito=Decimal("500.00"),
                credito_disponivel=Decimal("500.00"),
                dia_vencimento=5,
                bloqueado=False,
                ativo=True
            ),
            Cliente(
                empresa_id=1,
                cpf="11122233344",
                nome="Pedro Oliveira",
                telefone="+5511999993333",
                email="pedro@email.com",
                data_nasc=date(1978, 12, 10),
                limite_credito=Decimal("2000.00"),
                credito_disponivel=Decimal("2000.00"),
                dia_vencimento=15,
                bloqueado=False,
                ativo=True
            ),
        ]
        
        for cliente in clientes:
            session.add(cliente)
        
        await session.flush()
        
        # Adicionar endereços para o primeiro cliente
        enderecos = [
            Endereco(
                cliente_id=clientes[0].id,
                cep="01310100",
                logradouro="Avenida Paulista",
                numero="1000",
                complemento="Apto 101",
                bairro="Bela Vista",
                cidade="São Paulo",
                uf="SP",
                principal=True
            ),
            Endereco(
                cliente_id=clientes[0].id,
                cep="04542001",
                logradouro="Rua Joaquim Floriano",
                numero="500",
                bairro="Itaim Bibi",
                cidade="São Paulo",
                uf="SP",
                principal=False
            ),
        ]
        
        for endereco in enderecos:
            session.add(endereco)
        
        await session.commit()
        
        print(f"✅ {len(clientes)} clientes criados com sucesso!")
        print(f"✅ {len(enderecos)} endereços criados com sucesso!")


if __name__ == "__main__":
    asyncio.run(seed_data())

