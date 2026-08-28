# -*- coding: utf-8 -*-
"""Confere a escala fluida de main.css.

Um clamp() errado nao quebra nada visivel: a pagina continua carregando, o texto
so fica no tamanho errado. Este check resolve cada `--fs-*` nas duas pontas da
faixa (360px e 1440px de viewport) e compara com a tabela documentada no proprio
CSS, alem de garantir que nenhuma fonte de CONTEUDO caia abaixo de 13px.

    python tools/check_type_scale.py
"""
import io
import os
import re
import sys

CSS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "css", "main.css")

# token -> (px em 360px de viewport, px em 1440px)  — a tabela do comentario
ESPERADO = {
    "--fs-xs":    (13.0, 14.0),
    "--fs-sm":    (14.5, 15.5),
    "--fs-base":  (15.5, 17.0),
    "--fs-md":    (16.5, 18.0),
    "--fs-h3":    (17.0, 19.5),
    "--fs-lead":  (17.0, 21.0),
    "--fs-h2":    (29.0, 46.0),
    "--fs-h2-lg": (31.0, 54.0),
    "--fs-h1":    (36.0, 72.0),
}

# piso de legibilidade: nada que a pessoa precise LER pode ficar menor que isto
# no celular. Os mocks (dashboard e cartao da loja) sao reproducoes reduzidas da
# tela do app — texto de figura, nao de leitura — e ficam de fora.
PISO_PX = 13.0

CLAMP = re.compile(
    r"--(fs-[a-z0-9-]+):\s*clamp\(\s*([\d.]+)rem\s*,\s*"
    r"([\d.]+)rem\s*\+\s*([\d.]+)vw\s*,\s*([\d.]+)rem\s*\)"
)


def resolve(base_rem, slope_vw, minimo, maximo, viewport_px):
    """Mesmo calculo do navegador: clamp(min, base + slope*vw, max), em px."""
    fluido = base_rem * 16 + slope_vw * viewport_px / 100.0
    return max(minimo * 16, min(fluido, maximo * 16))


def main():
    css = io.open(CSS, encoding="utf-8").read()

    achados = {}
    for m in CLAMP.finditer(css):
        nome, minimo, base, slope, maximo = m.group(1), *map(float, m.groups()[1:])
        achados["--" + nome] = (
            resolve(base, slope, minimo, maximo, 360),
            resolve(base, slope, minimo, maximo, 1440),
            resolve(base, slope, minimo, maximo, 320),   # telefone estreito
            resolve(base, slope, minimo, maximo, 2560),  # monitor grande
        )

    erros = []

    faltando = set(ESPERADO) - set(achados)
    if faltando:
        erros.append("tokens ausentes ou fora do formato clamp(rem + vw): %s"
                     % ", ".join(sorted(faltando)))

    for nome, (esp_min, esp_max) in sorted(ESPERADO.items()):
        if nome not in achados:
            continue
        p360, p1440, p320, p2560 = achados[nome]
        if abs(p360 - esp_min) > 0.15:
            erros.append("%s a 360px: %.2fpx, a tabela diz %.1fpx" % (nome, p360, esp_min))
        if abs(p1440 - esp_max) > 0.15:
            erros.append("%s a 1440px: %.2fpx, a tabela diz %.1fpx" % (nome, p1440, esp_max))
        # as pontas tem que TRAVAR: sem isso o clamp nao esta segurando nada
        if abs(p320 - p360) > 0.01:
            erros.append("%s nao trava embaixo: %.2fpx a 320 contra %.2fpx a 360"
                         % (nome, p320, p360))
        if abs(p2560 - p1440) > 0.01:
            erros.append("%s nao trava em cima: %.2fpx a 2560 contra %.2fpx a 1440"
                         % (nome, p2560, p1440))
        if p360 < PISO_PX - 0.01:
            erros.append("%s comeca em %.2fpx, abaixo do piso de %.0fpx"
                         % (nome, p360, PISO_PX))

    if erros:
        print("FALHOU:")
        for e in erros:
            print("  - " + e)
        return 1

    print("escala ok — %d tokens, todos travados entre 360px e 1440px:" % len(ESPERADO))
    for nome in ESPERADO:
        p360, p1440 = achados[nome][0], achados[nome][1]
        print("  %-11s %5.1fpx -> %5.1fpx" % (nome, p360, p1440))
    return 0


if __name__ == "__main__":
    sys.exit(main())
