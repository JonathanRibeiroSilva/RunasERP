<#
  restore.ps1 — desfaz um reset da ferramenta de design.

  A ferramenta reescreve a raiz do projeto: ela recria index.html na versao
  original, devolve support.js / image-slot.js / glitter-warp.js para a raiz,
  restaura as fotos com o xadrez e apaga as pastas. Ja aconteceu uma vez.

  Este script usa o git como rede de seguranca: restaura tudo que e rastreado
  e lista o que a ferramenta recriou fora do lugar, para voce decidir.

  Uso:   powershell -ExecutionPolicy Bypass -File tools/restore.ps1
#>

$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')

if (-not (Test-Path '.git')) {
    Write-Host 'Sem repositorio git aqui — nao da para restaurar.' -ForegroundColor Red
    Write-Host 'Rode: git init; git add -A; git commit -m "estado bom"'
    exit 1
}

Write-Host '== Antes ==' -ForegroundColor Cyan
git status --short

Write-Host ''
Write-Host '== Restaurando arquivos rastreados ==' -ForegroundColor Cyan
git checkout -- .
Write-Host 'ok' -ForegroundColor Green

# Arquivos que a ferramenta costuma recriar na raiz e que agora vivem em assets/js
$intrusos = @('support.js', 'image-slot.js', 'glitter-warp.js') |
            Where-Object { Test-Path $_ }

$dcFiles = Get-ChildItem -File -Filter '*.dc.html' -ErrorAction SilentlyContinue

if ($intrusos -or $dcFiles) {
    Write-Host ''
    Write-Host '== A ferramenta recriou estes arquivos na raiz ==' -ForegroundColor Yellow
    $intrusos | ForEach-Object { Write-Host "   $_   (a copia boa esta em assets/js/)" }
    $dcFiles  | ForEach-Object { Write-Host "   $($_.Name)   (fonte da ferramenta; index.html e a versao refatorada)" }
    Write-Host ''
    Write-Host 'Confira se assets/js/ esta atualizado e entao apague os da raiz.' -ForegroundColor Yellow
    Write-Host 'Se o runtime mudou de versao, copie por cima:' -ForegroundColor Yellow
    Write-Host '   Move-Item -Force support.js, image-slot.js, glitter-warp.js assets/js/'
}

Write-Host ''
Write-Host '== Depois ==' -ForegroundColor Cyan
git status --short
Write-Host ''
Write-Host 'Pronto. Se as fotos voltaram com xadrez:' -ForegroundColor Cyan
Write-Host '   python tools/clean_products.py tools/originals assets/img/products'
