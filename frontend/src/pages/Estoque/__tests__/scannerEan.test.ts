import { afterEach, describe, expect, it, vi } from 'vitest';
import { cameraSuportada, criarDetector, escolherFormatos } from '../scannerEan';

afterEach(() => vi.unstubAllGlobals());

describe('escolherFormatos', () => {
  it('mantém só formatos de varejo que o navegador suporta', () => {
    expect(escolherFormatos(['qr_code', 'ean_13', 'aztec', 'code_128'])).toEqual(['ean_13', 'code_128']);
  });

  it('devolve vazio quando o navegador não suporta nenhum', () => {
    expect(escolherFormatos(['qr_code'])).toEqual([]);
  });
});

describe('cameraSuportada', () => {
  const comCamera = () => vi.stubGlobal('navigator', { mediaDevices: { getUserMedia: vi.fn() } });

  it('liga a câmera em contexto seguro mesmo sem BarcodeDetector nativo', () => {
    vi.stubGlobal('isSecureContext', true);
    comCamera();
    expect('BarcodeDetector' in window).toBe(false);
    expect(cameraSuportada()).toBe(true);
  });

  it('não liga a câmera sem HTTPS', () => {
    vi.stubGlobal('isSecureContext', false);
    comCamera();
    expect(cameraSuportada()).toBe(false);
  });

  it('não liga a câmera quando o navegador não tem getUserMedia', () => {
    vi.stubGlobal('isSecureContext', true);
    vi.stubGlobal('navigator', {});
    expect(cameraSuportada()).toBe(false);
  });
});

describe('criarDetector', () => {
  const detectorNativo = (formatos: string[]) =>
    class {
      static getSupportedFormats = async () => formatos;
      constructor(public opts?: { formats?: string[] }) {}
      detect = async () => [];
    };

  it('usa o BarcodeDetector nativo, só com os formatos de varejo', async () => {
    const Nativo = detectorNativo(['qr_code', 'ean_13']);
    vi.stubGlobal('BarcodeDetector', Nativo);
    const detector = await criarDetector();
    expect(detector).toBeInstanceOf(Nativo);
    expect((detector as InstanceType<typeof Nativo>).opts).toEqual({ formats: ['ean_13'] });
  });

  it('cai no leitor reserva quando não existe BarcodeDetector', async () => {
    const detector = await criarDetector();
    // vídeo ainda sem quadro: o leitor reserva responde vazio em vez de lançar
    expect(await detector.detect(document.createElement('video'))).toEqual([]);
  });

  it('cai no leitor reserva quando o nativo não lê nenhum formato de varejo', async () => {
    const Nativo = detectorNativo(['qr_code']);
    vi.stubGlobal('BarcodeDetector', Nativo);
    expect(await criarDetector()).not.toBeInstanceOf(Nativo);
  });
});
