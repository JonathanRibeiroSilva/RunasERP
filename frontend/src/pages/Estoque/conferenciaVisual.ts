import type { ConferenciaVisualPayload, DeteccaoObjeto } from '@/types/estoque';

/** Forma que o COCO-SSD devolve: caixa em pixels do quadro de vídeo. */
export interface PredicaoCoco {
  bbox: [number, number, number, number];
  class: string;
  score: number;
}

const limitar = (valor: number) => Math.min(1, Math.max(0, valor));

/**
 * Pixels do quadro → fração da imagem, o formato do contrato do servidor.
 * O modelo às vezes devolve caixa vazada pela borda; o servidor recusa isso
 * (422), então a caixa é recortada aqui e a que sobra sem área é descartada.
 */
export const paraDeteccoes = (
  predicoes: PredicaoCoco[],
  larguraQuadro: number,
  alturaQuadro: number
): DeteccaoObjeto[] => {
  if (larguraQuadro <= 0 || alturaQuadro <= 0) return [];
  return predicoes.flatMap(({ bbox: [px, py, pw, ph], class: rotulo, score }) => {
    const x = limitar(px / larguraQuadro);
    const y = limitar(py / alturaQuadro);
    const largura = Math.min(limitar((px + pw) / larguraQuadro) - x, 1 - x);
    const altura = Math.min(limitar((py + ph) / alturaQuadro) - y, 1 - y);
    if (largura <= 0 || altura <= 0) return [];
    return [{ rotulo, confianca: limitar(score), caixa: { x, y, largura, altura } }];
  });
};

export const montarPayload = (detecoes: DeteccaoObjeto[], versaoModelo: string): ConferenciaVisualPayload => ({
  modelo: 'coco-ssd',
  versao_modelo: versaoModelo,
  // O servidor aceita no máximo 100; as de maior confiança é que importam.
  detecoes: [...detecoes].sort((a, b) => b.confianca - a.confianca).slice(0, 100),
});
