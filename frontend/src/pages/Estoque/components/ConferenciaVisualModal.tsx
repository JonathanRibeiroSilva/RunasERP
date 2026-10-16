import { useEffect, useRef, useState } from 'react';
import { toast } from 'react-toastify';
import Modal from '@/components/common/Modal/Modal';
import { estoqueApi } from '@/services/api/estoqueApi';
import { getErrorMessage } from '@/services/api/axios';
import type { DeteccaoObjeto } from '@/types/estoque';
import { montarPayload, paraDeteccoes, type PredicaoCoco } from '../conferenciaVisual';

interface Props {
  onClose: () => void;
}

const VERSAO_MODELO = 'lite_mobilenet_v2';
const INTERVALO_MS = 500;
const LIMIAR_EXIBICAO = 0.5;

type Detector = { detect: (v: HTMLVideoElement) => Promise<PredicaoCoco[]> };

const resumir = (contagem: Record<string, number>) =>
  Object.entries(contagem)
    .map(([rotulo, n]) => `${n}× ${rotulo}`)
    .join(' · ');

/**
 * Detecção genérica de objetos para conferir um recebimento a olho. Não
 * identifica SKU e não mexe no estoque: o servidor só valida e resume o que
 * foi visto. COCO-SSD sobre tfjs-webgl (JS puro, sem WASM: a CSP de produção
 * bloqueia). Os pesos vêm de /models porque connect-src é 'self'.
 */
const ConferenciaVisualModal: React.FC<Props> = ({ onClose }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const ultimas = useRef<DeteccaoObjeto[]>([]);
  const [status, setStatus] = useState<'carregando' | 'pronto' | 'erro'>('carregando');
  const [mensagemErro, setMensagemErro] = useState('');
  const [contagem, setContagem] = useState<Record<string, number>>({});
  const [enviando, setEnviando] = useState(false);

  useEffect(() => {
    let parado = false;
    let timer: ReturnType<typeof setInterval> | undefined;
    let stream: MediaStream | undefined;

    const desenhar = (video: HTMLVideoElement, deteccoes: DeteccaoObjeto[]) => {
      const canvas = canvasRef.current;
      const ctx = canvas?.getContext('2d');
      if (!canvas || !ctx) return;
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.lineWidth = Math.max(2, canvas.width / 200);
      ctx.font = `${Math.max(14, canvas.width / 40)}px sans-serif`;
      ctx.strokeStyle = '#22c55e';
      ctx.fillStyle = '#22c55e';
      for (const { rotulo, confianca, caixa } of deteccoes) {
        const x = caixa.x * canvas.width;
        const y = caixa.y * canvas.height;
        ctx.strokeRect(x, y, caixa.largura * canvas.width, caixa.altura * canvas.height);
        ctx.fillText(`${rotulo} ${Math.round(confianca * 100)}%`, x + 4, y + ctx.lineWidth + 14);
      }
    };

    (async () => {
      try {
        // Importado sob demanda: ~1,5 MB de tfjs que só quem abre esta tela paga.
        const [tf, cocoSsd] = await Promise.all([
          import('@tensorflow/tfjs-core'),
          import('@tensorflow-models/coco-ssd'),
          import('@tensorflow/tfjs-converter'),
          import('@tensorflow/tfjs-backend-webgl'),
        ]);
        await tf.setBackend('webgl');
        await tf.ready();
        const modelo: Detector = await cocoSsd.load({
          base: 'lite_mobilenet_v2',
          modelUrl: `${import.meta.env.BASE_URL}models/coco-ssd/model.json`,
        });
        if (parado) return;

        stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: { ideal: 'environment' } },
        });
        if (parado) return stream.getTracks().forEach((t) => t.stop());
        const video = videoRef.current;
        if (!video) return;
        video.srcObject = stream;
        await video.play();
        setStatus('pronto');

        let ocupado = false;
        timer = setInterval(async () => {
          if (ocupado || parado || video.videoWidth === 0) return;
          ocupado = true; // a inferência pode demorar mais que o intervalo
          try {
            const predicoes = await modelo.detect(video);
            const deteccoes = paraDeteccoes(
              predicoes.filter((p) => p.score >= LIMIAR_EXIBICAO),
              video.videoWidth,
              video.videoHeight
            );
            if (parado) return;
            ultimas.current = deteccoes;
            desenhar(video, deteccoes);
            const porRotulo: Record<string, number> = {};
            for (const d of deteccoes) porRotulo[d.rotulo] = (porRotulo[d.rotulo] ?? 0) + 1;
            setContagem(porRotulo);
          } catch {
            /* quadro sem imagem ainda: tenta no próximo ciclo */
          } finally {
            ocupado = false;
          }
        }, INTERVALO_MS);
      } catch (e) {
        if (parado) return;
        setMensagemErro(
          e instanceof DOMException && e.name === 'NotAllowedError'
            ? 'Permissão da câmera negada. Libere a câmera para este site e tente de novo.'
            : 'Não foi possível carregar o modelo ou abrir a câmera neste aparelho.'
        );
        setStatus('erro');
      }
    })();

    return () => {
      parado = true;
      if (timer) clearInterval(timer);
      stream?.getTracks().forEach((t) => t.stop());
    };
  }, []);

  const enviar = async () => {
    setEnviando(true);
    try {
      const resumo = await estoqueApi.conferenciaVisual(montarPayload(ultimas.current, VERSAO_MODELO));
      toast.success(
        resumo.total_aceito === 0
          ? 'Nada detectado com confiança suficiente.'
          : `Conferência registrada: ${resumir(resumo.contagem_por_rotulo)}`
      );
      onClose();
    } catch (e) {
      toast.error(getErrorMessage(e));
    } finally {
      setEnviando(false);
    }
  };

  const total = Object.values(contagem).reduce((soma, n) => soma + n, 0);

  return (
    <Modal
      isOpen
      title="Conferência visual"
      onClose={onClose}
      footer={
        status === 'pronto' && (
          <button type="button" className="btn" disabled={enviando || total === 0} onClick={enviar}>
            {enviando ? 'Enviando…' : 'Registrar conferência'}
          </button>
        )
      }
    >
      {status === 'erro' ? (
        <p role="alert">{mensagemErro}</p>
      ) : (
        <>
          {status === 'carregando' && <p>Carregando modelo de detecção…</p>}
          <div style={{ position: 'relative' }}>
            <video ref={videoRef} playsInline muted style={{ width: '100%', borderRadius: 8, background: '#000' }} />
            <canvas
              ref={canvasRef}
              aria-hidden="true"
              style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', pointerEvents: 'none' }}
            />
          </div>
          <p style={{ marginTop: 8 }}>
            {total === 0 ? 'Aponte a câmera para a carga recebida.' : resumir(contagem)}
          </p>
          <p style={{ fontSize: 12, opacity: 0.7 }}>
            Detecção genérica de objetos: não identifica produto e não altera o estoque.
          </p>
        </>
      )}
    </Modal>
  );
};

export default ConferenciaVisualModal;
