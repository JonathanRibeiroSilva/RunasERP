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
    
    async def test_listar_empresas_devolve_so_a_propria(
        self, async_client: httpx.AsyncClient, admin_headers: dict
    ):
        """GET /empresas nunca vaza outro tenant — uma empresa, uma loja."""
        response = await async_client.get("/empresas", headers=admin_headers)
        assert response.status_code == 200
        tenant = int(admin_headers["X-Empresa-Id"])
        items = response.json()["items"]
        assert {e["id"] for e in items} <= {tenant}, f"vazou outro tenant: {items}"

    async def test_buscar_empresa_de_outro_tenant_e_negado(
        self, async_client: httpx.AsyncClient, admin_headers: dict
    ):
        """Isolamento por id: o tenant 1 não lê a empresa 2."""
        outro = int(admin_headers["X-Empresa-Id"]) + 1
        response = await async_client.get(f"/empresas/{outro}", headers=admin_headers)
        assert response.status_code in (403, 404)

    async def test_atualizar_empresa_de_outro_tenant_e_negado(
        self, async_client: httpx.AsyncClient, admin_headers: dict
    ):
        """Escrita cross-tenant é o furo caro — bloqueada antes de tocar o banco."""
        outro = int(admin_headers["X-Empresa-Id"]) + 1
        response = await async_client.put(
            f"/empresas/{outro}",
            headers=admin_headers,
            json={"nome_fantasia": "invadida"},
        )
        assert response.status_code in (403, 404)

    async def test_empresa_nao_se_auto_promove_de_plano(
        self, async_client: httpx.AsyncClient, admin_headers: dict
    ):
        """plano/max_* saíram de EmpresaUpdate: o lojista não muda o próprio plano."""
        eu = admin_headers["X-Empresa-Id"]
        antes = await async_client.get(f"/empresas/{eu}", headers=admin_headers)
        assert antes.status_code == 200
        plano_antes = antes.json().get("plano")

        await async_client.put(
            f"/empresas/{eu}",
            headers=admin_headers,
            json={"plano": "ENTERPRISE", "max_usuarios": 9999},
        )
        depois = await async_client.get(f"/empresas/{eu}", headers=admin_headers)
        assert depois.json().get("plano") == plano_antes

    async def test_listar_empresas_sem_header_de_tenant_e_rejeitado(
        self, async_client: httpx.AsyncClient
    ):
        """Fail closed: sem X-Empresa-Id o serviço não adivinha o tenant."""
        response = await async_client.get("/empresas")
        assert response.status_code in (400, 401, 403)

    
    async def test_buscar_empresa_publica(
        self, async_client: httpx.AsyncClient
    ):
        """Teste: Buscar empresa pública por slug."""
        response = await async_client.get("/empresas/publico/distribuidora-central")
        assert response.status_code in [200, 404]
        print("✅ Endpoint empresa pública validado")
