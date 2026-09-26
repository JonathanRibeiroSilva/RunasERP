# 🌱 Seed de Dados Completo - Ambiente Realista

## Ordem de execução

1. ✅ Empresas (já existe seed)
2. ✅ Usuários do Gateway (admin já criado no seed)
3. 🆕 Categorias de Produtos
4. 🆕 Produtos
5. 🆕 Clientes

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

### Produtos (30)
- 5 por categoria principal
- Com preços realistas
- Com estoque
- Com códigos de barras

### Clientes (20)
- Mix de pessoa física e jurídica
- Com endereços completos
- Com crédito configurado
- Ativos e inativos
