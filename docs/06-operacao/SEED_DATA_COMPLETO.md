# 🌱 Seed de Dados Completo - Ambiente Realista

Todos os comandos abaixo assumem a stack de desenvolvimento (`docker-compose.dev.yml`), cujos containers se chamam `erp-<servico>-dev`.

## Ordem de execução

1. ✅ Usuários do Gateway: `admin@runas.com` e `operador@runas.com` são criados sozinhos no startup do api-gateway (`api-gateway/main.py:46` chama `seed_admin()`); não há comando manual.
2. Empresas (`seed.py`)
3. Categorias de Produtos (`seed_categorias.py`)
4. Produtos (`seed_produtos.py`, exige as categorias)
5. Clientes (`seed_clientes.py`)

Os seeds de categorias, produtos e clientes gravam tudo com `empresa_id=1` fixo e pulam a execução se já houver registros dessa empresa.

## Como executar

```bash
# 1. Empresas
docker exec -it erp-empresas-dev python seed.py

# 2. Categorias (produtos)
docker exec -it erp-produtos-dev python seed_categorias.py

# 3. Produtos
docker exec -it erp-produtos-dev python seed_produtos.py

# 4. Clientes
docker exec -it erp-clientes-dev python seed_clientes.py
```

## Dados que serão criados

### Usuários do Gateway (automático no boot)
- Admin: e-mail e senha vêm de `ADMIN_EMAIL` / `ADMIN_PASSWORD` (padrões `admin@runas.com` / `Admin@123`), `empresa_id` de `ADMIN_EMPRESA_ID` (padrão 1)
- Operador de teste: `operador@runas.com` / `Operador@123` (papel OPERADOR, mesma empresa do admin)
- Super admin da plataforma: só é criado se `SUPER_ADMIN_EMAIL` e `SUPER_ADMIN_PASSWORD` estiverem no ambiente
- Senhas acima são apenas de desenvolvimento; troque em qualquer ambiente exposto.

### Empresas (3)
- Distribuidora Central (Matriz)
- Distribuidora Central - Zona Sul (Filial)
- Mercadinho do João (MEI)

### Categorias (8)
- Alimentos
- Bebidas
- Higiene e Limpeza
- Mercearia
- Frios e Laticínios
- Padaria
- Hortifruti
- Açougue

### Produtos (29)
- Distribuição: Mercearia 4, Alimentos 1, Bebidas 5, Higiene e Limpeza 5, Frios e Laticínios 5, Padaria 3, Hortifruti 3, Açougue 3
- Com preço, custo, `estoque_minimo` e código de barras
- **Não** cria registros de estoque: o saldo vem do seed do serviço de estoque (`services/estoque/seed.py`, que cria um registro por produto/variante existente)

### Clientes (15)
- 8 pessoas físicas e 7 estabelecimentos comerciais; todos usam CPF como identificador (o seed não cria CNPJ)
- Sem endereços (o seed genérico `services/clientes/seed.py` é quem usa o model `Endereco`)
- Com `limite_credito` e `credito_disponivel`
- 14 ativos e 1 inativo/bloqueado (Pedro Henrique Alves)

## Outros seeds

Cada serviço tem também um `seed.py` genérico. Em `financeiro` e `notificacoes` ele é apenas um stub com `TODO` (não cria nada).
