# Regras de Negócio — Índice

Um documento por domínio. Cada um lista as entidades, os campos e as regras
numeradas. O prefixo da numeração é por **entidade**, não por domínio: `clientes.md`
usa `RN-CLI-*` e `RN-END-*`; `produtos.md` usa `RN-CAT-*`, `RN-PRO-*`, `RN-VAR-*`,
`RN-FOR-*`, `RN-FP-*`, `RN-CAL-*` e `RN-FOT-*`; `estoque.md` usa `RN-EST-*`, `RN-MOV-*`,
`RN-LOT-*` e `RN-INV-*`; `vendas.md` usa `RN-CAR-*`, `RN-PED-*` e `RN-VEN-*`;
`financeiro.md` usa `RN-FIN-*`, `RN-PAG-*` e `RN-CRE-*`.

| Domínio | Documento | O que cobre |
|---------|-----------|-------------|
| Clientes | [clientes.md](./clientes.md) | Cliente e Endereço: validação de CPF, telefone E.164, nome e e-mail; limite e crédito disponível para venda fiada; bloqueio. Casos de uso ao final. |
| Produtos | [produtos.md](./produtos.md) | Sete entidades: Categoria, Produto, Variante, Fornecedor, vínculo Fornecedor-Produto, configuração de Catálogo e fotos de Catálogo. |
| Estoque | [estoque.md](./estoque.md) | Estoque, Movimentação, Lote e Inventário: fórmula `quantidade_disponivel = quantidade - quantidade_reservada`, alertas de mínimo/zerado e reserva. |
| Vendas | [vendas.md](./vendas.md) | Carrinho (token anônimo, TTL, reserva de estoque no Redis), Pedido e Venda, além dos fluxos completos e das integrações com os outros serviços. |
| Financeiro | [financeiro.md](./financeiro.md) | **PLANEJADO — ver aviso abaixo.** Conta a Receber, Pagamento Fiado, controle de crédito, jobs Celery, eventos assíncronos e relatórios. |

## ⚠️ financeiro.md é especificação, não é o que roda

`services/financeiro/main.py` expõe **uma única rota**: `GET /health`
(`services/financeiro/main.py:56-59`). Não há nenhum `include_router` no
serviço, e `services/financeiro/routers/` e `services/financeiro/models/`
contêm apenas `__init__.py`.

Ou seja: **nenhuma** das regras de `financeiro.md` (`RN-FIN-*`, `RN-PAG-*`, `RN-CRE-*`) está implementada. Trate
`financeiro.md` como especificação a construir, não como comportamento
vigente. Não escreva código nem teste assumindo que qualquer uma dessas
regras já existe.

Os outros quatro serviços documentados aqui têm routers montados no `main.py`:
clientes (2 `include_router`), produtos (8), estoque (1) e vendas (6).

## Onde olhar em seguida

- [docs/10-api-reference/](../10-api-reference/) — contratos das rotas. Contém seis arquivos `*-api.md`
  (`clientes`, `estoque`, `financeiro`, `plataforma`, `produtos`, `vendas`), mais `openapi.yaml`
  e `mapeamento-rotas.md`. Não há `*-api.md` para `empresas` nem para `notificacoes`.
- [docs/03-arquitetura/](../03-arquitetura/) — topologia, comunicação entre serviços e persistência.

## A confirmar

- **A CONFIRMAR:** se as regras dos quatro documentos implementados (clientes, produtos, estoque, vendas) ainda correspondem ao código — este índice confirmou apenas que os serviços existem e têm rotas montadas, não fez a conferência regra a regra.
- **A CONFIRMAR:** os cinco documentos declaram "Última atualização: 26 de Maio de 2026, Versão 1.0.0" no rodapé; nenhuma fonte no repositório corrobora essa data.
