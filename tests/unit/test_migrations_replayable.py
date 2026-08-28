"""Every service's Alembic chain must build its schema from an empty database.

Production predates Alembic: every schema was stamped, so `alembic upgrade head`
is a no-op there and no boot ever replayed the chain. The bugs only surfaced on
a fresh database — a `docker-compose down -v`, or a new VPS:

- vendas created `historico_status_venda` in two revisions, so the second one
  died on DuplicateTable and took the container down with it;
- estoque's first revision created all five tables with no `schema=`, so they
  landed in `public` and the next revision's ALTER on `estoque.*` found nothing;
- clientes and produtos started from an ALTER on tables no revision ever created.

This guards the class, not the three bugs.
"""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

REVISION = re.compile(r"^revision(?::\s*str)?\s*=\s*['\"]([^'\"]+)['\"]", re.M)
DOWN_REVISION = re.compile(
    r"^down_revision(?::\s*[^=]+)?\s*=\s*(?:['\"]([^'\"]+)['\"]|None)", re.M
)
CREATE_TABLE = re.compile(r"op\.create_table\(\s*['\"]([a-z_]+)['\"]")
SCHEMALESS = re.compile(r"op\.(create_table|create_index)\(")


def _versions_dirs():
    """Every service that ships Alembic revisions, as (name, list-of-files)."""
    for alembic_dir in sorted(REPO.glob("*/alembic")) + sorted(REPO.glob("services/*/alembic")):
        files = [p for p in sorted(alembic_dir.glob("versions/*.py")) if p.stem != "__init__"]
        if files:
            yield alembic_dir.parent.name, files


def _balanced_call(source: str, open_paren: int) -> str:
    """The text of the call whose opening parenthesis sits at `open_paren`."""
    depth, i = 1, open_paren + 1
    while i < len(source) and depth:
        depth += (source[i] == "(") - (source[i] == ")")
        i += 1
    return source[open_paren:i]


def test_every_service_has_exactly_one_head():
    """A chain with two roots or a dangling parent cannot be upgraded at all."""
    for service, files in _versions_dirs():
        revisions, parents = set(), []
        for path in files:
            source = path.read_text(encoding="utf-8")
            revisions.add(REVISION.search(source).group(1))
            parents.append(DOWN_REVISION.search(source).group(1))

        roots = [p for p in parents if p is None]
        assert len(roots) == 1, f"{service}: {len(roots)} revisions with down_revision = None"

        dangling = sorted({p for p in parents if p and p not in revisions})
        assert not dangling, f"{service}: down_revision points at missing {dangling}"

        heads = revisions - {p for p in parents if p}
        assert len(heads) == 1, f"{service}: multiple heads {sorted(heads)}"


def test_no_table_is_created_twice():
    """Two revisions creating the same table means DuplicateTable on a fresh database."""
    for service, files in _versions_dirs():
        created = {}
        for path in files:
            for table in CREATE_TABLE.findall(path.read_text(encoding="utf-8")):
                created.setdefault(table, []).append(path.name)

        duplicated = {t: f for t, f in created.items() if len(f) > 1}
        assert not duplicated, f"{service}: created more than once -> {duplicated}"


def test_every_created_object_names_its_schema():
    """Without schema=, DDL lands in public — the service then queries an empty schema."""
    for service, files in _versions_dirs():
        offenders = []
        for path in files:
            source = path.read_text(encoding="utf-8")
            for match in SCHEMALESS.finditer(source):
                call = _balanced_call(source, match.end() - 1)
                if "schema=" not in call:
                    line = source[: match.start()].count("\n") + 1
                    offenders.append(f"{path.name}:{line} op.{match.group(1)}")

        assert not offenders, f"{service}: missing schema= -> {offenders}"
