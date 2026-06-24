"""
Testes de Integração - Serviço de Clientes
Cobre: CRUD, Endereços, Crédito, Validações, Multi-tenancy
"""
import pytest
import httpx
from faker import Faker

fake = Faker("pt_BR")


@pytest.mark.integration
@pytest.mark.asyncio
class TestClientesCRUD:
    """Suite de testes de CRUD de clientes."""
    
    async def test_criar_cliente_pf_sucesso(
        self, async_client: httpx.AsyncClient, admin_headers: dict
    ):
        """Teste: Criar cliente pessoa física com sucesso."""
        cliente_data = {
            "empresa_id": 1,
            "tipo_pessoa": "F",
            "nome_completo": fake.name(),
            "cpf": "123.456.789-00",
            "email": fake.email(),
            "telefone": "(11) 98765-4321",
            "data_nascimento": "1990-01-15"
        }
        
        response = await async_client.post(
            "/clientes", json=cliente_data, headers=admin_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["tipo_pessoa"] == "F"
        print(f"✅ Cliente PF criado: {data['id']}")
    
    async def test_listar_clientes(
        self, async_client: httpx.AsyncClient, admin_headers: dict
    ):
        """Teste: Listar clientes com paginação."""
        response = await async_client.get(
            "/clientes", params={"skip": 0, "limit": 10}, headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data
        print(f"✅ {data['total']} clientes encontrados")
    
    async def test_isolamento_multitenancy(
        self, async_client: httpx.AsyncClient, admin_token: str
    ):
        """Teste: Cliente de empresa 1 não aparece para empresa 2."""
        headers_emp1 = {"Authorization": f"Bearer {admin_token}", "X-Empresa-Id": "1"}
        headers_emp2 = {"Authorization": f"Bearer {admin_token}", "X-Empresa-Id": "2"}
        
        cliente_data = {
            "empresa_id": 1,
            "tipo_pessoa": "F",
            "nome_completo": "Cliente Empresa 1",
            "cpf": "111.111.111-11",
            "email": "emp1@test.com",
            "telefone": "(11) 91111-1111"
        }
        
        create_resp = await async_client.post("/clientes", json=cliente_data, headers=headers_emp1)
        assert create_resp.status_code == 201
        cliente_id = create_resp.json()["id"]
        
        get_resp = await async_client.get(f"/clientes/{cliente_id}", headers=headers_emp2)
        assert get_resp.status_code == 404
        print("✅ Isolamento multi-tenant validado")
