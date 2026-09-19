"""Nenhum deploy migra sem um dump do banco feito antes.

Todo serviço roda `alembic upgrade head` no boot, e o rollback do deploy.yml só
troca imagem — nunca desfaz DDL. Até 2026-09-19 não havia backup de tipo nenhum
(/data/coolify/backups vazio). O db-backup do compose de prod é o que fica entre
uma migration ruim e o dado perdido.

Um backup que roda em paralelo com a migration não protege nada: estes testes
guardam o encadeamento que faz dele pré-requisito — db-backup → db-init → cada
serviço que migra — e os dois detalhes que o tornam confiável.
"""
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]


def _servicos() -> dict:
    compose = yaml.safe_load((REPO / "docker-compose.prod.yml").read_text(encoding="utf-8"))
    return compose["services"]


def _migram() -> list:
    """Quem roda `alembic upgrade head` no boot: o gateway e todo diretório de services/."""
    nomes = ["api-gateway"] + sorted(p.name for p in (REPO / "services").iterdir() if p.is_dir())
    return [f"{n}-prod" for n in nomes]


def test_db_init_so_roda_depois_do_backup_terminar_bem():
    condicao = _servicos()["db-init"].get("depends_on", {}).get("db-backup", {}).get("condition")

    assert condicao == "service_completed_successfully", (
        "db-init não espera o db-backup sair 0 — um deploy que não conseguiu fazer "
        f"o dump seguiria migrando (condition={condicao!r})"
    )


def test_todo_servico_que_migra_espera_o_db_init():
    servicos = _servicos()
    soltos = [
        nome for nome in _migram()
        if servicos.get(nome, {}).get("depends_on", {}).get("db-init", {}).get("condition")
        != "service_completed_successfully"
    ]

    assert not soltos, (
        f"estes serviços migram no boot sem esperar db-init (e portanto o backup): {soltos}"
    )


def test_backup_mora_em_bind_mount_absoluto():
    """O Coolify reescreve volumes nomeados e descarta `external:`; bind mount ele repassa."""
    volumes = _servicos()["db-backup"].get("volumes", [])
    origens = [str(v).split(":")[0] for v in volumes]

    assert origens and all(o.startswith("/") for o in origens), (
        f"backup fora de bind mount absoluto — sob o Coolify ele morre com o projeto: {volumes}"
    )


def test_dump_so_ganha_nome_final_depois_de_verificado():
    """Arquivo pela metade com nome de backup bom é pior que nenhum: engana na hora do restore."""
    script = _servicos()["db-backup"]["command"][0]
    dump, verifica, renomeia = (script.index(t) for t in ("pg_dump", "pg_restore --list", "mv "))

    assert dump < verifica < renomeia, (
        "o dump precisa ir para nome temporário, passar no pg_restore --list e só então "
        "ser renomeado"
    )
    assert "set -e" in script, "sem set -e, uma falha no meio ainda sai 0 e libera o db-init"
