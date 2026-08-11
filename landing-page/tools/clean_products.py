"""
Remove o xadrez de transparencia que ficou "queimado" nos pixels das fotos de
produto, achata o fundo num cinza-claro uniforme e reenquadra o produto.

As fotos originais tem alpha 100% opaco: o quadriculado que parece
transparencia e pixel de verdade, e aparecia como xadrez no card da loja.

Estrategia:
  1. Detecta as duas cores do xadrez amostrando a borda da imagem.
  2. Marca como candidato a fundo todo pixel cinza-claro (baixa saturacao e
     luminancia >= cor escura do xadrez - tolerancia).
  3. Mantem so os candidatos conectados a borda -> esse e o fundo real
     (evita apagar areas claras DENTRO do produto, como leite ou pao).
  4. Pinta o fundo de BG.
  5. Recorta o bounding box do produto e recentra num quadrado.

Uso:
    python tools/clean_products.py tools/originals assets/img/products

Precisa de: Pillow, numpy, scipy
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

SRC = Path(sys.argv[1])
DST = Path(sys.argv[2]) if len(sys.argv) > 2 else SRC

CHROMA_MAX = 16      # quao "cinza" um pixel precisa ser para ser fundo
TOL = 14             # tolerancia sobre a cor escura do xadrez
MARGIN = 0.05        # respiro ao redor do produto, em fracao do lado
# O thumb da loja renderiza a ~118px de lado, entao 320 ja cobre telas 2x com
# folga. Estava em 800, e uma das fotos batia no teto e saia com 501 KB para
# ocupar 118px na tela.
OUT_SIZE = 320       # lado maximo da imagem final (quadrada)
QUALITY = 86         # WebP: ~94% menor que o PNG equivalente, sem diferenca visivel
# O <image-slot> pinta rgba(127,127,127,.08) sobre o branco do .store-thumb,
# o que da exatamente #F5F5F5. Usar a MESMA cor no fundo da foto faz a faixa
# das laterais (letterbox do object-fit: contain) sumir por completo.
BG = (245, 245, 245)


def checker_colors(rgb):
    """Duas cores dominantes na moldura externa da imagem."""
    band = np.concatenate([
        rgb[:3].reshape(-1, 3), rgb[-3:].reshape(-1, 3),
        rgb[:, :3].reshape(-1, 3), rgb[:, -3:].reshape(-1, 3),
    ])
    chroma = band.max(1).astype(int) - band.min(1).astype(int)
    grey = band[chroma <= CHROMA_MAX].mean(1).astype(int)
    if grey.size == 0:
        return 255, 255
    counts = np.bincount(grey, minlength=256)
    top = np.argsort(counts)[::-1][:6]
    top = [v for v in top if counts[v] > grey.size * 0.02]
    return (max(top), min(top)) if top else (255, 255)


def clean(path_in, path_out):
    im = Image.open(path_in).convert("RGBA")
    flat = Image.new("RGBA", im.size, (255, 255, 255, 255))
    flat.alpha_composite(im)
    rgb = np.asarray(flat.convert("RGB")).astype(np.uint8)

    light, dark = checker_colors(rgb)

    chroma = rgb.max(2).astype(int) - rgb.min(2).astype(int)
    lum = rgb.mean(2)
    candidate = (chroma <= CHROMA_MAX) & (lum >= dark - TOL)

    # so o que encosta na borda e fundo de verdade
    labels, n = ndimage.label(candidate)
    if n:
        edge = np.unique(np.concatenate([
            labels[0], labels[-1], labels[:, 0], labels[:, -1],
        ]))
        edge = edge[edge > 0]
        background = np.isin(labels, edge)
    else:
        background = np.zeros_like(candidate)

    # come 1px a mais para matar a borda serrilhada do xadrez
    background = ndimage.binary_dilation(background, iterations=1) & candidate

    out = rgb.copy()
    out[background] = BG

    # bounding box do produto: pixels com contraste de verdade
    solid = (~background) & ((lum < 236) | (chroma > 22))
    solid = ndimage.binary_opening(solid, structure=np.ones((3, 3)))
    ys, xs = np.nonzero(solid)
    if ys.size:
        y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        out[:y0] = BG
        out[y1:] = BG
        out[:, :x0] = BG
        out[:, x1:] = BG
        crop = Image.fromarray(out[y0:y1, x0:x1])
    else:
        crop = Image.fromarray(out)

    # Quadrado com margem uniforme, na resolucao nativa do recorte: nunca
    # amplia (evita borrar as fotos pequenas), so reduz se passar do teto.
    side = int(max(crop.width, crop.height) * (1 + 2 * MARGIN))
    if side > OUT_SIZE:
        inner = int(OUT_SIZE / (1 + 2 * MARGIN))
        crop.thumbnail((inner, inner), Image.LANCZOS)
        side = OUT_SIZE
    canvas = Image.new("RGB", (side, side), BG)
    canvas.paste(crop, ((side - crop.width) // 2, (side - crop.height) // 2))
    canvas.save(path_out, "WEBP", quality=QUALITY, method=6)

    print(f"{path_in.name}: xadrez {light}/{dark} -> "
          f"{100 * background.mean():.1f}% virou fundo, "
          f"recorte {crop.width}x{crop.height}")


DST.mkdir(parents=True, exist_ok=True)
for f in sorted(SRC.glob("*.png")):
    clean(f, DST / f.with_suffix(".webp").name)
