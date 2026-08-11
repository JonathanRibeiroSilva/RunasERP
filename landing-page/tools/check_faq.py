"""Confere se o FAQ do componente e o do JSON-LD continuam iguais.

As mesmas 6 perguntas vivem em dois lugares do index.html:

  - no `raw = [...]` do componente, que e o que a pagina mostra;
  - no JSON-LD (FAQPage) do <head> estatico, que e o que o Google le sem
    executar JavaScript.

A duplicacao e proposital (robo de rich result nao roda JS), mas silenciosa:
editar um lado e esquecer o outro nao quebra nada visivelmente, so publica
dado estruturado que nao corresponde a pagina. Este script pega isso.

    python tools/check_faq.py

Sai com codigo 1 se divergirem.
"""

import io
import json
import re
import sys
from pathlib import Path

HTML = Path(__file__).resolve().parent.parent / "index.html"


def faq_do_jsonld(src):
    bloco = re.search(
        r'<script type="application/ld\+json">(.*?)</script>', src, re.S
    )
    if not bloco:
        sys.exit("nao achei o bloco JSON-LD no <head>")
    try:
        dados = json.loads(bloco.group(1))
    except json.JSONDecodeError as e:
        sys.exit(f"JSON-LD invalido: {e}")
    for no in dados.get("@graph", []):
        if no.get("@type") == "FAQPage":
            return [
                (q["name"].strip(), q["acceptedAnswer"]["text"].strip())
                for q in no["mainEntity"]
            ]
    sys.exit("nao achei o no FAQPage dentro do @graph")


def faq_do_componente(src):
    # o array `raw` do renderVals; pega ate o `];` que o fecha
    bloco = re.search(r"const raw = \[(.*?)\n    \];", src, re.S)
    if not bloco:
        sys.exit("nao achei o array `raw` do componente")
    itens = re.findall(
        r"\{\s*q:\s*'((?:[^'\\]|\\.)*)',\s*a:\s*'((?:[^'\\]|\\.)*)'\s*\}",
        bloco.group(1),
    )
    return [(q.replace("\\'", "'").strip(), a.replace("\\'", "'").strip())
            for q, a in itens]


src = io.open(HTML, encoding="utf-8").read()
jsonld = faq_do_jsonld(src)
componente = faq_do_componente(src)

if not componente:
    sys.exit("nenhuma pergunta extraida do componente — o formato do array mudou?")

problemas = []
if len(jsonld) != len(componente):
    problemas.append(
        f"quantidade diferente: componente tem {len(componente)}, JSON-LD tem {len(jsonld)}"
    )

for i, (comp, ld) in enumerate(zip(componente, jsonld)):
    if comp[0] != ld[0]:
        problemas.append(f"[{i}] pergunta difere\n     componente: {comp[0]}\n     JSON-LD   : {ld[0]}")
    if comp[1] != ld[1]:
        problemas.append(f"[{i}] resposta difere\n     componente: {comp[1]}\n     JSON-LD   : {ld[1]}")

if problemas:
    print("FAQ fora de sincronia:\n")
    for p in problemas:
        print("  " + p)
    sys.exit(1)

print(f"FAQ em sincronia: {len(componente)} perguntas iguais nos dois lugares.")
