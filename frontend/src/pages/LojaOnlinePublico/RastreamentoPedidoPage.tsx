import { useState, useEffect } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { FiArrowLeft, FiPackage, FiCheck, FiClock, FiTruck, FiMapPin, FiCheckCircle, FiXCircle, FiAlertCircle } from 'react-icons/fi';
import { apiPublica } from '@/services/api/apiPublica';
import { Toast } from '@/utils/toast';
import './RastreamentoPedidoPage.scss';

// Types — alinhados ao contrato real de GET /loja/rastrear/{numero} (RastreamentoPedido).
// A API retorna um objeto PLANO (status_atual, valor_total, historico[...]), não { venda, itens }.
interface HistoricoItem {
  etapa: string;
  descricao: string | null;
  data: string;
  concluido: boolean;
  alterado_por: string | null;
}

interface RastreamentoDados {
  numero_venda: string;
  status_atual: string;
  data_pedido: string;
  data_confirmacao: string | null;
  data_separacao: string | null;
  data_entregue: string | null;
  data_finalizada: string | null;
  data_cancelada: string | null;
  tipo_entrega: string;
  valor_total: number | string; // Decimal serializado como string (ex.: "18.90")
  historico: HistoricoItem[];
  proxima_etapa: string | null;
  previsao_entrega: string | null;
}

const STATUS_INFO: Record<string, { label: string; color: string; icon: any }> = {
  PEDIDO: { label: 'Pedido Recebido', color: '#6c757d', icon: FiPackage },
  PENDENTE_PAGAMENTO: { label: 'Aguardando Pagamento', color: '#ffc107', icon: FiClock },
  CONFIRMADA: { label: 'Pagamento Confirmado', color: '#17a2b8', icon: FiCheck },
  SEPARADA: { label: 'Em Separação', color: '#fd7e14', icon: FiPackage },
  EM_ENTREGA: { label: 'Em Entrega', color: '#0dcaf0', icon: FiTruck },
  ENTREGUE: { label: 'Entregue', color: '#28a745', icon: FiMapPin },
  FINALIZADA: { label: 'Finalizada', color: '#198754', icon: FiCheck },
  CANCELADA: { label: 'Cancelada', color: '#dc3545', icon: FiArrowLeft },
  REEMBOLSADA: { label: 'Reembolsada', color: '#6f42c1', icon: FiArrowLeft },
};

const STATUS_ORDER = ['PEDIDO', 'PENDENTE_PAGAMENTO', 'CONFIRMADA', 'SEPARADA', 'EM_ENTREGA', 'ENTREGUE', 'FINALIZADA'];

// Enquanto o pedido está nesses status, o pagamento pode confirmar a qualquer momento via
// webhook assíncrono do Mercado Pago (às vezes segundos após o redirect de volta pra cá).
const STATUS_AGUARDANDO_PAGAMENTO = ['PEDIDO', 'PENDENTE_PAGAMENTO'];
const POLLING_INTERVALO_MS = 4000;
const POLLING_MAX_TENTATIVAS = 30; // ~2 minutos

const RastreamentoPedidoPage = () => {
  const { empresaSlug, numeroPedido } = useParams<{ empresaSlug: string; numeroPedido: string }>();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const [dados, setDados] = useState<RastreamentoDados | null>(null);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState('');
  const [mostrarAlertaPagamento, setMostrarAlertaPagamento] = useState(false);
  const [statusPagamento, setStatusPagamento] = useState<'success' | 'failure' | 'pending' | null>(null);

  // Detectar retorno do Mercado Pago e mostrar mensagem
  useEffect(() => {
    const status = searchParams.get('status') as 'success' | 'failure' | 'pending' | null;

    if (status) {
      setStatusPagamento(status);
      setMostrarAlertaPagamento(true);

      // Mostrar toast baseado no status
      if (status === 'success') {
        Toast.success('Pagamento aprovado! Seu pedido foi confirmado.');
      } else if (status === 'failure') {
        Toast.error('Pagamento recusado. Tente novamente ou escolha outro método.');
      } else if (status === 'pending') {
        Toast.info('Pagamento pendente. Você receberá uma notificação quando for confirmado.');
      }

      // Limpar parâmetro da URL após 5 segundos
      setTimeout(() => {
        setMostrarAlertaPagamento(false);
        searchParams.delete('status');
        setSearchParams(searchParams, { replace: true });
      }, 5000);
    }
  }, [searchParams, setSearchParams]);

  useEffect(() => {
    if (numeroPedido) carregarRastreamento();
  }, [numeroPedido]);

  // Enquanto o pedido aguarda confirmação de pagamento, faz polling silencioso — o webhook do
  // Mercado Pago pode confirmar segundos (ou minutos, no caso de cartão via 3DS) depois do
  // cliente já ter sido redirecionado de volta pra essa tela.
  useEffect(() => {
    if (!numeroPedido || !dados) return;
    if (!STATUS_AGUARDANDO_PAGAMENTO.includes(dados.status_atual)) return;

    let tentativas = 0;
    const intervalId = setInterval(async () => {
      tentativas += 1;
      if (tentativas > POLLING_MAX_TENTATIVAS) {
        clearInterval(intervalId);
        return;
      }
      await carregarRastreamento({ silencioso: true });
    }, POLLING_INTERVALO_MS);

    return () => clearInterval(intervalId);
  }, [numeroPedido, dados?.status_atual]);

  const carregarRastreamento = async ({ silencioso = false }: { silencioso?: boolean } = {}) => {
    try {
      if (!silencioso) setLoading(true);
      setErro('');
      const response = await apiPublica.get(`/loja/rastrear/${numeroPedido}?empresaSlug=${empresaSlug}`);
      setDados(response.data ?? null);
    } catch (error: any) {
      if (silencioso) return; // não substitui uma tela já carregada por um erro de poll em background
      setDados(null);
      const mensagemErro = error?.response?.data?.detail || 'Pedido não encontrado';
      // Se detail for um array, pegar a primeira mensagem
      if (Array.isArray(mensagemErro)) {
        setErro(mensagemErro[0]?.msg || 'Pedido não encontrado');
      } else if (typeof mensagemErro === 'object') {
        setErro(JSON.stringify(mensagemErro));
      } else {
        setErro(mensagemErro);
      }
    } finally {
      if (!silencioso) setLoading(false);
    }
  };

  const formatarPreco = (valor: number | string | null | undefined) => {
    const numero = Number(valor);
    if (!Number.isFinite(numero)) return 'R$ 0,00';
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(numero);
  };

  const formatarData = (dataStr: string | null | undefined) => {
    if (!dataStr) return '';
    const data = new Date(dataStr);
    if (Number.isNaN(data.getTime())) return '';
    return new Intl.DateTimeFormat('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(data);
  };

  const getStatusIndex = (status: string): number => {
    return STATUS_ORDER.indexOf(status);
  };

  // 1. Estado de carregamento (dados ainda não disponíveis ou requisição pendente)
  if (loading) {
    return (
      <div className="rastreamento-page">
        <div className="loading">
          <div className="spinner" />
          <p>Carregando pedido...</p>
        </div>
      </div>
    );
  }

  // 2. Estado de erro / pedido não encontrado (requisição concluída sem dados válidos)
  if (erro || !dados) {
    return (
      <div className="rastreamento-page">
        <div className="erro-state">
          <span className="erro-icon">😕</span>
          <h2>Pedido não encontrado</h2>
          {erro && <p>{erro}</p>}
          <button onClick={() => navigate(`/c/${empresaSlug}`)}>
            <FiArrowLeft /> Voltar ao catálogo
          </button>
        </div>
      </div>
    );
  }

  // 3. Render seguro — a partir daqui `dados` é garantidamente não-nulo.
  //    Todo acesso usa fallback defensivo para sobreviver a respostas parciais.
  const statusAtual = dados.status_atual ?? 'PEDIDO';
  const historico: HistoricoItem[] = Array.isArray(dados.historico) ? dados.historico : [];
  const ultimoHistorico = historico.length > 0 ? historico[historico.length - 1] : null;
  const statusInfo = STATUS_INFO[statusAtual] || STATUS_INFO.PEDIDO;
  const statusAtualIndex = getStatusIndex(statusAtual);
  const Icon = statusInfo.icon;

  const isCancelada = statusAtual === 'CANCELADA' || statusAtual === 'REEMBOLSADA';

  return (
    <div className="rastreamento-page">
      {/* Header */}
      <header className="rastreamento-header">
        <button className="btn-voltar" onClick={() => navigate(`/c/${empresaSlug}`)}>
          <FiArrowLeft /> Voltar ao catálogo
        </button>
        <div className="header-info">
          <h1>Pedido {dados.numero_venda}</h1>
          <span className="badge-status" style={{ backgroundColor: statusInfo.color }}>
            <Icon /> {statusInfo.label}
          </span>
        </div>
      </header>

      {/* Alerta de Status do Pagamento */}
      {mostrarAlertaPagamento && statusPagamento && (
        <div className={`alerta-pagamento ${statusPagamento}`}>
          {statusPagamento === 'success' && (
            <>
              <FiCheckCircle size={32} />
              <div className="alerta-conteudo">
                <h3>✅ Pagamento Aprovado!</h3>
                <p>Seu pedido foi confirmado e já está sendo processado. Você receberá atualizações sobre o status da entrega.</p>
              </div>
            </>
          )}
          {statusPagamento === 'failure' && (
            <>
              <FiXCircle size={32} />
              <div className="alerta-conteudo">
                <h3>❌ Pagamento Recusado</h3>
                <p>Não foi possível processar o pagamento. Entre em contato para tentar novamente ou escolha outro método de pagamento.</p>
              </div>
            </>
          )}
          {statusPagamento === 'pending' && (
            <>
              <FiAlertCircle size={32} />
              <div className="alerta-conteudo">
                <h3>⏳ Pagamento Pendente</h3>
                <p>Seu pagamento está sendo processado. Você receberá uma notificação quando for confirmado (geralmente em alguns minutos para PIX).</p>
              </div>
            </>
          )}
        </div>
      )}

      <div className="rastreamento-container">
        {/* Timeline de Status */}
        <div className="timeline-section">
          <h2>Acompanhe seu pedido</h2>

          {!isCancelada ? (
            <div className="timeline">
              {STATUS_ORDER.slice(0, -1).map((status, index) => {
                const info = STATUS_INFO[status] || STATUS_INFO.PEDIDO;
                const StepIcon = info.icon;
                const isCompleted = statusAtualIndex >= 0 && index <= statusAtualIndex;
                const isActive = index === statusAtualIndex;

                return (
                  <div key={status} className="timeline-step">
                    <div className={`timeline-marker ${isCompleted ? 'completed' : ''} ${isActive ? 'active' : ''}`}>
                      {isCompleted ? <FiCheck /> : <StepIcon />}
                    </div>
                    <div className="timeline-content">
                      <h4>{info.label}</h4>
                      {isActive && ultimoHistorico && (
                        <p className="timeline-date">{formatarData(ultimoHistorico.data)}</p>
                      )}
                    </div>
                    {index < STATUS_ORDER.length - 2 && (
                      <div className={`timeline-line ${index < statusAtualIndex ? 'completed' : ''}`} />
                    )}
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="status-cancelado">
              <Icon size={48} color={statusInfo.color} />
              <h3>{statusInfo.label}</h3>
              {(ultimoHistorico?.descricao || dados.proxima_etapa) && (
                <p>{ultimoHistorico?.descricao || dados.proxima_etapa}</p>
              )}
            </div>
          )}
        </div>

        {/* Detalhes do Pedido */}
        <div className="detalhes-section">
          <h3>Detalhes do pedido</h3>

          {/* Informações Gerais */}
          <div className="info-card">
            <div className="info-row">
              <span className="info-label">Data do pedido:</span>
              <span className="info-value">{formatarData(dados.data_pedido)}</span>
            </div>
            <div className="info-row">
              <span className="info-label">Tipo de entrega:</span>
              <span className="info-value">
                {dados.tipo_entrega === 'DELIVERY' ? 'Entrega em domicílio' : 'Retirada no local'}
              </span>
            </div>
            {dados.previsao_entrega && (
              <div className="info-row">
                <span className="info-label">Previsão de entrega:</span>
                <span className="info-value">{dados.previsao_entrega}</span>
              </div>
            )}
          </div>

          {/* Total */}
          <div className="total-pedido">
            <span>Total do pedido</span>
            <strong>{formatarPreco(dados.valor_total)}</strong>
          </div>

          {/* Histórico */}
          {historico.length > 0 && (
            <div className="historico-section">
              <h4>Histórico de alterações</h4>
              <div className="historico-lista">
                {historico.slice().reverse().map((item, index) => (
                  <div key={index} className="historico-item">
                    <span className="historico-data">{formatarData(item.data)}</span>
                    <div className="historico-mudanca">
                      <span className="status-novo">{STATUS_INFO[item.etapa]?.label || item.etapa}</span>
                    </div>
                    {item.descricao && <p className="historico-obs">{item.descricao}</p>}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      <footer className="loja-online-footer">
        <p>Powered by <strong>Runas ERP</strong></p>
      </footer>
    </div>
  );
};

export default RastreamentoPedidoPage;
