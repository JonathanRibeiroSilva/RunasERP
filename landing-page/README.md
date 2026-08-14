# Runas — Landing Page

Landing page do Runas (ERP para micro e pequenas empresas). É um Design
Component: `index.html` traz o markup + a lógica (`<script type="text/x-dc">`),
e `assets/js/support.js` é o runtime que compila os `{{ ... }}`, `<sc-if>` e
`<sc-for>`.

## Como rodar

Precisa de um servidor HTTP (o runtime carrega os scripts por caminho
relativo; abrir via `file://` não funciona):

```bash
python -m http.server 8000
# http://localhost:8000
```

## Deploy

Cloudflare Pages, projeto `runas-landing` (Direct Upload — não é conectado ao
GitHub, push não publica nada):

```powershell
powershell -ExecutionPolicy Bypass -File tools/deploy.ps1
```

O script copia `index.html`, `.image-slots.state.json` e `assets/` para uma
pasta temporária e sobe só isso. **Não troque por `wrangler pages deploy .`**:
o comando manda a pasta inteira — `README.md`, `tools/` e `.design/` foram todos
ao ar no primeiro deploy. `.assetsignore` não é lido por esse comando.
`.design/source/index.original.html` é a página duplicada; indexada, vira
duplicate content.

⚠️ `.image-slots.state.json` **precisa** ir junto. Parece arquivo de trabalho da
ferramenta, mas `image-slot.js` faz `fetch()` dele em runtime (`STATE_FILE`) e é
lá que moram a capa e o avatar da loja, em base64 — esses dois slots não têm
atributo `src`. Deixar de fora publica a página com o placeholder tracejado de
"solte uma imagem" no lugar das duas. Já aconteceu.

## Estrutura

```
index.html                      markup + lógica do componente
README.md
assets/
  css/main.css                  toda a folha de estilo (mobile-first)
  js/
    support.js                  runtime do Design Component
    image-slot.js               <image-slot> — slots de imagem editáveis
    glitter-warp.js             <glitter-warp> — partículas do CTA final
  img/
    brand/                      logotipos
    products/                   fotos dos produtos da loja de exemplo
tools/
  originals/                    fotos de produto antes do tratamento
  clean_products.py             script que trata as fotos
  restore.ps1                   desfaz um reset da ferramenta de design
.design/                        material de trabalho da ferramenta
  source/index.original.html    versão original, antes da refatoração
  uploads/  screenshots/
.image-slots.state.json         estado dos <image-slot> (o componente escreve aqui — manter na raiz)
.thumbnail
```

## ⚠️ A ferramenta de design reescreve a raiz

Já aconteceu uma vez: a ferramenta regenerou o projeto, renomeou `index.html`
para `*.dc.html`, devolveu `support.js` / `image-slot.js` / `glitter-warp.js`
para a raiz, restaurou as fotos com o xadrez e apagou as pastas.

Por isso o projeto está sob **git** — essa é a rede de segurança. Se acontecer
de novo:

```powershell
powershell -ExecutionPolicy Bypass -File tools/restore.ps1
```

O script restaura os arquivos rastreados e lista o que a ferramenta recriou
fora do lugar. Se o runtime tiver mudado de versão, mova por cima:

```powershell
Move-Item -Force support.js, image-slot.js, glitter-warp.js assets/js/
```

E se as fotos voltarem com xadrez:

```bash
python tools/clean_products.py tools/originals assets/img/products
```

**Antes de mexer no projeto pela ferramenta, faça um commit.** É o que torna o
reset reversível.

## CSS

`assets/css/main.css` é mobile-first: o estilo base atende telefone e cada
`@media (min-width: …)` só acrescenta para telas maiores. Breakpoints:

| Largura | O que muda |
|---------|------------|
| 400px   | respiro interno do card da loja |
| 480px   | botões lado a lado, features de preço em 2 colunas |
| 600px   | rodapé em 2 colunas |
| 640px   | tipografia e espaçamentos maiores |
| 680/720px | listas de módulos e passos em 2 colunas |
| 768px   | mock do dashboard ganha sidebar e 4 KPIs |
| 960px   | seção da Loja Online em 2 colunas; rodapé em 4 |
| 1024px  | navegação completa no lugar do hambúrguer |
| 1440px  | container vai a 1320px (senão sobra vazio nas laterais) |
| 1800px  | container a 1480px e seções mais espaçadas |

Convenções:

- Tokens em `:root` (cores, tipografia, `--gutter`, `--section-y`, `--tap`).
  `--gutter` e `--section-y` mudam por breakpoint, então `.shell` e `.section`
  respondem sozinhos.
- Títulos usam `clamp()` — escalam de forma contínua, sem salto de breakpoint.
- Alvos de toque respeitam `--tap` (44px), conforme WCAG 2.5.5.
- `:hover` sempre dentro de `@media (hover: hover)`, para o estado não "grudar"
  depois de um toque.
- `@media (prefers-reduced-motion: reduce)` desliga marquee, scroll suave e
  transições.

Verificado sem overflow horizontal de **280px a 2560px**.

### Cuidado: o header sticky depende de um override no wrapper

O runtime injeta `#dc-root, #dc-root > .sc-host { height: 100% }`
(`assets/js/support.js`, constante `FULL_PAGE_CSS`). Esse wrapper é o bloco
container do `position: sticky` do header — travado em uma tela de altura, o
header grudava por exatamente uma viewport e depois descolava e sumia.
`main.css` desfaz isso com `html #dc-root { height: auto; min-height: 100% }`
(o `html` na frente só serve para vencer a especificidade do runtime sem
`!important`).

Se o header voltar a sumir ao rolar, é esse override que se perdeu.

### Cuidado: custom elements não recebem `class`

O runtime **não repassa o atributo `class`** para custom elements
(`<image-slot>`, `<glitter-warp>`) — a classe simplesmente não chega no DOM.
Esses elementos precisam de `style` inline, e não é só cosmético: os dois medem
o próprio `clientWidth`/`clientHeight` para dimensionar o canvas/imagem, então
sem tamanho inline eles nascem 0×0 e não aparecem. Para elementos HTML normais,
`class` funciona sem problema.

### Cuidado: SEO fica no `<head>` estático, não no `<helmet>`

`title`, `description`, `canonical`, Open Graph, Twitter Card e JSON-LD moram no
`<head>` no **topo do arquivo**, fora do `<helmet>`.

O `<helmet>` só é processado depois que o runtime roda, e robô de prévia de link
(WhatsApp, Telegram, Slack) **não executa JavaScript**. Com essas tags no
helmet, colar o link do Runas numa conversa mostrava só a URL crua — sem título,
sem descrição, sem imagem. Como o funil inteiro desemboca no WhatsApp, era o
pior lugar possível para depender de JS.

Se alguma dessas tags voltar para dentro do `<helmet>`, a prévia quebra de novo,
e nada na página parece errado — só o compartilhamento.

As URLs do `og:image`, `og:url` e `canonical` são **absolutas** de propósito: os
robôs não resolvem caminho relativo. Se o domínio mudar, elas mudam junto.

### O FAQ existe em dois lugares

As 6 perguntas estão no `raw = [...]` do componente (o que a página mostra) e no
JSON-LD `FAQPage` do `<head>` (o que o Google lê sem rodar JS). A duplicação é
proposital, mas silenciosa: editar um lado e esquecer o outro publica dado
estruturado que não bate com a página.

```bash
python tools/check_faq.py     # sai com codigo 1 se divergirem
```

## Fotos de produto

As fotos originais vinham com o xadrez de transparência **queimado nos pixels**
(alpha 100% opaco), o que aparecia como quadriculado cinza no card da loja.
`tools/clean_products.py` detecta as duas cores do xadrez, mantém só a região
conectada à borda (para não furar áreas claras do produto), pinta esse fundo de
`#F5F5F5` e recorta/recentra o produto num quadrado.

`#F5F5F5` não é arbitrário: o `<image-slot>` pinta `rgba(127,127,127,.08)` sobre
o branco do `.store-thumb`, o que dá exatamente essa cor — assim a faixa lateral
do `object-fit: contain` some.

A saída é **WebP de no máximo 320px** de lado (`OUT_SIZE`/`QUALITY` no topo do
script). O thumb da loja renderiza a ~118px, então 320 já cobre telas 2x. Antes
o teto era 800px em PNG e uma das fotos saía com 501 KB para ocupar 118px na
tela — as quatro somavam 710 KB, hoje somam 38 KB.

O script nunca amplia: fotos cujo recorte é menor que o teto ficam no tamanho
nativo, para não borrar.

Precisa de `Pillow`, `numpy` e `scipy`.
