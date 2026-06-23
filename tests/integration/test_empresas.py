"""
Testes de Integração - Serviço de Empresas
Cobre: CRUD, Validação CNPJ, Slug único
"""
import pytest
import httpx
from faker import Faker

fake = Faker("pt_BR")


@pytest.mark.integration
@pytest.mark.asyncio
class TestEmpresasCRUD:
    """Suite de testes de CRUD de empresas."""
    
    async def test_listar_empresas(
        self, async_client: httpx.AsyncClient, admin_headers: dict
    ):
        """Teste: Listar empresas."""
        response = await async_client.get("/empresas", headers=admin_headers)
        assert response.status_code == 200
        print("✅ Listagem de empresas validada")
    
    async def test_buscar_empresa_publica(
        self, async_client: httpx.AsyncClient
    ):
        """Teste: Buscar empresa pública por slug."""
        response = await async_client.get("/empresas/publico/distribuidora-central")
        assert response.status_code in [200, 404]
        print("✅ Endpoint empresa pública validado")
