import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { FiPackage, FiSearch, FiCreditCard, FiShoppingCart, FiFilter } from 'react-icons/fi';
import { apiPublica } from '@/services/api/apiPublica';
import { getErrorMessage, getErrorStatus } from '@/services/api/axios';
import { toast } from 'react-toastify';
import ClienteLayout from './components/ClienteLayout';
import './MeusPedidosPage.scss';

// Types
interface Pedido {
  id: string;
  numero_venda: string;
  status: string;
  valor_total: number;
  data_pedido: string;
  tipo_entrega: string;
  quantidade_itens: number;
}

const STATUS_INFO: Record<string, { label: string; color: string; canRetry: boolean; canEdit: boolean }> = {
  PEDIDO: { label: 'Pedido Recebido', color: '#6c757d', canRetry: true, canEdit: true },
  PENDENTE_PAGAMENTO: { label: 'Aguardando Pagamento', color: '#ffc107', canRetry: true, canEdit: true },
  CONFIRMADA: { label: 'Pagamento Confirmado', color: '#17a2b8', canRetry: false, canEdit: false },
  SEPARADA: { label: 'Em Separação', color: '#fd7e14', canRetry: false, canEdit: false },
  EM_ENTREGA: { label: 'Em Entrega', color: '#0dcaf0', canRetry: false, canEdit: false },
  ENTREGUE: { label: 'Entregue', color: '#28a745', canRetry: false, canEdit: false },
  FINALIZADA: { label: 'Finalizada', color: '#198754', canRetry: false, canEdit: false },
  CANCELADA: { label: 'Cancelada', color: '#dc3545', canRetry: false, canEdit: false },
  REEMBOLSADA: { label: 'Reembolsada', color: '#6f42c1', canRetry: false, canEdit: false },
};

const MeusPedidosPage = () => {
  const { empresaSlug } = useParams<{ empresaSlug: string }>();
  const navigate = useNavigate();

  const [pedidos, setPedidos] = useState<Pedido[]>([]);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState('');
  const [statusFiltro, setStatusFiltro] = useState('');
  const [processando, setProcessando] = useState<string | null>(null); // ID do pedido sendo processado

  useEffect(() => {
    carregarPedidos();
  }, [statusFiltro]);

  const carregarPedidos = async () => {
    try {
      setLoading(true);
      setErro('');
      
      const params = new URLSearchParams({
        empresaSlug: empresaSlug || '',
        limit: '50',
      });
      
      if (statusFiltro) params.append('status', statusFiltro);

      const response = await apiPublica.get(`/loja/meus-pedidos?${params}`);
      setPedidos(response.data || []);
    } catch (error) {
      console.error('Erro ao carregar pedidos:', error);
      
      if (getErrorStatus(error) === 401) {
        setErro('Você precisa estar logado para ver seus pedidos. Redirecionando...');
        setTimeout(() => {
          navigate(`/c/${empresaSlug}/login`, { state: { from: window.location.pathname } });
        }, 2000);
      } else {
        setErro(getErrorMessage(error, 'Erro ao carregar pedidos'));
      }
    } finally {
      setLoading(false);
    }
  };

  const handleRetryPayment = async (pedido: Pedido, event: React.MouseEvent) => {
    event.stopPropagation(); // Evitar click no card
    
    try {
      setProcessando(pedido.id);
      
      const response = await apiPublica.post(
        `/loja/pedidos/${pedido.numero_venda}/retry-payment?empresaSlug=${empresaSlug}`
      );
      
      if (response.data.mercadopago_url) {
        toast.success('Redirecionando para pagamento...');
        
        // Redirecionar para Mercado Pago
        window.location.href = response.data.mercadopago_url;
      } else {
        toast.error('Erro ao gerar link de pagamento');
      }
    } catch (error) {
      console.error('Erro ao tentar pagamento:', error);
      toast.error(getErrorMessage(error, 'Erro ao gerar link de pagamento'));
    } finally {
      setProcessando(null);
    }
  };

  const handleRecuperarCarrinho = async (pedido: Pedido, event: React.MouseEvent) => {
    event.stopPropagation(); // Evitar click no card
    
    try {
      setProcessando(pedido.id);
      
      const response = await apiPublica.post(
        `/loja/pedidos/${pedido.numero_venda}/recuperar-carrinho?empresaSlug=${empresaSlug}`
      );
      
      if (response.data.success) {
        const { itens_adicionados, itens_sem_estoque } = response.data;
        
        // Mostrar avisos sobre itens sem estoque
        if (itens_sem_estoque && itens_sem_estoque.length > 0) {
          toast.warning(
            `${itens_adicionados} item(ns) adicionado(s) ao carrinho. ` +
            `${itens_sem_estoque.length} item(ns) não estão mais disponíveis.`,
            { autoClose: 5000 }
          );
        } else {
          toast.success(`Carrinho recuperado! ${itens_adicionados} item(ns) adicionado(s).`);
        }
        
        // Redirecionar para carrinho
        navigate(`/c/${empresaSlug}/carrinho`);
      }
    } catch (error) {
      console.error('Erro ao recuperar carrinho:', error);
      toast.error(getErrorMessage(error, 'Erro ao recuperar carrinho'));
    } finally {
      setProcessando(null);
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
    <ClienteLayout title="Meus Pedidos">
      <div className="meus-pedidos-content">
        {/* Filtros */}
        <div className="filtros-section">
          <div className="filtro-item">
            <FiFilter />
            <label>Status:</label>
            <select
              value={statusFiltro}
              onChange={(e) => setStatusFiltro(e.target.value)}
            >
              <option value="">Todos</option>
              <option value="PEDIDO">Pedido Recebido</option>
              <option value="PENDENTE_PAGAMENTO">Aguardando Pagamento</option>
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
          <div className="pedidos-lista">
            {pedidos.map((pedido) => {
              const statusInfo = STATUS_INFO[pedido.status] || STATUS_INFO.PEDIDO;
              const isProcessando = processando === pedido.id;

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
                      <span className="info-label">Itens:</span>
                      <span className="info-value">
                        {pedido.quantidade_itens || 0} {pedido.quantidade_itens === 1 ? 'item' : 'itens'}
                      </span>
                    </div>
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
                    <button className="btn-rastrear" onClick={(e) => {
                      e.stopPropagation();
                      handleVerPedido(pedido.numero_venda);
                    }}>
                      <FiSearch /> Rastrear pedido
                    </button>
                    
                    {/* Botão Tentar Pagamento Novamente */}
                    {statusInfo.canRetry && (
                      <button
                        className="btn-retry-payment"
                        onClick={(e) => handleRetryPayment(pedido, e)}
                        disabled={isProcessando}
                      >
                        {isProcessando ? (
                          <>
                            <div className="spinner-small" />
                            Processando...
                          </>
                        ) : (
                          <>
                            <FiCreditCard /> Tentar Pagamento
                          </>
                        )}
                      </button>
                    )}
                    
                    {/* Botão Editar Pedido */}
                    {statusInfo.canEdit && (
                      <button
                        className="btn-edit-order"
                        onClick={(e) => handleRecuperarCarrinho(pedido, e)}
                        disabled={isProcessando}
                        title="Recuperar carrinho para editar pedido"
                      >
                        {isProcessando ? (
                          <>
                            <div className="spinner-small" />
                            Carregando...
                          </>
                        ) : (
                          <>
                            <FiShoppingCart /> Editar Pedido
                          </>
                        )}
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </ClienteLayout>
  );
};

export default MeusPedidosPage;
