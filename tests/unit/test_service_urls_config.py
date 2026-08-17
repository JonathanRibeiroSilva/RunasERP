"""Service-to-service URLs must come from settings, and prod must define them.

The storefront cart answered 500 in production for weeks: utils/tenant.py had
`http://empresas:8007` baked in, which resolves in dev (container `empresas`)
and nowhere else (prod containers are `*-prod`). Health checks stayed green —
only /loja/* broke. This guards the class, not the one line.
"""
import re
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
HOSTNAME_LITERAL = re.compile(r"https?://(?!localhost)[a-z][a-z0-9-]*:[0-9]{4}")


def test_no_service_hostname_hardcoded_outside_config():
    """Only config.py may name another container; everything else reads settings."""
    offenders = [
        f"{path.relative_to(REPO)}:{n}"
        for path in REPO.glob("services/*/**/*.py")
        if path.name != "config.py" and "tests" not in path.parts
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if HOSTNAME_LITERAL.search(line)
    ]
    assert not offenders, f"hardcoded service URLs (use settings.*_URL): {offenders}"


def _urls_used_in_code(service: str) -> set:
    return {
        name
        for path in (REPO / "services" / service).rglob("*.py")
        if "tests" not in path.parts and path.name != "config.py"
        for name in re.findall(r"settings\.(\w+_URL)", path.read_text(encoding="utf-8"))
    }


def test_prod_compose_overrides_every_dev_default_url_the_service_calls():
    """A *_URL default in config.py is a dev container name — prod must override it."""
    compose = yaml.safe_load((REPO / "docker-compose.prod.yml").read_text(encoding="utf-8"))
    missing = []
    for config in REPO.glob("services/*/config.py"):
        service = config.parent.name
        env = compose["services"].get(f"{service}-prod", {}).get("environment", {})
        dev_defaults = set(re.findall(r"^\s*(\w+_URL): str = \"http://[a-z]", config.read_text(encoding="utf-8"), re.M))
        missing += [f"{service}-prod: {n}" for n in sorted(dev_defaults & _urls_used_in_code(service)) if n not in env]
    assert not missing, f"prod compose misses URL overrides: {missing}"
