import { FiUsers, FiPackage, FiShoppingCart, FiDollarSign, FiAlertCircle } from 'react-icons/fi';
import './DashboardPage.scss';

// Dados mockados (serão substituídos por dados reais da API)
const mockStats = [
  {
    id: 1,
    title: 'Vendas do Mês',
    value: 'R$ 45.230,00',
    change: '+12%',
    changeType: 'positive' as const,
    icon: <FiDollarSign />,
    color: 'primary',
  },
  {
    id: 2,
    title: 'Clientes Ativos',
    value: '234',
    change: '+8',
    changeType: 'positive' as const,
    icon: <FiUsers />,
    color: 'secondary',
  },
  {
    id: 3,
    title: 'Produtos Cadastrados',
    value: '156',
    change: '+5',
    changeType: 'positive' as const,
    icon: <FiPackage />,
    color: 'success',
  },
  {
    id: 4,
    title: 'Pedidos Pendentes',
    value: '12',
    change: '-3',
    changeType: 'negative' as const,
    icon: <FiShoppingCart />,
    color: 'warning',
  },
];

const mockAlerts = [
  {
    id: 1,
    type: 'warning',
    message: '5 produtos com estoque baixo',
    action: 'Ver produtos',
  },
  {
    id: 2,
    type: 'error',
    message: '3 contas vencidas',
    action: 'Ver contas',
  },
  {
    id: 3,
    type: 'info',
    message: '8 pedidos aguardando confirmação',
    action: 'Ver pedidos',
  },
];

const DashboardPage = () => {
  return (
    <div className="dashboard-page">
      {/* Header */}
      <div className="dashboard-header">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="page-subtitle">Visão geral do seu negócio</p>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="stats-grid">
        {mockStats.map((stat) => (
          <div key={stat.id} className={`stat-card stat-${stat.color}`}>
            <div className="stat-icon">{stat.icon}</div>
            <div className="stat-content">
              <p className="stat-title">{stat.title}</p>
              <h3 className="stat-value">{stat.value}</h3>
              <span className={`stat-change ${stat.changeType}`}>{stat.change} vs mês anterior</span>
            </div>
          </div>
        ))}
      </div>

      {/* Alerts Section */}
      <div className="alerts-section">
        <h2 className="section-title">
          <FiAlertCircle />
          Alertas e Notificações
        </h2>
        <div className="alerts-list">
          {mockAlerts.map((alert) => (
            <div key={alert.id} className={`alert-item alert-${alert.type}`}>
              <div className="alert-content">
                <FiAlertCircle className="alert-icon" />
                <span className="alert-message">{alert.message}</span>
              </div>
              <button className="alert-action">{alert.action}</button>
            </div>
          ))}
        </div>
      </div>

      {/* Placeholder para gráficos */}
      <div className="charts-section">
        <div className="chart-card">
          <h3 className="chart-title">Vendas dos Últimos 7 Dias</h3>
          <div className="chart-placeholder">
            <p className="text-muted">Gráfico será implementado em breve</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
