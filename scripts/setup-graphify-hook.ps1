# ============================================================================
# Graphify Git Hook Setup Script
# ============================================================================

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet('install', 'uninstall', 'status', 'enable', 'disable')]
    [string]$Action = 'status'
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$HookPath = Join-Path $RepoRoot ".git\hooks\post-commit"
$HookDisabledPath = "$HookPath.disabled"

$HookTemplate = @"
#!/bin/sh
code_changed=`$(git diff-tree --no-commit-id --name-only -r HEAD | grep -E '\.(py|ts|tsx|js|jsx|vue)`$')

if [ -n "`$code_changed" ]; then
    echo "🔄 Atualizando Graphify..."
    if ! command -v graphify &> /dev/null; then
        echo "⚠️  Graphify não encontrado"
        exit 0
    fi
    graphify update > /dev/null 2>&1
    if [ `$? -eq 0 ]; then
        echo "✅ Graphify atualizado"
    fi
fi
exit 0
"@

function Show-Status {
    Write-Host ""
    Write-Host "📊 Status do Graphify Hook" -ForegroundColor Cyan
    Write-Host ("=" * 50)
    
    if (Test-Path $HookPath) {
        Write-Host "✅ Hook ATIVO" -ForegroundColor Green
    }
    elseif (Test-Path $HookDisabledPath) {
        Write-Host "⏸️  Hook DESABILITADO" -ForegroundColor Yellow
    }
    else {
        Write-Host "❌ Hook NÃO INSTALADO" -ForegroundColor Red
    }
    
    Write-Host ""
    Write-Host "📁 Localização: $HookPath" -ForegroundColor Gray
    Write-Host ("=" * 50)
}

function Install-Hook {
    Write-Host ""
    Write-Host "🔧 Instalando Graphify Hook..." -ForegroundColor Cyan
    
    if (Test-Path $HookPath) {
        $backup = "$HookPath.backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
        Copy-Item $HookPath $backup
        Write-Host "📦 Backup criado: $backup" -ForegroundColor Gray
    }
    
    $hooksDir = Split-Path $HookPath
    if (-not (Test-Path $hooksDir)) {
        New-Item -ItemType Directory -Path $hooksDir -Force | Out-Null
    }
    
    Set-Content -Path $HookPath -Value $HookTemplate -Encoding UTF8
    
    Write-Host "✅ Hook instalado!" -ForegroundColor Green
    Write-Host ""
}

function Uninstall-Hook {
    Write-Host ""
    Write-Host "🗑️  Desinstalando..." -ForegroundColor Cyan
    
    if (Test-Path $HookPath) {
        Remove-Item $HookPath -Force
        Write-Host "✅ Hook removido!" -ForegroundColor Green
    }
    elseif (Test-Path $HookDisabledPath) {
        Remove-Item $HookDisabledPath -Force
        Write-Host "✅ Hook removido!" -ForegroundColor Green
    }
    else {
        Write-Host "ℹ️  Nenhum hook encontrado" -ForegroundColor Gray
    }
    Write-Host ""
}

function Enable-Hook {
    Write-Host ""
    Write-Host "▶️  Ativando..." -ForegroundColor Cyan
    
    if (Test-Path $HookDisabledPath) {
        Move-Item $HookDisabledPath $HookPath -Force
        Write-Host "✅ Hook reativado!" -ForegroundColor Green
    }
    elseif (Test-Path $HookPath) {
        Write-Host "ℹ️  Hook já está ativo" -ForegroundColor Gray
    }
    else {
        Write-Host "❌ Hook não encontrado. Use 'install' primeiro" -ForegroundColor Red
    }
    Write-Host ""
}

function Disable-Hook {
    Write-Host ""
    Write-Host "⏸️  Desabilitando..." -ForegroundColor Cyan
    
    if (Test-Path $HookPath) {
        Move-Item $HookPath $HookDisabledPath -Force
        Write-Host "✅ Hook desabilitado!" -ForegroundColor Green
    }
    elseif (Test-Path $HookDisabledPath) {
        Write-Host "ℹ️  Hook já está desabilitado" -ForegroundColor Gray
    }
    else {
        Write-Host "❌ Hook não encontrado. Use 'install' primeiro" -ForegroundColor Red
    }
    Write-Host ""
}

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   Graphify Git Hook - Setup Manager           ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════╝" -ForegroundColor Cyan

switch ($Action) {
    'install' { Install-Hook; Show-Status }
    'uninstall' { Uninstall-Hook; Show-Status }
    'enable' { Enable-Hook; Show-Status }
    'disable' { Disable-Hook; Show-Status }
    'status' {
        Show-Status
        Write-Host ""
        Write-Host "💡 Comandos:" -ForegroundColor Yellow
        Write-Host "   install, uninstall, enable, disable, status" -ForegroundColor Gray
        Write-Host ""
    }
}
