#!/usr/bin/env bash
# Roda NA VPS antes de destruir qualquer coisa.
# Gera /tmp/resgate-vps.tar.gz com tudo que não está no git.
set -euo pipefail
OUT=/tmp/resgate; rm -rf "$OUT"; mkdir -p "$OUT"

# 1. Inventário: o que está rodando, de onde veio, quais volumes/redes existem
docker ps -a --format '{{.Names}}\t{{.Image}}\t{{.Status}}'          > "$OUT/containers.txt"
docker volume ls                                                     > "$OUT/volumes.txt"
docker network ls                                                    > "$OUT/networks.txt"
# working_dir + config file de cada stack compose ativo — revela QUAL compose subiu o banco
docker ps -a --format '{{.Label "com.docker.compose.project.working_dir"}}\t{{.Label "com.docker.compose.project.config_files"}}' \
  | sort -u                                                          > "$OUT/stacks.txt"

# 2. Arquivos que não estão no git
for f in nginx .env docker-compose*.yml cloudflared-config.yml; do
  cp -r "$f" "$OUT/" 2>/dev/null || echo "ausente: $f" >> "$OUT/faltando.txt"
done

# 3. Dump do banco — descubra o nome do container em containers.txt e ajuste
DB=$(docker ps --format '{{.Names}}' | grep -iE 'db|postgres' | head -1)
if [ -n "$DB" ]; then
  docker exec "$DB" pg_dumpall -U "${POSTGRES_USER:-erp}" > "$OUT/dump-completo.sql"
  echo "dump OK de $DB ($(wc -c < "$OUT/dump-completo.sql") bytes)"
else
  echo "AVISO: nenhum container de banco encontrado — confira containers.txt" >&2
fi

# 4. Certificados SSL (volume external, some se o volume for removido)
docker run --rm -v letsencrypt-certs:/certs:ro -v "$OUT":/out alpine \
  tar czf /out/letsencrypt.tar.gz -C /certs . 2>/dev/null || echo "sem volume letsencrypt-certs"

tar czf /tmp/resgate-vps.tar.gz -C /tmp resgate
echo "PRONTO: /tmp/resgate-vps.tar.gz — baixe com scp antes de destruir qualquer coisa."
