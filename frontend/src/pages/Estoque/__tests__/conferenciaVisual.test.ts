import { describe, expect, it } from 'vitest';
import { montarPayload, paraDeteccoes } from '../conferenciaVisual';

describe('paraDeteccoes', () => {
  it('converte pixels em fração do quadro', () => {
    const [d] = paraDeteccoes([{ bbox: [64, 48, 128, 96], class: 'bottle', score: 0.9 }], 640, 480);
    expect(d.caixa.x).toBeCloseTo(0.1);
    expect(d.caixa.y).toBeCloseTo(0.1);
    expect(d.caixa.largura).toBeCloseTo(0.2);
    expect(d.caixa.altura).toBeCloseTo(0.2);
    expect(d.rotulo).toBe('bottle');
  });

  it('recorta caixa que vaza pela borda, para o servidor não devolver 422', () => {
    const [d] = paraDeteccoes([{ bbox: [600, -20, 100, 100], class: 'cup', score: 0.8 }], 640, 480);
    expect(d.caixa.x + d.caixa.largura).toBeLessThanOrEqual(1);
    expect(d.caixa.y).toBe(0);
    expect(d.caixa.altura).toBeCloseTo(80 / 480);
  });

  it('descarta caixa que sobrou sem área', () => {
    expect(paraDeteccoes([{ bbox: [700, 10, 50, 50], class: 'cup', score: 0.8 }], 640, 480)).toEqual([]);
  });

  it('quadro de vídeo ainda sem tamanho não gera nada', () => {
    expect(paraDeteccoes([{ bbox: [0, 0, 10, 10], class: 'cup', score: 1 }], 0, 0)).toEqual([]);
  });
});

describe('montarPayload', () => {
  it('manda no máximo 100 detecções, as de maior confiança', () => {
    const muitas = Array.from({ length: 150 }, (_, i) => ({
      rotulo: 'bottle',
      confianca: i / 150,
      caixa: { x: 0, y: 0, largura: 0.1, altura: 0.1 },
    }));
    const { detecoes, modelo } = montarPayload(muitas, '2.2.3');
    expect(modelo).toBe('coco-ssd');
    expect(detecoes).toHaveLength(100);
    expect(detecoes[0].confianca).toBeGreaterThan(detecoes[99].confianca);
  });
});
