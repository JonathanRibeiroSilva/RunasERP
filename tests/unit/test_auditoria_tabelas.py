"""As migrations de auditoria só podem ligar trigger em tabela que existe.

O plano desta fase listava `financeiro.contas_pagar` e `financeiro.contas_receber`
como alvos de trigger. Nenhuma das duas existe: financeiro é um serviço vazio,
sem model e sem migration. Também trazia `vendas.venda_itens` (o nome real é
`itens_venda`) e `estoque.*_saldo` (o real é `estoque.estoque`).

CREATE TRIGGER em tabela inexistente derruba o boot do serviço, e migrations
não rodam em produção — o schema foi carimbado — então o erro só apareceria
num banco novo, que é exatamente onde ninguém está olhando.
"""
import ast
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

TABELA = re.compile(r'__tablename__\s*=\s*["\']([a-z_]+)["\']')


def _tabelas_do_servico(servico: Path) -> set:
    """Todo __tablename__ declarado nos models do serviço."""
    return {
        m
        for path in (servico / "models").rglob("*.py")
        for m in TABELA.findall(path.read_text(encoding="utf-8"))
    }


def _alvos_da_migration(path: Path) -> list:
    """A lista TABELAS declarada no topo da migration de auditoria."""
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if (
            isinstance(node, ast.Assign)
            and any(getattr(t, "id", None) == "TABELAS" for t in node.targets)
        ):
            return ast.literal_eval(node.value)
    return []


def test_toda_tabela_auditada_existe_como_model():
    inexistentes = []
    for migration in REPO.glob("*/alembic/versions/*_auditoria.py"):
        servico = migration.parents[2]
        conhecidas = _tabelas_do_servico(servico)
        inexistentes += [
            f"{servico.name}: {t}"
            for t in _alvos_da_migration(migration)
            if t not in conhecidas
        ]
    for migration in REPO.glob("services/*/alembic/versions/*_auditoria.py"):
        servico = migration.parents[2]
        conhecidas = _tabelas_do_servico(servico)
        inexistentes += [
            f"{servico.name}: {t}"
            for t in _alvos_da_migration(migration)
            if t not in conhecidas
        ]
    assert not inexistentes, (
        "CREATE TRIGGER em tabela que nenhum model declara — o boot morre num "
        f"banco novo: {inexistentes}"
    )


def test_auditoria_nao_audita_a_si_mesma():
    """Trigger nas tabelas de auditoria seria recursão infinita."""
    proibidas = {"auditoria", "auditoria_registros", "webhooks_processados",
                 "webhooks_plataforma", "carrinho"}
    ofensores = [
        f"{m.parents[2].name}: {t}"
        for m in list(REPO.glob("*/alembic/versions/*_auditoria.py"))
        + list(REPO.glob("services/*/alembic/versions/*_auditoria.py"))
        for t in _alvos_da_migration(m)
        if t in proibidas
    ]
    assert not ofensores, f"auditar o auditor (ou cache/fila): {ofensores}"
