import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { FiArrowLeft, FiPackage, FiCheck, FiClock, FiTruck, FiMapPin } from 'react-icons/fi';
import axios from 'axios';
import './RastreamentoPedidoPage.scss';

const apiPublica = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

// Types
interface ItemVenda {
  id: string;
  produto_nome: string;
  variante_sku: string;
  quantidade: number;
  preco_unitario: number;
  subtotal: number;
}

interface HistoricoStatus {
  status_anterior: string | null;
  status_novo: string;
  alterado_em: string;
  observacao: string | null;
}

interface Venda {
  id: string;
  numero_venda: string;
  status: string;
  valor_total: number;
  tipo_entrega: string;
  data_pedido: string;
  observacao?: string;
}

interface RastreamentoDados {
  venda: Venda;
  itens: ItemVenda[];
  historico: HistoricoStatus[];
}

const STATUS_INFO: Record<string, { label: string; color: string; icon: any }> = {
  PEDIDO: { label: 'Pedido Recebido', color: '#6c757d', icon: FiPackage },
  PENDENTE: { label: 'Aguardando Pagamento', color: '#ffc107', icon: FiClock },
  CONFIRMADA: { label: 'Pagamento Confirmado', color: '#17a2b8', icon: FiCheck },
  SEPARADA: { label: 'Em Separação', color: '#fd7e14', icon: FiPackage },
  EM_ENTREGA: { label: 'Em Entrega', color: '#0dcaf0', icon: FiTruck },
  ENTREGUE: { label: 'Entregue', color: '#28a745', icon: FiMapPin },
  FINALIZADA: { label: 'Finalizada', color: '#198754', icon: FiCheck },
  CANCELADA: { label: 'Cancelada', color: '#dc3545', icon: FiArrowLeft },
  REEMBOLSADA: { label: 'Reembolsada', color: '#6f42c1', icon: FiArrowLeft },
};

const STATUS_ORDER = ['PEDIDO', 'PENDENTE', 'CONFIRMADA', 'SEPARADA', 'EM_ENTREGA', 'ENTREGUE', 'FINALIZADA'];

const RastreamentoPedidoPage = () => {
  const { empresaSlug, numeroPedido } = useParams<{ empresaSlug: string; numeroPedido: string }>();
  const navigate = useNavigate();

  const [dados, setDados] = useState<RastreamentoDados | null>(null);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState('');

  useEffect(() => {
    if (numeroPedido) carregarRastreamento();
  }, [numeroPedido]);

  const carregarRastreamento = async () => {
    try {
      setLoading(true);
      const response = await apiPublica.get(`/loja/rastrear/${numeroPedido}?empresaSlug=${empresaSlug}`);
      setDados(response.data);
    } catch (error: any) {
      const mensagemErro = error.response?.data?.detail || 'Pedido não encontrado';
      // Se detail for um array, pegar a primeira mensagem
      if (Array.isArray(mensagemErro)) {
        setErro(mensagemErro[0]?.msg || 'Pedido não encontrado');
      } else if (typeof mensagemErro === 'object') {
        setErro(JSON.stringify(mensagemErro));
      } else {
        setErro(mensagemErro);
      }
    } finally {
      setLoading(false);
    }
  };

  const formatarPreco = (valor: number) =>
    new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valor);

  const formatarData = (dataStr: string) => {
    const data = new Date(dataStr);
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

  if (erro || !dados) {
    return (
      <div className="rastreamento-page">
        <div className="erro-state">
          <span className="erro-icon">😕</span>
          <h2>Pedido não encontrado</h2>
          <p>{erro}</p>
          <button onClick={() => navigate(`/c/${empresaSlug}`)}>
            <FiArrowLeft /> Voltar ao catálogo
          </button>
        </div>
      </div>
    );
  }

  const { venda, itens, historico } = dados;
  const statusInfo = STATUS_INFO[venda.status] || STATUS_INFO.PEDIDO;
  const statusAtualIndex = getStatusIndex(venda.status);
  const Icon = statusInfo.icon;

  const isCancelada = venda.status === 'CANCELADA' || venda.status === 'REEMBOLSADA';

  return (
    <div className="rastreamento-page">
      {/* Header */}
      <header className="rastreamento-header">
        <button className="btn-voltar" onClick={() => navigate(`/c/${empresaSlug}`)}>
          <FiArrowLeft /> Voltar ao catálogo
        </button>
        <div className="header-info">
          <h1>Pedido {venda.numero_venda}</h1>
          <span className="badge-status" style={{ backgroundColor: statusInfo.color }}>
            <Icon /> {statusInfo.label}
          </span>
        </div>
      </header>

      <div className="rastreamento-container">
        {/* Timeline de Status */}
        <div className="timeline-section">
          <h2>Acompanhe seu pedido</h2>

          {!isCancelada ? (
            <div className="timeline">
              {STATUS_ORDER.slice(0, -1).map((status, index) => {
                const info = STATUS_INFO[status];
                const StepIcon = info.icon;
                const isCompleted = index <= statusAtualIndex;
                const isActive = index === statusAtualIndex;

                return (
                  <div key={status} className="timeline-step">
                    <div className={`timeline-marker ${isCompleted ? 'completed' : ''} ${isActive ? 'active' : ''}`}>
                      {isCompleted ? <FiCheck /> : <StepIcon />}
                    </div>
                    <div className="timeline-content">
                      <h4>{info.label}</h4>
                      {isActive && historico.length > 0 && (
                        <p className="timeline-date">{formatarData(historico[historico.length - 1].alterado_em)}</p>
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
              {historico.length > 0 && historico[historico.length - 1].observacao && (
                <p>{historico[historico.length - 1].observacao}</p>
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
              <span className="info-value">{formatarData(venda.data_pedido)}</span>
            </div>
            <div className="info-row">
              <span className="info-label">Tipo de entrega:</span>
              <span className="info-value">
                {venda.tipo_entrega === 'DELIVERY' ? 'Entrega em domicílio' : 'Retirada no local'}
              </span>
            </div>
            {venda.observacao && (
              <div className="info-row">
                <span className="info-label">Observação:</span>
                <span className="info-value">{venda.observacao}</span>
              </div>
            )}
          </div>

          {/* Itens */}
          <h4>Itens do pedido</h4>
          <div className="itens-lista">
            {itens.map((item) => (
              <div key={item.id} className="item-pedido">
                <div className="item-info">
                  <span className="item-quantidade">{item.quantidade}x</span>
                  <div className="item-detalhes">
                    <strong>{item.produto_nome}</strong>
                    <small>SKU: {item.variante_sku}</small>
                  </div>
                </div>
                <span className="item-preco">{formatarPreco(item.subtotal)}</span>
              </div>
            ))}
          </div>

          {/* Total */}
          <div className="total-pedido">
            <span>Total do pedido</span>
            <strong>{formatarPreco(venda.valor_total)}</strong>
          </div>

          {/* Histórico */}
          {historico.length > 0 && (
            <div className="historico-section">
              <h4>Histórico de alterações</h4>
              <div className="historico-lista">
                {historico.slice().reverse().map((item, index) => (
                  <div key={index} className="historico-item">
                    <span className="historico-data">{formatarData(item.alterado_em)}</span>
                    <div className="historico-mudanca">
                      {item.status_anterior && (
                        <span className="status-anterior">{STATUS_INFO[item.status_anterior]?.label}</span>
                      )}
                      {item.status_anterior && <span className="arrow">→</span>}
                      <span className="status-novo">{STATUS_INFO[item.status_novo]?.label}</span>
                    </div>
                    {item.observacao && <p className="historico-obs">{item.observacao}</p>}
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
