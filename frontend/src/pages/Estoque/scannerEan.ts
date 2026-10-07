/** Tipos mínimos da Barcode Detection API: o TypeScript instalado não a declara. */
export interface BarcodeDetectorLike {
  detect(source: CanvasImageSource): Promise<Array<{ rawValue: string }>>;
}
export interface BarcodeDetectorCtor {
  new (opts?: { formats?: string[] }): BarcodeDetectorLike;
  getSupportedFormats(): Promise<string[]>;
}

/** Formatos de produto de varejo; o resto (QR etc.) só atrapalharia a leitura. */
const FORMATOS_VAREJO = ['ean_13', 'ean_8', 'upc_a', 'upc_e', 'code_128'];

export const escolherFormatos = (suportados: string[]): string[] =>
  FORMATOS_VAREJO.filter((formato) => suportados.includes(formato));

/**
 * `BarcodeDetector` só existe em Android, macOS e ChromeOS; a câmera ainda exige
 * HTTPS. Sem os dois, a tela cai no campo de texto (que também atende leitor USB).
 */
export const cameraSuportada = (): boolean =>
  typeof window !== 'undefined' &&
  'BarcodeDetector' in window &&
  window.isSecureContext &&
  !!navigator.mediaDevices?.getUserMedia;

export const obterDetector = (): BarcodeDetectorCtor =>
  (window as unknown as { BarcodeDetector: BarcodeDetectorCtor }).BarcodeDetector;
