import { FiDollarSign, FiTrendingUp, FiTrendingDown, FiPieChart } from 'react-icons/fi';
import './FinanceiroPage.scss';

const FinanceiroPage = () => {
  return (
    <div className="financeiro-page">
      <div className="page-header">
        <div>
          <h1>
            <FiDollarSign /> Financeiro
          </h1>
          <p className="text-muted">Gestão financeira e fluxo de caixa</p>
        </div>
      </div>

      <div className="coming-soon-container">
        <div className="coming-soon-icon">
          <FiDollarSign size={80} />
        </div>
        <h2>Gestão Financeira</h2>
        <p>Esta funcionalidade está em desenvolvimento e será implementada em breve.</p>
        
        <div className="features-preview">
          <div className="feature-card">
            <FiTrendingUp size={32} />
            <h3>Contas a Receber</h3>
            <p>Controle de pagamentos pendentes de clientes</p>
          </div>
          
          <div className="feature-card">
            <FiTrendingDown size={32} />
            <h3>Contas a Pagar</h3>
            <p>Gestão de despesas e fornecedores</p>
          </div>
          
          <div className="feature-card">
            <FiPieChart size={32} />
            <h3>Fluxo de Caixa</h3>
            <p>Visualização completa das movimentações financeiras</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FinanceiroPage;
