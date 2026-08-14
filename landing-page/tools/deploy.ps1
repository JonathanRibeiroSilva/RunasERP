# Publica a landing no Cloudflare Pages (projeto runas-landing).
#
# Sobe de uma cópia limpa porque `wrangler pages deploy` manda TUDO o que está
# na pasta — README.md, tools/, .design/ e .image-slots.state.json inclusive.
# `.assetsignore` não é lido nesse comando. O .design/source/index.original.html
# é a página inteira duplicada: indexado, vira duplicate content.
#
# Uso: powershell -ExecutionPolicy Bypass -File tools/deploy.ps1

$ErrorActionPreference = "Stop"
$src = Split-Path $PSScriptRoot -Parent
$stage = Join-Path $env:TEMP "runas-landing-stage"

Remove-Item -Recurse -Force $stage -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force $stage | Out-Null
Copy-Item (Join-Path $src "index.html") $stage
Copy-Item (Join-Path $src "assets") $stage -Recurse

npx wrangler pages deploy $stage --project-name runas-landing --branch main --commit-dirty=true
