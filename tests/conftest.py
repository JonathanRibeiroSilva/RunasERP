"""
Fixtures compartilhadas para todos os testes do Runas ERP.
"""
import asyncio
import os
import pytest
from typing import AsyncGenerator, Generator
import httpx
from faker import Faker

os.environ["SECRET_KEY"] = "test-secret-key-super-secure-min-32-chars"

fake = Faker("pt_BR")


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Cria um event loop para toda a sessão de testes."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def api_base_url() -> str:
    """URL base do API Gateway."""
    return os.getenv("API_URL", "http://localhost:8000")


@pytest.fixture
async def async_client(api_base_url: str) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Cliente HTTP async para testes de API."""
    async with httpx.AsyncClient(
        base_url=api_base_url,
        timeout=10.0,
        follow_redirects=True
    ) as client:
        yield client


@pytest.fixture
async def admin_token(async_client: httpx.AsyncClient) -> str:
    """Token de autenticação do admin."""
    response = await async_client.post(
        "/auth/login",
        json={"email": "admin@runas.com", "password": "Admin@123"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
async def admin_headers(admin_token: str) -> dict:
    """Headers com autenticação de admin + empresa_id=1."""
    return {
        "Authorization": f"Bearer {admin_token}",
        "X-Empresa-Id": "1"
    }


@pytest.fixture
def fake_cliente() -> dict:
    """Dados fake de um cliente para testes."""
    return {
        "empresa_id": 1,
        "tipo_pessoa": "F",
        "nome_completo": fake.name(),
        "cpf": "123.456.789-00",
        "email": fake.email(),
        "telefone": fake.phone_number()[:15],
        "data_nascimento": "1990-01-01"
    }
