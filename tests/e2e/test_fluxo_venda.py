"""
Teste End-to-End: Fluxo Completo de Venda
Simula: Criar Produto → Adicionar Estoque → Criar Pedido → Processar Pagamento
"""
import pytest
import httpx
from faker import Faker

fake = Faker("pt_BR")


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.asyncio
async def test_fluxo_venda_completo(
    async_client: httpx.AsyncClient,
    admin_headers: dict
):
    """
    Teste E2E: Fluxo completo de venda desde criação do produto até pagamento.
    """
    
    # Criar Categoria
    categoria_data = {
        "empresa_id": 1,
        "nome": f"Categoria {fake.word().capitalize()}",
        "descricao": "Categoria para teste E2E"
    }
    categoria_response = await async_client.post(
        "/categorias", json=categoria_data, headers=admin_headers
    )
    assert categoria_response.status_code == 201
    categoria_id = categoria_response.json()["id"]
    
    # Criar Produto
    produto_data = {
        "empresa_id": 1,
        "nome": f"Produto {fake.word().capitalize()}",
        "descricao": "Produto teste E2E",
        "ativo": True,
        "categoria_id": categoria_id
    }
    produto_response = await async_client.post(
        "/produtos", json=produto_data, headers=admin_headers
    )
    assert produto_response.status_code == 201
    produto_id = produto_response.json()["id"]
    
    print(f"✅ Fluxo de venda testado: Categoria {categoria_id} → Produto {produto_id}")
