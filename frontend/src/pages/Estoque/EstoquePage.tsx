import { FiBox, FiPackage, FiTrendingUp, FiAlertTriangle } from 'react-icons/fi';
import './EstoquePage.scss';

const EstoquePage = () => {
  return (
    <div className="estoque-page">
      <div className="page-header">
        <div>
          <h1>
            <FiBox /> Estoque
          </h1>
          <p className="text-muted">Gestão de estoque e movimentações</p>
        </div>
      </div>

      <div className="coming-soon-container">
        <div className="coming-soon-icon">
          <FiBox size={80} />
        </div>
        <h2>Gestão de Estoque</h2>
        <p>Esta funcionalidade está em desenvolvimento e será implementada em breve.</p>
        
        <div className="features-preview">
          <div className="feature-card">
            <FiPackage size={32} />
            <h3>Controle de Estoque</h3>
            <p>Visualize e gerencie o estoque de todos os produtos</p>
          </div>
          
          <div className="feature-card">
            <FiTrendingUp size={32} />
            <h3>Movimentações</h3>
            <p>Entradas, saídas e transferências de mercadorias</p>
          </div>
          
          <div className="feature-card">
            <FiAlertTriangle size={32} />
            <h3>Alertas</h3>
            <p>Notificações de estoque baixo e rupturas</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EstoquePage;
