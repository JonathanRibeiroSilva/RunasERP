# Provisiona um novo lojista (tenant): empresa + usuario ADMIN.
#
# Wrapper de POST /plataforma/tenants. A logica (incluindo a compensacao quando o
# admin falha) vive no gateway, em api-gateway/routers/plataforma.py - este script
# so monta o payload. Nao existe mais o caminho antigo de bater direto nos
# containers em endpoints sem autenticacao; aquele era o furo que este endpoint fecha.
#
# Requer um token de SUPER_ADMIN. Obtenha com POST /auth/login usando as credenciais
# de SUPER_ADMIN_EMAIL / SUPER_ADMIN_PASSWORD.
#
# Uso:
#   .\scripts\provisionar-lojista.ps1 -Token "eyJ..." -RazaoSocial "Padaria X LTDA" `
#       -NomeFantasia "Padaria X" -Slug "padaria-x" -Cnpj "12.345.678/0001-90" `
#       -Email "dono@padariax.com" -Senha "Senha@123"
#
# Senha: 8-20 chars, com maiuscula, minuscula, numero e caractere especial.
param(
    [Parameter(Mandatory = $true)][string]$Token,
    [Parameter(Mandatory = $true)][string]$RazaoSocial,
    [Parameter(Mandatory = $true)][string]$NomeFantasia,
    [Parameter(Mandatory = $true)][string]$Slug,
    [Parameter(Mandatory = $true)][string]$Cnpj,        # formato XX.XXX.XXX/XXXX-XX
    [Parameter(Mandatory = $true)][string]$Email,
    [Parameter(Mandatory = $true)][string]$Senha,
    # Endereco (obrigatorio no cadastro; pode ser completado depois na plataforma)
    [string]$Cep = "00000-000",
    [string]$Logradouro = "A definir",
    [string]$Numero = "S/N",
    [string]$Bairro = "Centro",
    [string]$Cidade = "Sao Paulo",
    [string]$Uf = "SP",
    [string]$GatewayUrl = "http://localhost:8000"
)
$ErrorActionPreference = 'Stop'

$body = @{
    empresa = @{
        razao_social    = $RazaoSocial
        nome_fantasia   = $NomeFantasia
        slug            = $Slug
        cnpj            = $Cnpj
        email           = $Email
        catalogo_titulo = $NomeFantasia
        cep             = $Cep
        logradouro      = $Logradouro
        numero          = $Numero
        bairro          = $Bairro
        cidade          = $Cidade
        uf              = $Uf
    }
    admin = @{
        nome  = $NomeFantasia
        email = $Email
        senha = $Senha
    }
} | ConvertTo-Json -Depth 5

try {
    $r = Invoke-RestMethod -Uri "$GatewayUrl/plataforma/tenants" -Method POST -Body $body `
        -ContentType "application/json" -Headers @{ Authorization = "Bearer $Token" }
} catch {
    Write-Host "ERRO ao provisionar: $($_.ErrorDetails.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=== Lojista provisionado ===" -ForegroundColor Cyan
Write-Host "Empresa : $($r.empresa.razao_social) (id $($r.empresa.id))"
Write-Host "Slug    : $($r.empresa.slug)"
Write-Host "Admin   : $($r.admin.email)"
Write-Host "Loja    : DESABILITADA - habilitar em Configuracoes da Loja apos configurar"
