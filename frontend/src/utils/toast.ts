/**
 * Utilitário para notificações Toast
 * Wrapper do react-toastify com configurações padronizadas
 */
import { toast, ToastOptions } from 'react-toastify';

// Configurações padrão
const defaultOptions: ToastOptions = {
  position: 'top-right',
  autoClose: 4000,
  hideProgressBar: false,
  closeOnClick: true,
  pauseOnHover: true,
  draggable: true,
};

export const Toast = {
  /**
   * Notificação de sucesso
   */
  success(message: string, options?: ToastOptions) {
    toast.success(message, { ...defaultOptions, ...options });
  },

  /**
   * Notificação de erro
   */
  error(message: string, options?: ToastOptions) {
    toast.error(message, { ...defaultOptions, autoClose: 5000, ...options });
  },

  /**
   * Notificação de aviso
   */
  warning(message: string, options?: ToastOptions) {
    toast.warning(message, { ...defaultOptions, ...options });
  },

  /**
   * Notificação informativa
   */
  info(message: string, options?: ToastOptions) {
    toast.info(message, { ...defaultOptions, ...options });
  },

  /**
   * Trata erros da API e exibe toast apropriado
   */
  apiError(error: any) {
    if (error.response?.data?.detail) {
      const detail = error.response.data.detail;

      // Se for array de erros de validação (422)
      if (Array.isArray(detail)) {
        detail.forEach((err: any) => {
          const campo = err.loc?.[err.loc.length - 1] || 'Campo';
          const mensagem = err.msg || 'Erro de validação';
          toast.error(`${campo}: ${mensagem}`, { ...defaultOptions, autoClose: 6000 });
        });
      } 
      // Se for string
      else if (typeof detail === 'string') {
        toast.error(detail, { ...defaultOptions, autoClose: 5000 });
      } 
      // Se for objeto
      else {
        toast.error('Erro ao processar solicitação', { ...defaultOptions });
      }
    } else if (error.message) {
      toast.error(error.message, { ...defaultOptions });
    } else {
      toast.error('Erro desconhecido', { ...defaultOptions });
    }
  },

  /**
   * Notificação de operação em andamento
   */
  loading(message: string) {
    return toast.loading(message);
  },

  /**
   * Atualiza uma notificação existente
   */
  update(toastId: any, type: 'success' | 'error' | 'info' | 'warning', message: string) {
    toast.update(toastId, {
      render: message,
      type,
      isLoading: false,
      autoClose: 4000,
      closeButton: true,
    });
  },

  /**
   * Remove uma notificação específica
   */
  dismiss(toastId?: any) {
    if (toastId) {
      toast.dismiss(toastId);
    } else {
      toast.dismiss();
    }
  },
};
