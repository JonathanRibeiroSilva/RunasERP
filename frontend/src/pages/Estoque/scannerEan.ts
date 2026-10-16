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
 * A câmera exige HTTPS e `getUserMedia`. O leitor não: `BarcodeDetector` só existe em
 * Android, macOS e ChromeOS, e nos demais `criarDetector` cai num leitor em JS puro.
 * Sem câmera, a tela fica no campo de texto (que também atende leitor USB).
 */
export const cameraSuportada = (): boolean =>
  typeof window !== 'undefined' && window.isSecureContext && !!navigator.mediaDevices?.getUserMedia;

/** `BarcodeDetector` nativo quando lê formato de varejo; senão o leitor reserva, baixado só nesse caso. */
export const criarDetector = async (): Promise<BarcodeDetectorLike> => {
  if ('BarcodeDetector' in window) {
    const Detector = (window as unknown as { BarcodeDetector: BarcodeDetectorCtor }).BarcodeDetector;
    const formatos = escolherFormatos(await Detector.getSupportedFormats());
    if (formatos.length > 0) return new Detector({ formats: formatos });
  }
  return (await import('./leitorReserva')).criarLeitorReserva();
};
