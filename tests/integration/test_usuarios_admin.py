"""
Testes de Integração - Usuários do tenant (/auth/admin/usuarios)

Cobre o isolamento cross-tenant e as invariantes que impedem um admin de
trancar a própria empresa para fora. Nenhum destes existia antes: a tela de
usuários simplesmente não tinha backend.
"""
import pytest
import httpx


@pytest.mark.integration
@pytest.mark.asyncio
class TestUsuariosAdmin:
    """Suite de isolamento e invariantes de usuários."""

    async def test_listar_devolve_so_o_proprio_tenant(
        self, async_client: httpx.AsyncClient, admin_headers: dict
    ):
        """UsuarioRepository.listar() não filtrava por empresa_id."""
        r = await async_client.get("/auth/admin/usuarios", headers=admin_headers)
        assert r.status_code == 200
        corpo = r.json()
        tenant = int(admin_headers["X-Empresa-Id"])
        assert {u["empresa_id"] for u in corpo["items"]} <= {tenant}
        assert corpo["ativos"] <= corpo["total"]

    async def test_listar_sem_auth_e_rejeitado(self, async_client: httpx.AsyncClient):
        """A rota é de admin: sem token não passa."""
        r = await async_client.get("/auth/admin/usuarios")
        assert r.status_code in (401, 403)

    async def test_editar_usuario_de_outro_tenant_devolve_404(
        self, async_client: httpx.AsyncClient, admin_headers: dict
    ):
        """404 e não 403: confirmar existência já vaza informação do outro lojista."""
        alheio = "00000000-0000-0000-0000-000000000001"
        r = await async_client.put(
            f"/auth/admin/usuarios/{alheio}",
            headers=admin_headers,
            json={"nome": "invadido"},
        )
        assert r.status_code == 404

    async def test_admin_nao_desativa_a_si_mesmo(
        self, async_client: httpx.AsyncClient, admin_headers: dict
    ):
        """O caminho mais curto para o tenant ficar sem ninguém dentro."""
        eu = await async_client.get("/auth/me", headers=admin_headers)
        assert eu.status_code == 200
        meu_id = eu.json()["id"]

        r = await async_client.put(
            f"/auth/admin/usuarios/{meu_id}",
            headers=admin_headers,
            json={"ativo": False},
        )
        assert r.status_code == 409

        r = await async_client.delete(
            f"/auth/admin/usuarios/{meu_id}", headers=admin_headers
        )
        assert r.status_code == 409

    async def test_admin_nao_se_rebaixa(
        self, async_client: httpx.AsyncClient, admin_headers: dict
    ):
        """Rebaixar-se a OPERADOR é desativar-se com outro nome."""
        eu = await async_client.get("/auth/me", headers=admin_headers)
        r = await async_client.put(
            f"/auth/admin/usuarios/{eu.json()['id']}",
            headers=admin_headers,
            json={"role": "OPERADOR"},
        )
        assert r.status_code == 409

    async def test_nao_e_possivel_criar_super_admin_pelo_tenant(
        self, async_client: httpx.AsyncClient, admin_headers: dict
    ):
        """SUPER_ADMIN entrou no RoleEnum: um ADMIN não pode se promover a dono."""
        r = await async_client.post(
            "/auth/admin/usuarios",
            headers=admin_headers,
            json={
                "nome": "Escalada de privilegio",
                "email": "escalada@teste.local",
                "senha": "Senha@12345",
                "role": "SUPER_ADMIN",
                "empresa_id": int(admin_headers["X-Empresa-Id"]),
            },
        )
        assert r.status_code == 403
