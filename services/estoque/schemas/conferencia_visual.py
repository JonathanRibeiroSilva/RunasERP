"""
Contrato da conferência visual de recebimento.

O modelo roda no navegador (COCO-SSD, JS puro: a CSP de produção bloqueia WASM) e
o servidor nunca vê imagem: recebe só o que o modelo achou. Este arquivo é o
contrato dessa fronteira. Tudo o que o cliente manda é validado aqui, porque
quem chama pode ser qualquer coisa que tenha o token interno, não só o nosso
frontend.

Zero escrita no estoque: a detecção genérica ("caixa", "garrafa") não identifica
SKU, então não há base para mexer em saldo. O endpoint só valida e resume.
"""
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

# As 80 classes do COCO, na ordem do modelo. Rótulo fora desta lista é payload
# forjado ou versão de modelo diferente: recusar é melhor que contar lixo.
COCO_ROTULOS = frozenset({
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck",
    "boat", "traffic light", "fire hydrant", "stop sign", "parking meter", "bench",
    "bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra",
    "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee",
    "skis", "snowboard", "sports ball", "kite", "baseball bat", "baseball glove",
    "skateboard", "surfboard", "tennis racket", "bottle", "wine glass", "cup",
    "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange",
    "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch",
    "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse",
    "remote", "keyboard", "cell phone", "microwave", "oven", "toaster", "sink",
    "refrigerator", "book", "clock", "vase", "scissors", "teddy bear",
    "hair drier", "toothbrush",
})

# Abaixo disto o COCO-SSD erra demais para contar como conferência.
LIMIAR_CONFIANCA = 0.5
MAX_DETECCOES = 100

# Coordenadas chegam como float do navegador; 1e-6 absorve o arredondamento.
_TOLERANCIA = 1e-6

Fracao = Annotated[float, Field(ge=0, le=1)]


class CaixaDelimitadora(BaseModel):
    """Retângulo em fração da imagem (0 a 1), origem no canto superior esquerdo.

    Fração, não pixel: o servidor não conhece a resolução da câmera e o contrato
    não deve depender dela.
    """
    model_config = ConfigDict(extra="forbid")

    x: Fracao
    y: Fracao
    largura: Annotated[float, Field(gt=0, le=1)]
    altura: Annotated[float, Field(gt=0, le=1)]

    @model_validator(mode="after")
    def _dentro_da_imagem(self) -> "CaixaDelimitadora":
        if self.x + self.largura > 1 + _TOLERANCIA or self.y + self.altura > 1 + _TOLERANCIA:
            raise ValueError("a caixa passa da borda da imagem")
        return self


class DeteccaoObjeto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rotulo: str = Field(..., max_length=32)
    confianca: Fracao
    caixa: CaixaDelimitadora

    @model_validator(mode="after")
    def _rotulo_coco(self) -> "DeteccaoObjeto":
        if self.rotulo not in COCO_ROTULOS:
            raise ValueError(f"rótulo fora das classes do COCO: {self.rotulo!r}")
        return self


class ConferenciaVisualRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    modelo: str = Field(..., pattern=r"^coco-ssd$")
    versao_modelo: str = Field(..., min_length=1, max_length=32)
    detecoes: list[DeteccaoObjeto] = Field(default_factory=list, max_length=MAX_DETECCOES)


class ConferenciaVisualResponse(BaseModel):
    total_detectado: int = Field(..., description="Tudo que o cliente mandou")
    total_aceito: int = Field(..., description="Detecções com confiança >= limiar")
    limiar_confianca: float = LIMIAR_CONFIANCA
    contagem_por_rotulo: dict[str, int] = Field(
        default_factory=dict, description="Só as detecções aceitas"
    )
