import { describe, expect, it } from 'vitest';
import { escolherFormatos } from '../scannerEan';

describe('escolherFormatos', () => {
  it('mantém só formatos de varejo que o navegador suporta', () => {
    expect(escolherFormatos(['qr_code', 'ean_13', 'aztec', 'code_128'])).toEqual(['ean_13', 'code_128']);
  });

  it('devolve vazio quando o navegador não suporta nenhum', () => {
    expect(escolherFormatos(['qr_code'])).toEqual([]);
  });
});
