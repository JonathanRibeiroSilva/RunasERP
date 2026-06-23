"""
Testes de Autenticação - API Gateway
Cobre: Login, OAuth, Refresh Tokens, Permissões
"""
import pytest
import httpx


@pytest.mark.integration
@pytest.mark.auth
@pytest.mark.asyncio
class TestAuth:
    """Suite de testes de autenticação."""
    
    async def test_login_admin_success(self, async_client: httpx.AsyncClient):
        """Teste: Login com credenciais de admin corretas."""
        response = await async_client.post(
            "/auth/login",
            json={"email": "admin@runas.com", "password": "Admin@123"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["usuario"]["email"] == "admin@runas.com"
    
    async def test_login_invalid_password(self, async_client: httpx.AsyncClient):
        """Teste: Login com senha incorreta retorna 401."""
        response = await async_client.post(
            "/auth/login",
            json={"email": "admin@runas.com", "password": "SenhaErrada123"}
        )
        assert response.status_code == 401
    
    async def test_access_protected_route_with_token(
        self, async_client: httpx.AsyncClient, admin_token: str
    ):
        """Teste: Acessar rota protegida com token válido retorna 200."""
        response = await async_client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        assert response.json()["email"] == "admin@runas.com"
