import { useEffect, useRef, useState } from 'react';
import Modal from '@/components/common/Modal/Modal';
import { escolherFormatos, obterDetector } from '../scannerEan';

interface Props {
  onCodigo: (codigo: string) => void;
  onClose: () => void;
}

const INTERVALO_MS = 250;

/** Lê EAN pela câmera traseira com o BarcodeDetector nativo (sem WASM: a CSP de produção o bloqueia). */
const ScannerEanModal: React.FC<Props> = ({ onCodigo, onClose }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    let parado = false;
    let timer: ReturnType<typeof setInterval> | undefined;
    let stream: MediaStream | undefined;

    (async () => {
      try {
        const Detector = obterDetector();
        const formatos = escolherFormatos(await Detector.getSupportedFormats());
        if (formatos.length === 0) throw new Error('formatos');
        const detector = new Detector({ formats: formatos });

        stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: { ideal: 'environment' } },
        });
        if (parado) return stream.getTracks().forEach((t) => t.stop());
        const video = videoRef.current;
        if (!video) return;
        video.srcObject = stream;
        await video.play();

        timer = setInterval(async () => {
          try {
            const [achado] = await detector.detect(video);
            if (achado && !parado) {
              parado = true;
              onCodigo(achado.rawValue);
            }
          } catch {
            /* quadro sem imagem ainda: tenta no próximo ciclo */
          }
        }, INTERVALO_MS);
      } catch (e) {
        if (parado) return;
        const negada = e instanceof DOMException && e.name === 'NotAllowedError';
        setErro(
          negada
            ? 'Permissão da câmera negada. Libere a câmera para este site e tente de novo.'
            : 'Não foi possível abrir a câmera neste aparelho. Digite o código no campo.'
        );
      }
    })();

    return () => {
      parado = true;
      if (timer) clearInterval(timer);
      stream?.getTracks().forEach((t) => t.stop());
    };
    // onCodigo muda a cada render da página; reabrir a câmera por isso seria um bug.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <Modal isOpen title="Ler código de barras" onClose={onClose}>
      {erro ? (
        <p role="alert">{erro}</p>
      ) : (
        <>
          <video
            ref={videoRef}
            playsInline
            muted
            style={{ width: '100%', borderRadius: 8, background: '#000' }}
          />
          <p style={{ marginTop: 8, textAlign: 'center' }}>Aponte a câmera para o código de barras</p>
        </>
      )}
    </Modal>
  );
};

export default ScannerEanModal;
