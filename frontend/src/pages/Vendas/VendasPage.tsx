import { FiShoppingCart, FiDollarSign, FiTrendingUp, FiClock } from 'react-icons/fi';
import './VendasPage.scss';

const VendasPage = () => {
  return (
    <div className="vendas-page">
      <div className="page-header">
        <div>
          <h1>
            <FiShoppingCart /> Vendas
          </h1>
          <p className="text-muted">Ponto de venda e gestão de pedidos</p>
        </div>
      </div>

      <div className="coming-soon-container">
        <div className="coming-soon-icon">
          <FiShoppingCart size={80} />
        </div>
        <h2>Gestão de Vendas</h2>
        <p>Esta funcionalidade está em desenvolvimento e será implementada em breve.</p>
        
        <div className="features-preview">
          <div className="feature-card">
            <FiShoppingCart size={32} />
            <h3>Ponto de Venda (PDV)</h3>
            <p>Sistema completo para registrar vendas rapidamente</p>
          </div>
          
          <div className="feature-card">
            <FiClock size={32} />
            <h3>Histórico de Vendas</h3>
            <p>Acompanhe todas as vendas realizadas</p>
          </div>
          
          <div className="feature-card">
            <FiTrendingUp size={32} />
            <h3>Relatórios</h3>
            <p>Análise de desempenho e vendas por período</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VendasPage;
