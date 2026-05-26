# Guia de Instalação - Frontend ERP Runas

## ⚠️ Pré-requisito: Node.js

O Node.js **não está instalado** no seu sistema. Você precisa instalá-lo antes de executar o frontend.

---

## 📥 Instalar Node.js

### Opção 1: Download Oficial (Recomendado)

1. Acesse: https://nodejs.org/
2. Baixe a versão **LTS** (Long Term Support) - atualmente 18.x ou superior
3. Execute o instalador
4. Siga as instruções do instalador (deixe as opções padrão marcadas)
5. Reinicie o terminal/PowerShell após a instalação

### Opção 2: Usando Chocolatey (Windows)

Se você tem o Chocolatey instalado:

```powershell
choco install nodejs-lts
```

### Opção 3: Usando Winget (Windows 10/11)

```powershell
winget install OpenJS.NodeJS.LTS
```

---

## ✅ Verificar Instalação

Após instalar, abra um **novo** terminal/PowerShell e execute:

```bash
node --version
```

Deve retornar algo como: `v18.x.x` ou superior

```bash
npm --version
```

Deve retornar algo como: `9.x.x` ou superior

---

## 🚀 Executar o Frontend

Após instalar o Node.js:

### 1. Navegar para a pasta do frontend

```bash
cd c:\Users\jonat\Documents\GitHub\ERP\RunasERP\frontend
```

### 2. Instalar dependências

```bash
npm install
```

Este comando irá:
- Baixar todas as dependências do projeto
- Criar a pasta `node_modules`
- Pode levar alguns minutos na primeira vez

### 3. Executar em modo desenvolvimento

```bash
npm run dev
```

### 4. Acessar a aplicação

Abra o navegador em: **http://localhost:3000**

---

## 🔐 Login

Use as credenciais de teste:

```
Email: admin@runas.com
Senha: Admin@123
```

---

## 📝 Scripts Disponíveis

Após a instalação, você pode usar:

```bash
# Desenvolvimento
npm run dev

# Build para produção
npm run build

# Preview do build
npm run preview

# Linting
npm run lint

# Formatação
npm run format

# Testes
npm run test
```

---

## 🐛 Problemas Comuns

### "npm não é reconhecido"

**Solução:** Reinicie o terminal/PowerShell após instalar o Node.js

### "Erro ao instalar dependências"

**Solução:** 
1. Delete a pasta `node_modules` (se existir)
2. Delete o arquivo `package-lock.json` (se existir)
3. Execute `npm install` novamente

### "Porta 3000 já está em uso"

**Solução:** 
- Feche outros aplicativos que possam estar usando a porta 3000
- Ou edite `vite.config.ts` para usar outra porta

### "Backend não está respondendo"

**Solução:**
- Verifique se o backend está rodando na porta 8000
- Acesse http://localhost:8000/docs para confirmar

---

## 📚 Documentação

Para mais informações, consulte:

- **README.md** - Visão geral do projeto
- **docs/frontend/STATUS.md** - Status da implementação
- **docs/frontend/IMPLEMENTATION-LOG.md** - Log detalhado
- **docs/frontend/DESIGN-SYSTEM.md** - Sistema de design

---

## 🆘 Suporte

Se encontrar problemas:

1. Verifique se o Node.js está instalado corretamente
2. Verifique se o backend está rodando
3. Consulte a documentação em `docs/frontend/`
4. Verifique os logs de erro no terminal

---

**Boa sorte! 🚀**
