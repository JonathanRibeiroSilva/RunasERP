"""
Testes da Loja Online Pública
Cobre: Listagem de produtos, categorias, busca (sem autenticação)
"""
import pytest
import httpx


@pytest.mark.integration
@pytest.mark.asyncio
class TestLojaOnlinePublica:
    """Suite de testes da loja online pública."""
    
    async def test_listar_produtos_publico_sem_auth(self, async_client: httpx.AsyncClient):
        """Teste: Listar produtos públicos sem autenticação."""
        response = await async_client.get(
            "/loja-online/publico/produtos",
            params={"empresaSlug": "distribuidora-central", "limit": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data or isinstance(data, list)
        print(f"✅ Loja online pública funcionando!")
    
    async def test_listar_categorias_publico_sem_auth(self, async_client: httpx.AsyncClient):
        """Teste: Listar categorias públicas sem autenticação."""
        response = await async_client.get(
            "/loja-online/publico/categorias",
            params={"empresaSlug": "distribuidora-central"}
        )
        
        assert response.status_code == 200
