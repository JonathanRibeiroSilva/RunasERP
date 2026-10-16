import {
  BarcodeFormat,
  BinaryBitmap,
  ChecksumException,
  DecodeHintType,
  FormatException,
  HTMLCanvasElementLuminanceSource,
  HybridBinarizer,
  MultiFormatOneDReader,
  NotFoundException,
  type LuminanceSource,
} from '@zxing/library';
import type { BarcodeDetectorLike } from './scannerEan';

/**
 * Leitor para navegadores sem `BarcodeDetector` (Chrome/Edge no Windows, Firefox, iOS).
 * JavaScript puro de propósito: a CSP de produção não tem `'wasm-unsafe-eval'`.
 */
const hints = new Map<DecodeHintType, unknown>([
  [
    DecodeHintType.POSSIBLE_FORMATS,
    [BarcodeFormat.EAN_13, BarcodeFormat.EAN_8, BarcodeFormat.UPC_A, BarcodeFormat.UPC_E, BarcodeFormat.CODE_128],
  ],
  [DecodeHintType.TRY_HARDER, true],
]);
// Só a família 1D: cada quadro roda menos leitores. O chunk continua em ~450 kB (119 kB gzip) porque
// o pacote não faz tree-shaking; ponytail: importar de '@zxing/library/esm/core/...' se o peso incomodar.
const leitor = new MultiFormatOneDReader(hints);

/** Texto do código no quadro, ou null. Quadro sem código legível é o caso normal, não um erro. */
export const decodificarQuadro = (fonte: LuminanceSource): string | null => {
  try {
    return leitor.decode(new BinaryBitmap(new HybridBinarizer(fonte)), hints).getText();
  } catch (e) {
    if (e instanceof NotFoundException || e instanceof ChecksumException || e instanceof FormatException) return null;
    throw e;
  }
};

// ponytail: decodifica na thread principal a cada 250 ms; Web Worker exigiria `worker-src blob:` na CSP.
export const criarLeitorReserva = (): BarcodeDetectorLike => {
  const canvas = document.createElement('canvas');
  return {
    async detect(origem) {
      const video = origem as HTMLVideoElement;
      if (!video.videoWidth) return [];
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      canvas.getContext('2d', { willReadFrequently: true })?.drawImage(video, 0, 0);
      const texto = decodificarQuadro(new HTMLCanvasElementLuminanceSource(canvas));
      return texto ? [{ rawValue: texto }] : [];
    },
  };
};
