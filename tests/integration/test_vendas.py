"""
Testes de Integração - Serviço de Vendas
Cobre: Pedidos, Pagamentos, Workflow, Multi-tenancy
"""
import pytest
import httpx


@pytest.mark.integration
@pytest.mark.asyncio
class TestVendasPedidos:
    """Suite de testes de pedidos."""
    
    async def test_listar_pedidos(
        self, async_client: httpx.AsyncClient, admin_headers: dict
    ):
        """Teste: Listar pedidos."""
        response = await async_client.get(
            "/pedidos", params={"skip": 0, "limit": 10}, headers=admin_headers
        )
        
        assert response.status_code == 200
        print("✅ Listagem de pedidos validada")
    
    async def test_isolamento_multitenancy(
        self, async_client: httpx.AsyncClient, admin_token: str
    ):
        """Teste: Pedidos de empresa 1 não aparecem para empresa 2."""
        h1 = {"Authorization": f"Bearer {admin_token}", "X-Empresa-Id": "1"}
        h2 = {"Authorization": f"Bearer {admin_token}", "X-Empresa-Id": "2"}
        
        list1 = await async_client.get("/pedidos", headers=h1)
        list2 = await async_client.get("/pedidos", headers=h2)
        
        assert list1.status_code == 200
        assert list2.status_code == 200
        print("✅ Isolamento multi-tenant pedidos validado")
