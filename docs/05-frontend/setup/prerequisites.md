# Pré-requisitos para Testar Autenticação Frontend

**Data:** 2026-05-25  
**Versão:** 1.0.0

---

## ✅ Checklist de Pré-requisitos

### Docker (Recomendado)

- [x] Windows 10/11 (seu sistema)
- [ ] Docker Desktop instalado
- [ ] Docker Compose instalado
- [ ] Acesso de administrador (para instalar)

**Se não estiver instalado:**
1. Acesse https://www.docker.com/products/docker-desktop
2. Baixe Docker Desktop para Windows
3. Execute o instalador
4. Reinicie o computador

**Vantagens:**
- ✅ Não precisa instalar dependências manualmente
- ✅ Ambiente isolado e consistente
- ✅ Fácil de compartilhar com o time
- ✅ Pronto para produção

### Node.js e npm (Alternativa)

**Verificar instalação:**
```bash
node --version
npm --version
```

**Versões recomendadas:**
- Node.js: v18.0.0 ou superior
- npm: v9.0.0 ou superior

**Se não estiver instalado:**
1. Acesse https://nodejs.org/
2. Baixe a versão LTS
3. Execute o instalador
4. Reinicie o terminal

### Python (Se não usar Docker)

**Verificar instalação:**
```bash
python --version
pip --version
```

**Versões recomendadas:**
- Python: 3.9 ou superior
- pip: 21.0 ou superior

**Se não estiver instalado:**
1. Acesse https://www.python.org/
2. Baixe a versão 3.11 ou superior
3. Execute o instalador
4. Marque "Add Python to PATH"
5. Reinicie o terminal

---

## 📁 Estrutura do Projeto

Verifique se a estrutura está correta:

```
c:\Users\jonat\Documents\GitHub\ERP\RunasERP\
├── api-gateway/          ✅ Backend
│   ├── main.py
│   ├── requirements.txt
│   └── ...
├── frontend/             ✅ Frontend
│   ├── src/
│   ├── package.json
│   └── ...
├── docs/                 ✅ Documentação
│   ├── frontend/
│   │   ├── OAUTH-SETUP.md
│   │   ├── QUICK-TEST-GUIDE.md
│   │   └── ...
│   └── ...
├── docker-compose.yml
├── docker-compose.dev.yml
└── ...
```

---

## 🔧 Configuração de Variáveis de Ambiente

### Frontend (.env.development)

Localização: `frontend/.env.development`

**Conteúdo mínimo:**
```env
VITE_API_URL=http://localhost:8000
VITE_OAUTH_REDIRECT_URI=http://localhost:3000/auth/callback

# Opcional (se tiver credenciais OAuth)
VITE_GOOGLE_CLIENT_ID=seu-client-id.apps.googleusercontent.com
VITE_MICROSOFT_CLIENT_ID=seu-client-id
VITE_MICROSOFT_TENANT_ID=common
```

**Verificar:**
```bash
cd frontend
cat .env.development
```

### Backend (.env)

Localização: `api-gateway/.env`

**Conteúdo mínimo:**
```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/erp_runas

# JWT
SECRET_KEY=sua-chave-secreta-aqui
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# OAuth (opcional)
GOOGLE_CLIENT_ID=seu-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=seu-client-secret
MICROSOFT_CLIENT_ID=seu-client-id
MICROSOFT_CLIENT_SECRET=seu-client-secret
MICROSOFT_TENANT_ID=common
```

**Verificar:**
```bash
cd api-gateway
cat .env
```

---

## 🗄️ Banco de Dados

### Com Docker (Recomendado)

O banco de dados é iniciado automaticamente com:
```bash
docker-compose -f docker-compose.dev.yml up
```

### Sem Docker

**Instalar PostgreSQL:**
1. Acesse https://www.postgresql.org/download/windows/
2. Baixe o instalador
3. Execute e siga as instruções
4. Anote a senha do usuário `postgres`

**Criar banco de dados:**
```bash
# Conectar ao PostgreSQL
psql -U postgres

# Criar banco
CREATE DATABASE erp_runas;

# Sair
\q
```

**Configurar .env:**
```env
DATABASE_URL=postgresql://postgres:sua-senha@localhost:5432/erp_runas
```

---

## 🔐 Credenciais de Teste

### Login Tradicional

Credenciais padrão (já criadas no banco):
```
Email: admin@runas.com
Senha: Admin@123
```

### OAuth (Opcional)

Para testar OAuth, você precisa de credenciais do Google e/ou Microsoft.

**Google:**
1. Acesse https://console.cloud.google.com/
2. Crie um novo projeto
3. Habilite Google+ API
4. Crie credenciais OAuth
5. Copie o Client ID

**Microsoft:**
1. Acesse https://portal.azure.com/
2. Vá em Azure Active Directory > App registrations
3. Crie um novo app
4. Copie o Client ID

Consulte [OAUTH-SETUP.md](./OAUTH-SETUP.md) para instruções detalhadas.

---

## 🚀 Verificação Final

Execute este script para verificar se tudo está configurado:

**Com Docker (Recomendado):**
```bash
# Verificar Docker
echo "Docker:"
docker --version

# Verificar Docker Compose
echo "Docker Compose:"
docker-compose --version

# Verificar estrutura do projeto
echo "Estrutura do projeto:"
ls -la c:\Users\jonat\Documents\GitHub\ERP\RunasERP\

# Verificar .env do frontend
echo ".env do frontend:"
cat c:\Users\jonat\Documents\GitHub\ERP\RunasERP\frontend\.env.development

# Verificar .env do backend
echo ".env do backend:"
cat c:\Users\jonat\Documents\GitHub\ERP\RunasERP\api-gateway\.env
```

**Sem Docker:**
```bash
# Verificar Node.js
echo "Node.js:"
node --version

# Verificar npm
echo "npm:"
npm --version

# Verificar Python
echo "Python:"
python --version

# Verificar Git
echo "Git:"
git --version

# Verificar estrutura do projeto
echo "Estrutura do projeto:"
ls -la c:\Users\jonat\Documents\GitHub\ERP\RunasERP\

# Verificar .env do frontend
echo ".env do frontend:"
cat c:\Users\jonat\Documents\GitHub\ERP\RunasERP\frontend\.env.development

# Verificar .env do backend
echo ".env do backend:"
cat c:\Users\jonat\Documents\GitHub\ERP\RunasERP\api-gateway\.env
```

---

## 📋 Checklist Final

Antes de começar os testes, verifique:

### Docker (Recomendado)
- [ ] Docker Desktop instalado
- [ ] Docker Compose instalado
- [ ] Estrutura do projeto correta
- [ ] `.env.development` do frontend configurado
- [ ] `.env` do backend configurado

### Node.js (Alternativa)
- [ ] Node.js v18+ instalado
- [ ] npm v9+ instalado
- [ ] Estrutura do projeto correta
- [ ] `.env.development` do frontend configurado
- [ ] `.env` do backend configurado

### Configuração Geral
- [ ] Banco de dados criado (ou será criado pelo Docker)
- [ ] Credenciais de teste (admin@runas.com / Admin@123)
- [ ] Credenciais OAuth (opcional)
- [ ] Repositório clonado/atualizado
- [ ] Branch correto (main)
- [ ] Sem conflitos de merge

---

## 🆘 Problemas Comuns

### "docker: command not found"
```bash
# Solução: Docker não está instalado ou não está no PATH
# Reinstale Docker Desktop e reinicie o terminal
```

### "docker-compose: command not found"
```bash
# Solução: Docker Compose não está instalado
# Reinstale Docker Desktop (inclui Compose) e reinicie o terminal
```

### "node: command not found"
```bash
# Solução: Node.js não está instalado ou não está no PATH
# Reinstale Node.js e reinicie o terminal
```

### "npm: command not found"
```bash
# Solução: npm não está instalado ou não está no PATH
# Reinstale Node.js (npm vem junto) e reinicie o terminal
```

### "python: command not found"
```bash
# Solução: Python não está instalado ou não está no PATH
# Reinstale Python e marque "Add Python to PATH"
```

### "Permission denied"
```bash
# Solução: Falta de permissões
# Execute o terminal como administrador
```

### "Port already in use"
```bash
# Solução: Porta 3000 ou 8000 já está em uso
# Feche outros aplicativos ou use portas diferentes
```

### "Cannot connect to Docker daemon"
```bash
# Solução: Docker não está rodando
# Abra Docker Desktop e aguarde inicializar
```

---

## 📞 Próximos Passos

Após verificar todos os pré-requisitos:

1. ✅ Leia [QUICK-TEST-GUIDE.md](./QUICK-TEST-GUIDE.md)
2. ✅ Siga as instruções de início rápido
3. ✅ Execute os testes básicos
4. ✅ Reporte qualquer problema

---

**Última Atualização:** 2026-05-25  
**Versão:** 1.0.0
