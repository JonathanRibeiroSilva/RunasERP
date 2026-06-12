import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { FiArrowLeft, FiPackage, FiSearch } from 'react-icons/fi';
import axios from 'axios';
import './MeusPedidosPage.scss';

const apiPublica = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

// Types
interface Pedido {
  id: string;
  numero_venda: string;
  status: string;
  valor_total: number;
  data_pedido: string;
  tipo_entrega: string;
}

const STATUS_INFO: Record<string, { label: string; color: string }> = {
  PEDIDO: { label: 'Pedido Recebido', color: '#6c757d' },
  PENDENTE: { label: 'Aguardando Pagamento', color: '#ffc107' },
  CONFIRMADA: { label: 'Pagamento Confirmado', color: '#17a2b8' },
  SEPARADA: { label: 'Em Separação', color: '#fd7e14' },
  EM_ENTREGA: { label: 'Em Entrega', color: '#0dcaf0' },
  ENTREGUE: { label: 'Entregue', color: '#28a745' },
  FINALIZADA: { label: 'Finalizada', color: '#198754' },
  CANCELADA: { label: 'Cancelada', color: '#dc3545' },
  REEMBOLSADA: { label: 'Reembolsada', color: '#6f42c1' },
};

const MeusPedidosPage = () => {
  const { empresaSlug } = useParams<{ empresaSlug: string }>();
  const navigate = useNavigate();

  const [pedidos, setPedidos] = useState<Pedido[]>([]);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState('');
  const [statusFiltro, setStatusFiltro] = useState('');

  useEffect(() => {
    carregarPedidos();
  }, [statusFiltro]);

  const carregarPedidos = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({ limit: '50' });
      if (statusFiltro) params.append('status', statusFiltro);

      const response = await apiPublica.get(`/loja/meus-pedidos?${params}`);
      setPedidos(response.data.items || []);
    } catch (error: any) {
      setErro(error.response?.data?.detail || 'Erro ao carregar pedidos');
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
    }).format(data);
  };

  const handleVerPedido = (numeroPedido: string) => {
    navigate(`/c/${empresaSlug}/pedido/${numeroPedido}`);
  };

  return (
    <div className="meus-pedidos-page">
      {/* Header */}
      <header className="pedidos-header">
        <button className="btn-voltar" onClick={() => navigate(`/c/${empresaSlug}`)}>
          <FiArrowLeft /> Voltar ao catálogo
        </button>
        <h1>
          <FiPackage />
          Meus Pedidos
        </h1>
      </header>

      {/* Filtros */}
      <div className="filtros-section">
        <div className="filtro-item">
          <label>Filtrar por status:</label>
          <select
            value={statusFiltro}
            onChange={(e) => setStatusFiltro(e.target.value)}
          >
            <option value="">Todos os status</option>
            <option value="PEDIDO">Pedido Recebido</option>
            <option value="PENDENTE">Aguardando Pagamento</option>
            <option value="CONFIRMADA">Pagamento Confirmado</option>
            <option value="SEPARADA">Em Separação</option>
            <option value="EM_ENTREGA">Em Entrega</option>
            <option value="ENTREGUE">Entregue</option>
            <option value="FINALIZADA">Finalizada</option>
            <option value="CANCELADA">Cancelada</option>
          </select>
        </div>
      </div>

      {erro && (
        <div className="erro-mensagem">
          ⚠️ {erro}
        </div>
      )}

      {/* Conteúdo */}
      {loading ? (
        <div className="loading">
          <div className="spinner" />
          <p>Carregando pedidos...</p>
        </div>
      ) : pedidos.length === 0 ? (
        <div className="empty-state">
          <span className="empty-icon">📦</span>
          <h2>Nenhum pedido encontrado</h2>
          <p>Você ainda não realizou nenhuma compra</p>
          <button onClick={() => navigate(`/c/${empresaSlug}`)}>
            Ver produtos
          </button>
        </div>
      ) : (
        <div className="pedidos-container">
          <div className="pedidos-lista">
            {pedidos.map((pedido) => {
              const statusInfo = STATUS_INFO[pedido.status] || STATUS_INFO.PEDIDO;

              return (
                <div
                  key={pedido.id}
                  className="pedido-card"
                  onClick={() => handleVerPedido(pedido.numero_venda)}
                >
                  <div className="pedido-header">
                    <div className="pedido-numero">
                      <strong>#{pedido.numero_venda}</strong>
                      <span className="pedido-data">{formatarData(pedido.data_pedido)}</span>
                    </div>
                    <span
                      className="badge-status"
                      style={{ backgroundColor: statusInfo.color }}
                    >
                      {statusInfo.label}
                    </span>
                  </div>

                  <div className="pedido-info">
                    <div className="info-item">
                      <span className="info-label">Entrega:</span>
                      <span className="info-value">
                        {pedido.tipo_entrega === 'DELIVERY' ? 'Domicílio' : 'Retirada'}
                      </span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Total:</span>
                      <span className="info-value valor">{formatarPreco(pedido.valor_total)}</span>
                    </div>
                  </div>

                  <div className="pedido-footer">
                    <button className="btn-rastrear">
                      <FiSearch /> Rastrear pedido
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      <footer className="catalogo-footer">
        <p>Powered by <strong>Runas ERP</strong></p>
      </footer>
    </div>
  );
};

export default MeusPedidosPage;
