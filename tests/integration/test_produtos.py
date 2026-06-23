"""
Testes de Integração - Serviço de Produtos
Cobre: CRUD Produtos, Categorias, Variantes, Cálculo de Preço, Multi-tenancy
"""
import pytest
import httpx
from faker import Faker

fake = Faker("pt_BR")


@pytest.mark.integration
@pytest.mark.asyncio
class TestCategorias:
    """Suite de testes de categorias."""
    
    async def test_criar_categoria(
        self, async_client: httpx.AsyncClient, admin_headers: dict
    ):
        """Teste: Criar categoria com sucesso."""
        categoria_data = {
            "empresa_id": 1,
            "nome": f"Categoria {fake.word().capitalize()}",
            "descricao": "Descrição da categoria teste"
        }
        
        response = await async_client.post(
            "/categorias", json=categoria_data, headers=admin_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        print(f"✅ Categoria criada: {data['id']}")


@pytest.mark.integration
@pytest.mark.asyncio
class TestProdutos:
    """Suite de testes de produtos."""
    
    async def test_criar_produto_completo(
        self, async_client: httpx.AsyncClient, admin_headers: dict
    ):
        """Teste: Criar produto completo com categoria."""
        categoria = await async_client.post(
            "/categorias",
            json={"empresa_id": 1, "nome": "Bebidas", "descricao": "Teste"},
            headers=admin_headers
        )
        categoria_id = categoria.json()["id"]
        
        produto_data = {
            "empresa_id": 1,
            "nome": f"Produto {fake.word().capitalize()}",
            "descricao": "Produto para testes",
            "ativo": True,
            "categoria_id": categoria_id
        }
        
        response = await async_client.post(
            "/produtos", json=produto_data, headers=admin_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        print(f"✅ Produto criado: {data['id']}")
    
    async def test_isolamento_multitenancy(
        self, async_client: httpx.AsyncClient, admin_token: str
    ):
        """Teste: Produto de empresa 1 não aparece para empresa 2."""
        h1 = {"Authorization": f"Bearer {admin_token}", "X-Empresa-Id": "1"}
        h2 = {"Authorization": f"Bearer {admin_token}", "X-Empresa-Id": "2"}
        
        cat = await async_client.post(
            "/categorias", json={"empresa_id": 1, "nome": "Cat1", "descricao": "T"}, headers=h1
        )
        
        prod = await async_client.post(
            "/produtos",
            json={"empresa_id": 1, "nome": "P1", "descricao": "T", "ativo": True, "categoria_id": cat.json()["id"]},
            headers=h1
        )
        produto_id = prod.json()["id"]
        
        get_resp = await async_client.get(f"/produtos/{produto_id}", headers=h2)
        assert get_resp.status_code == 404
        print("✅ Isolamento multi-tenant validado")
