# Provisiona um novo lojista (tenant): empresa + usuario ADMIN, em sequencia com compensacao.
#
# A loja nasce DESABILITADA (catalogo_ativo = false): o lojista configura tudo em
# Configuracoes da Loja e habilita quando quiser. Este script e o caminho oficial de
# provisionamento ate existir o painel administrativo (SUPER_ADMIN) - a logica daqui
# vira o endpoint que o painel chamara.
#
# Uso:
#   .\scripts\provisionar-lojista.ps1 -RazaoSocial "Padaria X LTDA" -NomeFantasia "Padaria X" `
#       -Slug "padaria-x" -Cnpj "12.345.678/0001-90" -Email "dono@padariax.com" -Senha "Senha@123"
#
# Senha: 8-20 chars, com maiuscula, minuscula, numero e caractere especial.
param(
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
    [string]$EmpresasUrl = "http://localhost:8007",
    [string]$GatewayUrl = "http://localhost:8000"
)
$ErrorActionPreference = 'Stop'

# 1. Criar a empresa (loja nasce desabilitada)
$empresaBody = @{
    razao_social    = $RazaoSocial
    nome_fantasia   = $NomeFantasia
    slug            = $Slug
    cnpj            = $Cnpj
    email           = $Email
    catalogo_ativo  = $false
    catalogo_titulo = $NomeFantasia
    cep             = $Cep
    logradouro      = $Logradouro
    numero          = $Numero
    bairro          = $Bairro
    cidade          = $Cidade
    uf              = $Uf
} | ConvertTo-Json

try {
    $empresa = Invoke-RestMethod -Uri "$EmpresasUrl/empresas" -Method POST -Body $empresaBody -ContentType "application/json"
} catch {
    Write-Host "ERRO ao criar empresa: $($_.ErrorDetails.Message)" -ForegroundColor Red
    exit 1
}
Write-Host "Empresa criada: id=$($empresa.id) slug=$($empresa.slug)" -ForegroundColor Green

# 2. Criar o usuario ADMIN vinculado a empresa
$usuarioBody = @{
    nome       = $NomeFantasia
    email      = $Email
    senha      = $Senha
    role       = "ADMIN"
    empresa_id = $empresa.id
} | ConvertTo-Json

try {
    $usuario = Invoke-RestMethod -Uri "$GatewayUrl/auth/register" -Method POST -Body $usuarioBody -ContentType "application/json"
} catch {
    # Compensacao: nao deixar tenant orfao (empresa sem admin)
    Write-Host "ERRO ao criar usuario ADMIN: $($_.ErrorDetails.Message)" -ForegroundColor Red
    Write-Host "Compensando: removendo empresa $($empresa.id)..." -ForegroundColor Yellow
    try {
        # X-Empresa-Id: o servico exige o header de tenant tambem no acesso direto (fail closed)
        Invoke-RestMethod -Uri "$EmpresasUrl/empresas/$($empresa.id)" -Method DELETE -Headers @{ "X-Empresa-Id" = "$($empresa.id)" } | Out-Null
        Write-Host "Empresa removida. Nenhum tenant orfao." -ForegroundColor Yellow
    } catch {
        Write-Host "ATENCAO: falha ao remover empresa $($empresa.id) - remover manualmente." -ForegroundColor Red
    }
    exit 1
}

Write-Host ""
Write-Host "=== Lojista provisionado ===" -ForegroundColor Cyan
Write-Host "Empresa : $($empresa.razao_social) (id $($empresa.id))"
Write-Host "Slug    : $($empresa.slug)"
Write-Host "Admin   : $($usuario.email) (role $($usuario.role))"
Write-Host "Loja    : DESABILITADA - habilitar em Configuracoes da Loja apos configurar"
