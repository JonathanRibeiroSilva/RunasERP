import { useEffect } from 'react';
import { createPortal } from 'react-dom';
import { FiX } from 'react-icons/fi';
import './Modal.scss';

interface ModalProps {
  isOpen: boolean;
  title: string;
  onClose: () => void;
  children: React.ReactNode;
  footer?: React.ReactNode;
}

/**
 * Casca de modal reutilizável: overlay, fecha em ESC/clique-fora, acessível.
 *
 * Renderiza em document.body, não onde é chamado. O app rola dentro de
 * `.main-content`, que tem z-index e por isso é um contexto de empilhamento: um
 * overlay renderizado ali dentro vale `500` só entre os irmãos dele, e a Navbar
 * (300) e a Sidebar (200) continuam pintando por cima, sem ser escurecidas, e
 * com a roda do mouse caindo na página de trás. Fora do `.main-content` o
 * z-index do overlay volta a valer contra o app inteiro.
 */
const Modal: React.FC<ModalProps> = ({ isOpen, title, onClose, children, footer }) => {
  useEffect(() => {
    if (!isOpen) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return createPortal(
    <div className="modal-overlay" onClick={onClose} role="presentation">
      <div
        className="modal-dialog"
        onClick={(event) => event.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label={title}
      >
        <div className="modal-header">
          <h2>{title}</h2>
          <button type="button" className="modal-close" onClick={onClose} aria-label="Fechar">
            <FiX />
          </button>
        </div>
        <div className="modal-body">{children}</div>
        {footer && <div className="modal-footer">{footer}</div>}
      </div>
    </div>,
    document.body,
  );
};

export default Modal;
