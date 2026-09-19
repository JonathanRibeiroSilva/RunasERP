"""
Propaga as credenciais Mercado Pago (sandbox) do ambiente para o banco.

As credenciais usadas em runtime ficam em `vendas.configuracoes_pagamento`
(multi-tenant, uma linha por empresa). Este script faz o upsert dessas
credenciais a partir das variáveis de ambiente MP_ACCESS_TOKEN / MP_PUBLIC_KEY
(definidas no .env), garantindo que o ambiente de teste use a aplicação de
sandbox correta.

Uso (dentro do container vendas):
    docker exec -it erp-vendas-dev python scripts/set_mercadopago_credentials.py [empresa_id ...]

Sem argumentos, atualiza a empresa_id=4 (loja de teste padrão).
"""
import asyncio
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from config import settings
from services.configuracao_pagamento_service import ConfiguracaoPagamentoService

DEFAULT_EMPRESA_IDS = [4]


async def aplicar_credenciais(empresa_ids: list[int]) -> None:
    access_token = os.environ.get("MP_ACCESS_TOKEN", "").strip()
    public_key = os.environ.get("MP_PUBLIC_KEY", "").strip()
    # Opcional: sem ele a rota do webhook segue aceitando não assinado.
    webhook_secret = os.environ.get("MP_WEBHOOK_SECRET", "").strip()

    if not access_token or not public_key:
        raise SystemExit(
            "MP_ACCESS_TOKEN e MP_PUBLIC_KEY precisam estar definidos no ambiente (.env)."
        )

    if settings.MP_ENVIRONMENT.strip().lower() == "production":
        raise SystemExit(
            "MP_ENVIRONMENT=production: este script só aplica credenciais de sandbox."
        )

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        for empresa_id in empresa_ids:
            await ConfiguracaoPagamentoService.criar_ou_atualizar(
                session,
                empresa_id=empresa_id,
                access_token=access_token,
                public_key=public_key,
                ativo=True,
                webhook_secret=webhook_secret or None,
            )
            print(
                f"[ok] empresa_id={empresa_id} -> public_key={public_key[:16]}... "
                f"(sandbox={settings.mercadopago_sandbox}, "
                f"webhook_assinado={'sim' if webhook_secret else 'não'})"
            )

    await engine.dispose()


if __name__ == "__main__":
    ids = [int(a) for a in sys.argv[1:]] or DEFAULT_EMPRESA_IDS
    asyncio.run(aplicar_credenciais(ids))
