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
# Windows Git Hook - Chama PowerShell para executar a lógica
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "& {
    `$files = git diff-tree --no-commit-id --name-only -r HEAD
    `$codeChanged = `$files | Select-String -Pattern '\.(py|ts|tsx|js|jsx|vue)$'
    
    if (`$codeChanged) {
        Write-Host '🔄 Atualizando Graphify...' -ForegroundColor Yellow
        
        if (Get-Command graphify -ErrorAction SilentlyContinue) {
            graphify update > `$null 2>&1
            if (`$LASTEXITCODE -eq 0) {
                Write-Host '✅ Graphify atualizado' -ForegroundColor Green
            }
        } else {
            Write-Host '⚠️  Graphify não encontrado' -ForegroundColor Yellow
        }
    }
}"
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
    
    # No Windows, precisamos garantir que o Git pode executar o hook
    # Usar git update-index para marcar como executável
    try {
        git update-index --chmod=+x .git/hooks/post-commit 2>$null
    }
    catch {
        # Se falhar, não é crítico - o hook ainda pode funcionar
    }
    
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
