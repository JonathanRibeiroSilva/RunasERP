"""
Seed de clientes com CPFs válidos.
"""
import asyncio
from datetime import date
from decimal import Decimal
from sqlalchemy import select, func

from database import AsyncSessionLocal
from models.cliente import Cliente


async def seed_clientes():
    """Cria clientes de exemplo."""
    async with AsyncSessionLocal() as session:
        # Verificar se já existem clientes
        stmt = select(func.count()).select_from(Cliente).where(Cliente.empresa_id == 1)
        result = await session.execute(stmt)
        count = result.scalar_one()
        
        if count > 0:
            print(f"⚠️  Já existem {count} clientes para empresa_id=1. Pulando seed.")
            return
        
        print("🌱 Criando clientes...")
        
        clientes = [
            # Clientes Pessoa Física (CPF válidos)
            {
                "empresa_id": 1,
                "nome": "João da Silva",
                "cpf": "30180957660",  # CPF válido
                "email": "joao.silva@email.com",
                "telefone": "11987654321",
                "data_nasc": date(1985, 3, 15),
                "limite_credito": Decimal("5000.00"),
                "credito_disponivel": Decimal("5000.00"),
                "ativo": True
            },
            {
                "empresa_id": 1,
                "nome": "Maria Oliveira Santos",
                "cpf": "06944367475",  # CPF válido
                "email": "maria.santos@email.com",
                "telefone": "11976543210",
                "data_nasc": date(1990, 7, 22),
                "limite_credito": Decimal("3000.00"),
                "credito_disponivel": Decimal("2500.00"),
                "ativo": True
            },
            {
                "empresa_id": 1,
                "nome": "Carlos Eduardo Pereira",
                "cpf": "10886824214",  # CPF válido
                "email": "carlos.pereira@email.com",
                "telefone": "11965432109",
                "data_nasc": date(1978, 11, 5),
                "limite_credito": Decimal("10000.00"),
                "credito_disponivel": Decimal("8500.00"),
                "ativo": True
            },
            {
                "empresa_id": 1,
                "nome": "Ana Paula Costa",
                "cpf": "71187720623",  # CPF válido
                "email": "ana.costa@email.com",
                "telefone": "11954321098",
                "data_nasc": date(1995, 2, 18),
                "limite_credito": Decimal("2000.00"),
                "credito_disponivel": Decimal("2000.00"),
                "ativo": True
            },
            {
                "empresa_id": 1,
                "nome": "Pedro Henrique Alves",
                "cpf": "12126502392",  # CPF válido
                "email": "pedro.alves@email.com",
                "telefone": "11943210987",
                "limite_credito": Decimal("1500.00"),
                "credito_disponivel": Decimal("500.00"),
                "ativo": False,
                "bloqueado": True
            },
            {
                "empresa_id": 1,
                "nome": "Juliana Ferreira Lima",
                "cpf": "24578753239",  # CPF válido
                "email": "juliana.lima@email.com",
                "telefone": "11932109876",
                "data_nasc": date(1988, 9, 30),
                "limite_credito": Decimal("4000.00"),
                "credito_disponivel": Decimal("3800.00"),
                "ativo": True
            },
            {
                "empresa_id": 1,
                "nome": "Roberto Carlos Souza",
                "cpf": "92726971156",  # CPF válido
                "email": "roberto.souza@email.com",
                "telefone": "11921098765",
                "data_nasc": date(1982, 4, 12),
                "limite_credito": Decimal("6000.00"),
                "credito_disponivel": Decimal("6000.00"),
                "ativo": True
            },
            {
                "empresa_id": 1,
                "nome": "Fernanda Cristina Rocha",
                "cpf": "45060623297",  # CPF válido
                "email": "fernanda.rocha@email.com",
                "telefone": "11910987654",
                "data_nasc": date(1993, 6, 25),
                "limite_credito": Decimal("2500.00"),
                "credito_disponivel": Decimal("1800.00"),
                "ativo": True
            },
            
            # Clientes Empresas (usando CPF como identificador único - CPFs válidos)
            {
                "empresa_id": 1,
                "nome": "Restaurante Sabor do Brasil Ltda",
                "cpf": "43747818030",  # CPF válido
                "email": "contato@saborbrasil.com",
                "telefone": "1130001000",
                "limite_credito": Decimal("25000.00"),
                "credito_disponivel": Decimal("20000.00"),
                "ativo": True
            },
            {
                "empresa_id": 1,
                "nome": "Padaria Pão Quente",
                "cpf": "17803433103",  # CPF válido
                "email": "comercial@paoquente.com.br",
                "telefone": "1130002000",
                "limite_credito": Decimal("15000.00"),
                "credito_disponivel": Decimal("12000.00"),
                "ativo": True
            },
            {
                "empresa_id": 1,
                "nome": "Bar e Petiscaria do Zé",
                "cpf": "74047742848",  # CPF válido
                "email": "bar@doze.com.br",
                "telefone": "1130003000",
                "limite_credito": Decimal("10000.00"),
                "credito_disponivel": Decimal("8500.00"),
                "ativo": True
            },
            {
                "empresa_id": 1,
                "nome": "Lanchonete da Esquina",
                "cpf": "62742398716",  # CPF válido
                "email": "contato@lanchonetedaesquina.com.br",
                "telefone": "1130004000",
                "limite_credito": Decimal("8000.00"),
                "credito_disponivel": Decimal("8000.00"),
                "ativo": True
            },
            {
                "empresa_id": 1,
                "nome": "Mercadinho Bom Preço",
                "cpf": "50814072593",  # CPF válido
                "email": "compras@bompreco.com.br",
                "telefone": "1130005000",
                "limite_credito": Decimal("30000.00"),
                "credito_disponivel": Decimal("25000.00"),
                "ativo": True
            },
            {
                "empresa_id": 1,
                "nome": "Pizzaria Bella Napoli",
                "cpf": "40774760117",  # CPF válido
                "email": "pedidos@bellanapoli.com.br",
                "telefone": "1130006000",
                "limite_credito": Decimal("12000.00"),
                "credito_disponivel": Decimal("10000.00"),
                "ativo": True
            },
            {
                "empresa_id": 1,
                "nome": "Supermercado Preço Bom",
                "cpf": "62192760000",  # CPF válido
                "email": "suprimentos@precobom.com.br",
                "telefone": "1130007000",
                "limite_credito": Decimal("50000.00"),
                "credito_disponivel": Decimal("45000.00"),
                "ativo": True
            },
        ]
        
        for cli_data in clientes:
            cliente = Cliente(**cli_data)
            session.add(cliente)
        
        await session.commit()
        
        print(f"✅ {len(clientes)} clientes criados com sucesso!")


async def main():
    """Função principal."""
    print("=" * 60)
    print("🌱 SEED - Clientes")
    print("=" * 60)
    
    try:
        await seed_clientes()
        print("\n✅ Seed concluído com sucesso!")
    except Exception as e:
        print(f"\n❌ Erro ao executar seed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
