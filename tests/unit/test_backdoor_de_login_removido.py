"""O backdoor de login não volta.

Com `AUTH_BYPASS=true`, toda requisição sem token autenticava no gateway como
admin@runas.com, e o compose de dev ligava isso por padrão. Saiu em fdc7755
(`api-gateway/auth/oauth2.py` e `.env.example`), sem teste que afirmasse a
ausência.

A guarda é o nome da variável em qualquer arquivo versionado, sem diferenciar
maiúsculas: o pydantic-settings também não diferencia, então um campo
`auth_bypass` num config leria a mesma env. `git grep` só vê o que está
versionado — não abre `.env` real.
"""
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ESTE_ARQUIVO = Path(__file__).resolve().relative_to(REPO).as_posix()


def test_auth_bypass_nao_reaparece_no_repositorio():
    achados = subprocess.run(
        ["git", "grep", "-n", "-i", "auth_bypass", "--", ".", f":!{ESTE_ARQUIVO}"],
        cwd=REPO, capture_output=True, encoding="utf-8",
    )

    # git grep: 1 = nada achado; 0 = achou; acima disso, erro (sem git, fora do repo).
    assert achados.returncode == 1, achados.stdout or achados.stderr
