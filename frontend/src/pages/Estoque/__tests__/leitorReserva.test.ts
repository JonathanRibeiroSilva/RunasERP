import { RGBLuminanceSource } from '@zxing/library';
import { describe, expect, it } from 'vitest';
import { decodificarQuadro } from '../leitorReserva';

const L = ['0001101', '0011001', '0010011', '0111101', '0100011', '0110001', '0101111', '0111011', '0110111', '0001011'];
const G = ['0100111', '0110011', '0011011', '0100001', '0011101', '0111001', '0000101', '0010001', '0001001', '0010111'];
const R = ['1110010', '1100110', '1101100', '1000010', '1011100', '1001110', '1010000', '1000100', '1001000', '1110100'];
const PARIDADE = ['LLLLLL', 'LLGLGG', 'LLGGLG', 'LLGGGL', 'LGLLGG', 'LGGLLG', 'LGGGLL', 'LGLGLG', 'LGLGGL', 'LGGLGL'];

/** Codifica 13 dígitos em módulos de EAN-13 sem recalcular o dígito verificador (o teste precisa de DV inválido). */
const modulosEan13 = (digitos: string): string => {
  const d = [...digitos].map(Number);
  const esquerda = d.slice(1, 7).map((n, i) => (PARIDADE[d[0]][i] === 'L' ? L[n] : G[n]));
  const direita = d.slice(7).map((n) => R[n]);
  return `101${esquerda.join('')}01010${direita.join('')}101`;
};

/** Imagem em tons de cinza: barras pretas sobre fundo branco, com a zona de silêncio de 11 módulos. */
const desenharEan13 = (digitos: string, pixelsPorModulo = 3, altura = 60) => {
  const modulos = '0'.repeat(11) + modulosEan13(digitos) + '0'.repeat(11);
  const largura = modulos.length * pixelsPorModulo;
  const linha = new Uint8ClampedArray(largura);
  [...modulos].forEach((m, i) => linha.fill(m === '1' ? 0 : 255, i * pixelsPorModulo, (i + 1) * pixelsPorModulo));
  const luminancia = new Uint8ClampedArray(largura * altura);
  for (let y = 0; y < altura; y++) luminancia.set(linha, y * largura);
  return new RGBLuminanceSource(luminancia, largura, altura);
};

describe('decodificarQuadro', () => {
  it('lê um EAN-13 válido desenhado em barras', () => {
    expect(decodificarQuadro(desenharEan13('7894900011012'))).toBe('7894900011012');
  });

  it('recusa EAN-13 com dígito verificador inválido, como o leitor nativo', () => {
    expect(decodificarQuadro(desenharEan13('7894900011013'))).toBeNull();
  });

  it('devolve null num quadro sem código', () => {
    const branco = new RGBLuminanceSource(new Uint8ClampedArray(200 * 60).fill(255), 200, 60);
    expect(decodificarQuadro(branco)).toBeNull();
  });
});
