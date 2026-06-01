# FAQ - Perguntas Frequentes

> **Respostas para dúvidas comuns** sobre o Runas

---

## 📋 Índice

- [Geral](#geral)
- [Instalação e Setup](#instalação-e-setup)
- [Funcionalidades](#funcionalidades)
- [Técnico](#técnico)
- [Segurança](#segurança)
- [Licenciamento](#licenciamento)

---

## 🎯 Geral

### O que é o Runas?

O Runas é um sistema de gestão empresarial (ERP) moderno e acessível, desenvolvido especificamente para pequenos comércios brasileiros. Ele oferece gestão completa de clientes, produtos, estoque, vendas e financeiro.

### Para quem o Runas é indicado?

O Runas é ideal para:
- Pequenos comércios de alimentos e bebidas
- Mercearias e minimercados
- Distribuidoras de pequeno porte
- Lojas de conveniência
- Negócios que trabalham com vendas fiadas

### Quanto custa o Runas?

O Runas é um projeto open-source. Você pode:
- **Self-hosted**: Hospedar gratuitamente em seu próprio servidor
- **Cloud**: Contratar hospedagem gerenciada (em breve)

### Preciso de internet para usar?

Não necessariamente. O Runas pode ser instalado localmente e funcionar sem internet. Porém, algumas funcionalidades requerem conexão:
- Notificações WhatsApp
- Pagamentos via PIX (Mercado Pago)
- Atualizações do sistema

---

## 🚀 Instalação e Setup

### Quais são os requisitos mínimos?

**Para desenvolvimento:**
- Docker Desktop instalado
- 4GB RAM disponível
- 10GB espaço em disco
- Windows 10+, macOS 10.15+, ou Linux

**Para produção:**
- Servidor com 2 CPU cores
- 4GB RAM
- 20GB SSD
- Ubuntu 20.04+ ou similar

### Como instalo o Runas?

```bash
# 1. Clone o repositório
git clone https://github.com/denebcorp/runas.git
cd runas

# 2. Configure o ambiente
cp .env.example .env
# Edite o .env com suas configurações

# 3. Suba os containers
docker-compose up -d

# 4. Execute migrations e seed
make migrate
make seed

# 5. Acesse o sistema
# Frontend: http://localhost:3000
# API: http://localhost:8000
```

Consulte o [Guia de Setup](../02-setup/README.md) para instruções detalhadas.

### Posso instalar sem Docker?

Sim, mas não é recomendado. O Docker garante que todos os serviços funcionem corretamente. Para instalação manual, você precisará:
- Python 3.12+
- Node.js 18+
- PostgreSQL 15
- Redis 7
- RabbitMQ 3
- Evolution API

### Como atualizo o Runas?

```bash
# 1. Backup do banco de dados
docker exec db-clientes pg_dump -U erp clientes > backup.sql

# 2. Atualizar código
git pull origin main

# 3. Atualizar containers
docker-compose pull
docker-compose up -d

# 4. Executar migrations
make migrate
```

---

## 💼 Funcionalidades

### Posso vender online com o Runas?

Sim! O Runas possui um catálogo público onde clientes podem:
- Visualizar produtos disponíveis
- Adicionar ao carrinho
- Finalizar compra
- Pagar via PIX

### Como funciona o sistema de crédito (fiado)?

1. **Configurar limite**: Admin define limite de crédito para o cliente
2. **Compra fiada**: Cliente compra e o valor é debitado do crédito disponível
3. **Vencimento**: Sistema calcula data de vencimento automaticamente
4. **Cobrança**: Notificações automáticas 3 dias antes e no vencimento
5. **Pagamento**: Cliente paga e crédito é liberado novamente
6. **Bloqueio**: Cliente é bloqueado automaticamente se não pagar

### Posso emitir nota fiscal?

Não no MVP. A emissão de NF-e está planejada para versões futuras. Consulte o [Roadmap](./roadmap.md).

### Como funciona a integração com WhatsApp?

O Runas usa a Evolution API para enviar notificações via WhatsApp:
- Confirmação de pedidos
- Alertas de estoque baixo
- Lembretes de pagamento
- Confirmação de quitação

Você precisa configurar sua própria instância da Evolution API.

### Posso usar múltiplas lojas?

Não no MVP. O sistema atual suporta apenas uma loja. Multi-tenant está planejado para 2027.

### Como faço backup dos dados?

```bash
# Backup manual
docker exec db-clientes pg_dump -U erp clientes > backup-clientes.sql
docker exec db-produtos pg_dump -U erp produtos > backup-produtos.sql
# ... repetir para todos os bancos

# Backup automático (configurar cron)
0 2 * * * /path/to/backup-script.sh
```

---

## 🔧 Técnico

### Qual linguagem é usada no backend?

Python 3.12+ com FastAPI. Escolhemos Python por:
- Produtividade e legibilidade
- Ecossistema rico de bibliotecas
- Excelente para APIs REST
- Comunidade ativa

### Qual framework é usado no frontend?

React 18 com TypeScript. Escolhemos React por:
- Componentes reutilizáveis
- Ecossistema maduro
- Performance excelente
- Fácil manutenção

### Por que microsserviços?

Microsserviços oferecem:
- **Escalabilidade**: Escalar serviços independentemente
- **Manutenibilidade**: Código organizado por domínio
- **Resiliência**: Falha em um serviço não derruba o sistema
- **Flexibilidade**: Tecnologias diferentes por serviço

### Posso usar outro banco de dados?

O Runas foi projetado para PostgreSQL. Usar outro banco requer:
- Adaptar migrations (Alembic)
- Ajustar queries específicas do PostgreSQL
- Testar extensivamente

Não recomendamos para usuários iniciantes.

### Como adiciono um novo microsserviço?

1. Crie a estrutura de pastas seguindo o padrão
2. Configure o Dockerfile e requirements.txt
3. Adicione ao docker-compose.yml
4. Configure o banco de dados
5. Implemente modelos, schemas, repositories e routers
6. Adicione ao API Gateway
7. Documente

Consulte a [Arquitetura](./arquitetura/) para detalhes.

### Posso contribuir com código?

Sim! Consulte o [Guia de Contribuição](../../CONTRIBUTING.md).

---

## 🔒 Segurança

### O Runas é seguro?

Sim. Implementamos:
- Autenticação JWT
- Senhas hasheadas com bcrypt
- Validação de entrada em todos os endpoints
- Rate limiting
- HTTPS obrigatório em produção
- Logs de auditoria

### Como são armazenadas as senhas?

Senhas são hasheadas com bcrypt antes de serem salvas no banco. Nunca armazenamos senhas em texto plano.

### Posso usar autenticação de dois fatores (2FA)?

Não no MVP. 2FA está planejado para versões futuras.

### Como reporto uma vulnerabilidade?

**NÃO** abra issues públicas. Envie email para: **security@denebcorp.com**

### Os dados são criptografados?

- **Em trânsito**: Sim, via HTTPS
- **Em repouso**: Depende da configuração do PostgreSQL

Para dados sensíveis, recomendamos:
- Criptografia de disco no servidor
- Backups criptografados
- Acesso restrito ao banco

---

## 📄 Licenciamento

### Qual é a licença do Runas?

O Runas é proprietário da DenebCorp. Consulte o arquivo [LICENSE](../../LICENSE.md) para detalhes.

### Posso usar comercialmente?

Sim, você pode usar o Runas para fins comerciais em seu próprio negócio.

### Posso revender o Runas?

Não. A revenda ou redistribuição comercial não é permitida sem autorização expressa.

### Posso modificar o código?

Sim, você pode modificar o código para uso próprio. Porém, não pode redistribuir versões modificadas sem autorização.

### Posso ver o código-fonte?

Sim, o código-fonte está disponível no GitHub para fins de transparência e auditoria.

---

## 🆘 Suporte

### Onde obtenho ajuda?

- **Documentação**: [docs/](../)
- **GitHub Issues**: [github.com/denebcorp/runas/issues](https://github.com/denebcorp/runas/issues)
- **Discord**: [Link do servidor]
- **Email**: support@denebcorp.com

### Como reporto um bug?

1. Verifique se já não foi reportado
2. Abra uma issue no GitHub
3. Use o template de bug report
4. Inclua logs e passos para reproduzir

### Como sugiro uma funcionalidade?

1. Verifique se já não foi sugerida
2. Abra uma issue no GitHub
3. Use o template de feature request
4. Explique o problema que resolve

### Existe suporte comercial?

Sim, oferecemos:
- Instalação e configuração
- Treinamento de equipe
- Suporte prioritário
- Customizações

Entre em contato: **sales@denebcorp.com**

---

## 📚 Recursos Adicionais

- [Documentação Completa](../)
- [Guia de Setup](../02-setup/README.md)
- [Arquitetura](./arquitetura/)
- [Roadmap](./roadmap.md)
- [Changelog](../12-changelog/CHANGELOG.md)
- [Guia de Contribuição](../../CONTRIBUTING.md)

---

## ❓ Sua pergunta não está aqui?

Abra uma issue no GitHub com a tag `question` ou entre em contato:
- **Email**: support@denebcorp.com
- **Discord**: [Link do servidor]

---

**Projeto:** Runas  
**Equipe:** Equipe DenebCorp  
**Data:** 26 de Maio de 2026  
**Versão:** 1.0.0
