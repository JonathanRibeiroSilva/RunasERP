#!/usr/bin/env bash
# Mede o downtime REAL de um deploy: sonda produção de fora, 1x/s, e conta
# quantos segundos o site respondeu errado.
#
# O número que o CI reporta hoje (~2m26s) é o tempo que o Coolify levou para
# terminar, não o tempo que o visitante viu erro. Sem esta medição, qualquer
# melhoria vira "acho que melhorou".
#
#   ./medir-downtime.sh                 # sonda até Ctrl-C, imprime o resumo
#   ./medir-downtime.sh resumo x.csv    # reanalisa um csv já gravado
#   ./medir-downtime.sh teste           # autoteste do resumo
#
# Os dois alvos separam as camadas (nginx.conf: /api/ faz proxy pro gateway):
#   /health      -> túnel + container do frontend
#   /api/health  -> túnel + frontend + api-gateway  (o caminho real do usuário)
#
# Como ler os códigos:
#   200      ok
#   502/504  túnel de pé, container do frontend sumiu
#   530      cloudflared caiu (Cloudflare error 1033, não há origin registrado)
#   000      a sonda não conectou (rede local / DNS) — não é downtime do site
#   403      WAF respondeu no lugar do site: a amostra é MENTIRA, veja o UA
UA='Mozilla/5.0 (compatible; RunasProbe/1.0; +medir-downtime.sh)'
BASE="${BASE:-https://app.runaserp.com.br}"
ALVOS=("$BASE/health" "$BASE/api/health")
INTERVALO="${INTERVALO:-1}"
TIMEOUT="${TIMEOUT:-3}"

# -A não é enfeite: a zona tem uma regra de WAF ("User-Agent suspeito") que
# desafia qualquer UA com curl/wget e devolve 403 do próprio edge, sem tocar a
# VPS. Foi assim que o passo de verificação antigo do CI passou 5 minutos
# achando que estava sondando o site. Sem UA de navegador esta sonda mede o
# Cloudflare, não o ERP.

resumo() {
  local csv="$1"
  awk -F, -v OFS='' '
    function dur(a, b) { return sprintf("%ds", b - a) }
    function curto(a,  p) { p = a; sub(/^https?:\/\/[^\/]+/, "", p); return p }
    function fecha(alvo, fim_ts, fim_iso) {
      printf "  %-12s %s -> %s  (%s)  códigos: %s\n",
             curto(alvo), substr(ini_iso[alvo],12,8),
             substr(fim_iso,12,8), dur(ini[alvo], fim_ts), codigos[alvo]
      pior[alvo] = (fim_ts - ini[alvo] > pior[alvo]) ? fim_ts - ini[alvo] : pior[alvo]
      fora[alvo] += fim_ts - ini[alvo]
      aberta[alvo] = 0
    }
    NR == 1 { next }
    {
      ts = $1; iso = $2; alvo = $3; cod = $4
      if (!(alvo in total)) ordem[++n] = alvo
      total[alvo]++
      if (cod == 403) waf = 1
      if (cod == 200) {
        if (aberta[alvo]) fecha(alvo, ts, iso)
        next
      }
      ruins[alvo]++
      if (!aberta[alvo]) {
        aberta[alvo] = 1; ini[alvo] = ts; ini_iso[alvo] = iso; codigos[alvo] = ""
        if (!cab) { print "\nJanelas fora do ar:"; cab = 1 }
      }
      if (index(" " codigos[alvo], " " cod " ") == 0) codigos[alvo] = codigos[alvo] cod " "
      ult[alvo] = ts; ult_iso[alvo] = iso
    }
    END {
      for (i = 1; i <= n; i++) {
        alvo = ordem[i]
        if (aberta[alvo]) { fecha(alvo, ult[alvo], ult_iso[alvo]); print "    ^ ainda fora no fim da coleta" }
      }
      if (!cab) print "\nJanelas fora do ar: nenhuma."
      print "\nPor alvo:"
      for (i = 1; i <= n; i++) {
        alvo = ordem[i]
        printf "  %-46s %4d amostras  %3d ruins  fora %3ds  pior janela %3ds  disponibilidade %6.2f%%\n",
               alvo, total[alvo], ruins[alvo] + 0, fora[alvo] + 0, pior[alvo] + 0,
               100 * (total[alvo] - ruins[alvo]) / total[alvo]
      }
      if (waf) print "\n  !! apareceu 403: o WAF respondeu no lugar do site. Esta medição não vale."
    }
  ' "$csv"
}

case "${1:-sonda}" in
resumo)
  resumo "${2:?uso: $0 resumo arquivo.csv}"
  ;;

teste)
  # Falha se o agrupamento de janelas quebrar. Queda conhecida: 10:00:03 ->
  # 10:00:08 = 5s, com 502 e 530 no meio.
  t=$(mktemp); trap 'rm -f "$t"' EXIT
  {
    echo "epoch,iso,alvo,codigo,tempo_s"
    for i in 0 1 2 3 4 5 6 7 8; do
      cod=200
      [ "$i" -ge 3 ] && [ "$i" -le 7 ] && cod=502
      [ "$i" -eq 5 ] && cod=530
      printf '%d,2026-01-01T10:00:%02d-03:00,https://x/health,%s,0.1\n' "$((1767268800 + i))" "$i" "$cod"
    done
  } > "$t"
  saida="$(resumo "$t")"
  echo "$saida"
  echo "$saida" | grep -q '10:00:03 -> 10:00:08  (5s)' || { echo "FALHOU: janela errada"; exit 1; }
  echo "$saida" | grep -q 'códigos: 502 530' || { echo "FALHOU: códigos errados"; exit 1; }
  echo "$saida" | grep -q '9 amostras    5 ruins  fora   5s' || { echo "FALHOU: totais errados"; exit 1; }
  echo "OK"
  ;;

sonda)
  CSV="${2:-downtime-$(date +%Y%m%d-%H%M%S).csv}"
  echo "epoch,iso,alvo,codigo,tempo_s" > "$CSV"
  echo "sondando $BASE a cada ${INTERVALO}s -> $CSV   (Ctrl-C para o resumo)"
  trap 'resumo "$CSV"; echo; echo "csv: $CSV"; exit 0' INT TERM
  # Os alvos vão em paralelo: em série, um alvo que trava segura o outro e a
  # cadência real vira 2s — resolução ruim demais para uma janela de 2 minutos
  # que queremos ver encolher.
  amostra() {
    local alvo="$1"
    # curl escreve o -w mesmo quando falha em conectar: código 000.
    set -- $(curl -s -o /dev/null -A "$UA" --max-time "$TIMEOUT" -w '%{http_code} %{time_total}' "$alvo")
    printf '%s,%s,%s,%s,%s\n' "$(date +%s)" "$(date -Iseconds)" "$alvo" "${1:-000}" "${2:-0}" >> "$CSV"
    [ "${1:-000}" = 200 ] || echo "  $(date +%H:%M:%S) ${1:-000} $alvo"
  }
  while :; do
    for alvo in "${ALVOS[@]}"; do amostra "$alvo" & done
    wait
    sleep "$INTERVALO"
  done
  ;;
*)
  sed -n '2,25p' "$0"; exit 1
  ;;
esac
