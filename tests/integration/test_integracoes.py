"""
Testes de Integração - Integrações do tenant (/integracoes)

O router de integrações e o de pagamento eram inalcançáveis pelo gateway:
/admin/pagamento não estava em SERVICE_URLS e o mapa casa pelo primeiro
segmento. Estes testes falham se o roteamento quebrar de novo.
"""
import pytest
import httpx


@pytest.mark.integration
@pytest.mark.asyncio
class TestIntegracoes:
    """Suite de alcance, isolamento e não-vazamento de segredo."""

    async def test_rota_e_alcancavel_pelo_gateway(
        self, async_client: httpx.AsyncClient, admin_headers: dict
    ):
        """O furo original: 404 aqui significa que o mapa do gateway regrediu."""
        r = await async_client.get("/integracoes", headers=admin_headers)
        assert r.status_code == 200
        assert r.json()["empresa_id"] == int(admin_headers["X-Empresa-Id"])

    async def test_status_do_mercadopago_e_alcancavel(
        self, async_client: httpx.AsyncClient, admin_headers: dict
    ):
        """Mesmo furo, prefixo /pagamentos/admin."""
        r = await async_client.get("/pagamentos/admin/status", headers=admin_headers)
        assert r.status_code == 200
        assert "configurado" in r.json()

    async def test_sem_auth_e_rejeitado(self, async_client: httpx.AsyncClient):
        """Credencial de integração não é rota pública."""
        r = await async_client.get("/integracoes")
        assert r.status_code in (401, 403)

    async def test_resposta_nunca_devolve_segredo(
        self, async_client: httpx.AsyncClient, admin_headers: dict
    ):
        """
        A cifra no banco não serve para nada se a API devolve o valor em claro.

        Salva credenciais e confere que a resposta traz só os booleanos
        *_configurado — nem a chave da Evolution nem a senha do SMTP voltam.
        """
        r = await async_client.put(
            "/integracoes",
            headers=admin_headers,
            json={
                "evolution_url": "https://evo.teste.local",
                "evolution_api_key": "chave-fake-x1",
                "evolution_instance": "teste",
                "whatsapp_ativo": True,
                "smtp_host": "smtp.teste.local",
                "smtp_port": 587,
                "smtp_user": "envio@teste.local",
                "smtp_password": "senha-fake-x2",
                "email_ativo": True,
            },
        )
        assert r.status_code == 200, r.text

        corpo = r.json()
        assert corpo["evolution_api_key_configurado"] is True
        assert corpo["smtp_password_configurado"] is True

        bruto = r.text
        assert "chave-fake-x1" not in bruto
        assert "senha-fake-x2" not in bruto

        # E também não vaza no GET seguinte
        depois = await async_client.get("/integracoes", headers=admin_headers)
        assert "chave-fake-x1" not in depois.text
        assert "senha-fake-x2" not in depois.text

    async def test_segredo_vazio_mantem_o_atual(
        self, async_client: httpx.AsyncClient, admin_headers: dict
    ):
        """
        A tela mostra •••••• e só envia o segredo quando o admin digita.

        Um salvamento parcial não pode apagar a senha que ninguém tocou.
        """
        r = await async_client.put(
            "/integracoes",
            headers=admin_headers,
            json={"smtp_from_name": "Loja Teste"},
        )
        assert r.status_code == 200
        assert r.json()["smtp_password_configurado"] is True
