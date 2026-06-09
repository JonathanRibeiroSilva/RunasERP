"""
Script para popular dados iniciais de empresas.
"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from database import AsyncSessionLocal
from models.empresa import Empresa, TipoEmpresa, StatusEmpresa, RegimeTributario


async def seed_empresas():
    """Popula empresas de exemplo."""
    async with AsyncSessionLocal() as session:
        # Verificar se já existem empresas
        from sqlalchemy import select, func
        
        stmt = select(func.count()).select_from(Empresa)
        result = await session.execute(stmt)
        count = result.scalar_one()
        
        if count > 0:
            print(f"⚠️  Já existem {count} empresas cadastradas. Pulando seed.")
            return
        
        print("🌱 Criando empresas de exemplo...")
        
        # Empresa 1 - Matriz
        empresa1 = Empresa(
            slug="distribuidora-central",
            razao_social="Distribuidora Central de Alimentos LTDA",
            nome_fantasia="Distribuidora Central",
            tipo=TipoEmpresa.MATRIZ,
            status=StatusEmpresa.ATIVA,
            cnpj="12.345.678/0001-90",
            inscricao_estadual="123456789",
            regime_tributario=RegimeTributario.SIMPLES_NACIONAL,
            cep="01310-100",
            logradouro="Avenida Paulista",
            numero="1000",
            complemento="Sala 101",
            bairro="Bela Vista",
            cidade="São Paulo",
            uf="SP",
            telefone="(11) 3000-0001",
            celular="(11) 99000-0001",
            email="contato@distribuidoracentral.com.br",
            site="https://distribuidoracentral.com.br",
            cor_primaria="#1E40AF",
            cor_secundaria="#059669",
            catalogo_ativo=True,
            catalogo_titulo="Catálogo Online - Distribuidora Central",
            catalogo_descricao="Alimentos e bebidas com os melhores preços da região!",
            catalogo_whatsapp="(11) 99000-0001",
            plano="PRO",
            max_usuarios=20,
            max_produtos=None,  # Ilimitado
            max_lojas=5,
            ativo=True
        )
        session.add(empresa1)
        await session.flush()
        
        # Empresa 2 - Filial da 1
        empresa2 = Empresa(
            slug="distribuidora-central-zona-sul",
            razao_social="Distribuidora Central de Alimentos LTDA",
            nome_fantasia="Distribuidora Central - Zona Sul",
            tipo=TipoEmpresa.FILIAL,
            status=StatusEmpresa.ATIVA,
            cnpj="12.345.678/0002-71",
            inscricao_estadual="987654321",
            regime_tributario=RegimeTributario.SIMPLES_NACIONAL,
            cep="04542-001",
            logradouro="Avenida Brigadeiro Luís Antônio",
            numero="2000",
            bairro="Jardim Paulista",
            cidade="São Paulo",
            uf="SP",
            telefone="(11) 3000-0002",
            celular="(11) 99000-0002",
            email="zonasul@distribuidoracentral.com.br",
            cor_primaria="#1E40AF",
            cor_secundaria="#059669",
            catalogo_ativo=True,
            catalogo_titulo="Catálogo Online - Zona Sul",
            catalogo_descricao="Distribuidora Central - Unidade Zona Sul",
            catalogo_whatsapp="(11) 99000-0002",
            plano="PRO",
            max_usuarios=10,
            max_lojas=1,
            empresa_matriz_id=empresa1.id,
            ativo=True
        )
        session.add(empresa2)
        
        # Empresa 3 - Outra matriz
        empresa3 = Empresa(
            slug="mercadinho-do-joao",
            razao_social="João da Silva Comercio de Alimentos ME",
            nome_fantasia="Mercadinho do João",
            tipo=TipoEmpresa.MATRIZ,
            status=StatusEmpresa.ATIVA,
            cnpj="98.765.432/0001-10",
            regime_tributario=RegimeTributario.MEI,
            cep="13015-001",
            logradouro="Rua Barão de Jaguara",
            numero="500",
            bairro="Centro",
            cidade="Campinas",
            uf="SP",
            telefone="(19) 3000-0003",
            celular="(19) 99000-0003",
            email="contato@mercadinhodojoao.com.br",
            cor_primaria="#DC2626",
            cor_secundaria="#F59E0B",
            catalogo_ativo=True,
            catalogo_titulo="Mercadinho do João - Catálogo",
            catalogo_descricao="Seu mercadinho de bairro com qualidade e preço justo!",
            catalogo_whatsapp="(19) 99000-0003",
            plano="BASICO",
            max_usuarios=5,
            max_produtos=500,
            max_lojas=1,
            ativo=True
        )
        session.add(empresa3)
        
        await session.commit()
        
        print("✅ 3 empresas criadas com sucesso!")
        print(f"   - {empresa1.nome_fantasia} (Matriz)")
        print(f"   - {empresa2.nome_fantasia} (Filial)")
        print(f"   - {empresa3.nome_fantasia} (Matriz)")


async def main():
    """Função principal."""
    print("=" * 60)
    print("🌱 SEED - Serviço de Empresas")
    print("=" * 60)
    
    try:
        await seed_empresas()
        print("\n✅ Seed concluído com sucesso!")
    except Exception as e:
        print(f"\n❌ Erro ao executar seed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
