# Publica a landing no Cloudflare Pages (projeto runas-landing).
#
# Sobe de uma cópia limpa porque `wrangler pages deploy` manda TUDO o que está
# na pasta — README.md, tools/ e .design/ inclusive. `.assetsignore` não é lido
# nesse comando. O .design/source/index.original.html é a página inteira
# duplicada: indexado, vira duplicate content.
#
# .image-slots.state.json VAI junto: image-slot.js faz fetch() dele em runtime
# (STATE_FILE, assets/js/image-slot.js). É onde vivem a capa e o avatar da loja,
# que são base64 e não têm atributo src. Sem ele, os dois slots renderizam o
# placeholder tracejado de "solte uma imagem" em produção.
#
# Uso: powershell -ExecutionPolicy Bypass -File tools/deploy.ps1

$ErrorActionPreference = "Stop"
$src = Split-Path $PSScriptRoot -Parent
$stage = Join-Path $env:TEMP "runas-landing-stage"

Remove-Item -Recurse -Force $stage -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force $stage | Out-Null
Copy-Item (Join-Path $src "index.html") $stage
Copy-Item (Join-Path $src ".image-slots.state.json") $stage
Copy-Item (Join-Path $src "assets") $stage -Recurse

npx wrangler pages deploy $stage --project-name runas-landing --branch main --commit-dirty=true
