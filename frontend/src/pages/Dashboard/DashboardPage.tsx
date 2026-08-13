import { FiUsers, FiPackage, FiShoppingCart, FiDollarSign, FiArrowUpRight, FiArrowDownRight } from 'react-icons/fi';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Filler,
  Legend,
} from 'chart.js';
import { Line, Doughnut } from 'react-chartjs-2';
import './DashboardPage.scss';

// Register ChartJS
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Filler,
  Legend
);

// ── MOCK DATA ──────────────────────────────────────────────────────────────────

const mockStats = [
  { id: 1, title: 'Vendas do Mês', value: 'R$ 45.230,00', change: '+12%', changeType: 'positive', icon: <FiDollarSign />, color: 'primary' },
  { id: 2, title: 'Clientes Ativos', value: '234', change: '+8', changeType: 'positive', icon: <FiUsers />, color: 'secondary' },
  { id: 3, title: 'Produtos Cadastrados', value: '156', change: '+5', changeType: 'positive', icon: <FiPackage />, color: 'success' },
  { id: 4, title: 'Pedidos Pendentes', value: '12', change: '-3', changeType: 'negative', icon: <FiShoppingCart />, color: 'warning' },
];

const vendasRecentes = [
  { cliente: 'Carlos Eduardo Pereira',        data: '14/07/2025', pagamento: 'PIX',           valor: 4520.00, status: 'Confirmada' },
  { cliente: 'Ana Paula Costa',                data: '14/07/2025', pagamento: 'Cartão Crédito',valor: 1870.50, status: 'Confirmada' },
  { cliente: 'Restaurante Sabor do Brasil Ltda', data: '13/07/2025', pagamento: 'Boleto',      valor: 8750.00, status: 'Confirmada' },
  { cliente: 'Juliana Ferreira Lima',          data: '12/07/2025', pagamento: 'Dinheiro',      valor: 3200.00, status: 'Confirmada' },
  { cliente: 'Roberto Carlos Souza',           data: '14/07/2025', pagamento: 'PIX',           valor: 5600.00, status: 'Pendente' },
  { cliente: 'Fernanda Cristina Rocha',        data: '11/07/2025', pagamento: 'Cartão Débito', valor: 2100.00, status: 'Confirmada' },
  { cliente: 'Carlos Eduardo Pereira',        data: '10/07/2025', pagamento: 'Boleto',        valor: 6800.00, status: 'Entregue' },
  { cliente: 'Ana Paula Costa',                data: '09/07/2025', pagamento: 'Fiado',         valor: 1250.00, status: 'Pendente' },
];

const topProdutos = [
  { nome: 'Arroz Tipo 1 5kg',     vendas: 570 },
  { nome: 'Leite Integral 1L',    vendas: 480 },
  { nome: 'Açúcar Cristal 1kg',   vendas: 450 },
  { nome: 'Café Torrado 500g',    vendas: 330 },
  { nome: 'Banana Prata kg',      vendas: 310 },
];

const categoriasVendas = [
  { nome: 'Alimentos', valor: 43, cor: '#3B82F6' },
  { nome: 'Bebidas',   valor: 24, cor: '#10B981' },
  { nome: 'Limpeza',   valor: 15, cor: '#F59E0B' },
  { nome: 'Higiene',   valor: 11, cor: '#8B5CF6' },
  { nome: 'Outros',    valor: 7,  cor: '#EF4444' },
];

// ── CHART CONFIG ───────────────────────────────────────────────────────────────

const lineChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: true,
      position: 'top' as const,
      align: 'end' as const,
      labels: {
        color: '#94A3B8',
        font: { size: 12 },
        usePointStyle: true,
        pointStyle: 'circle',
        padding: 20,
      },
    },
    tooltip: {
      mode: 'index' as const,
      intersect: false,
      backgroundColor: 'rgba(16, 20, 29, 0.95)',
      titleColor: '#94A3B8',
      bodyColor: '#FFFFFF',
      borderColor: 'rgba(255, 255, 255, 0.1)',
      borderWidth: 1,
      padding: 12,
      displayColors: false,
      callbacks: {
        label: (ctx: any) => `R$ ${ctx.parsed.y.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`,
      },
    },
  },
  scales: {
    x: {
      grid: { display: false },
      ticks: { color: '#64748B', font: { size: 12 } },
      border: { display: false },
    },
    y: {
      grid: { color: 'rgba(255, 255, 255, 0.04)' },
      ticks: {
        color: '#64748B',
        font: { size: 11 },
        callback: (value: any) => `${(value / 1000).toFixed(0)}k`,
      },
      border: { display: false },
    },
  },
  interaction: {
    mode: 'nearest' as const,
    axis: 'x' as const,
    intersect: false,
  },
};

const lineChartData = {
  labels: ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'],
  datasets: [
    {
      fill: true,
      label: 'Vendas',
      data: [1200, 1900, 1500, 2200, 1800, 2800, 2400],
      borderColor: '#0EA5E9',
      backgroundColor: 'rgba(14, 165, 233, 0.08)',
      borderWidth: 2,
      tension: 0.4,
      pointBackgroundColor: '#0EA5E9',
      pointBorderColor: '#10141D',
      pointBorderWidth: 2,
      pointRadius: 0,
      pointHoverRadius: 5,
    },
  ],
};

const doughnutOptions = {
  responsive: true,
  maintainAspectRatio: false,
  cutout: '70%',
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: 'rgba(16, 20, 29, 0.95)',
      titleColor: '#94A3B8',
      bodyColor: '#FFFFFF',
      borderColor: 'rgba(255, 255, 255, 0.1)',
      borderWidth: 1,
      padding: 10,
      callbacks: {
        label: (ctx: any) => `${ctx.label}: ${ctx.parsed}%`,
      },
    },
  },
};

const doughnutData = {
  labels: categoriasVendas.map(c => c.nome),
  datasets: [
    {
      data: categoriasVendas.map(c => c.valor),
      backgroundColor: categoriasVendas.map(c => c.cor),
      borderColor: 'transparent',
      borderWidth: 2,
      hoverBorderColor: '#fff',
      hoverBorderWidth: 2,
    },
  ],
};

// ── HELPERS ─────────────────────────────────────────────────────────────────────

const formatarMoeda = (valor: number) =>
  new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valor);

const getStatusClass = (status: string) => {
  switch (status) {
    case 'Confirmada': return 'status-confirmada';
    case 'Pendente':   return 'status-pendente';
    case 'Entregue':   return 'status-entregue';
    default:           return '';
  }
};

const topBarColors = ['#0EA5E9', '#6366F1', '#10B981', '#F59E0B', '#EF4444'];

// ── COMPONENT ──────────────────────────────────────────────────────────────────

const DashboardPage = () => {
  const maxVendas = topProdutos[0]?.vendas || 1;

  return (
    <div className="dashboard-page">
      {/* ── STATS CARDS ── */}
      <div className="stats-grid">
        {mockStats.map((stat) => (
          <div key={stat.id} className={`stat-card stat-${stat.color}`}>
            <div className="stat-icon-wrapper">
              <div className="stat-icon">{stat.icon}</div>
            </div>
            <div className="stat-content">
              <p className="stat-title">{stat.title}</p>
              <h3 className="stat-value font-mono">{stat.value}</h3>
              <div className={`stat-change-wrapper ${stat.changeType}`}>
                {stat.changeType === 'positive' ? <FiArrowUpRight /> : <FiArrowDownRight />}
                <span className="stat-change">{stat.change} vs mês anterior</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* ── TOP ROW: Charts ── */}
      <div className="dash-top-row">
        {/* Line Chart */}
        <div className="dash-card dash-chart-line">
          <div className="dash-card-header">
            <h3>Vendas dos Últimos 7 Dias</h3>
          </div>
          <div className="dash-chart-container">
            <Line options={lineChartOptions as any} data={lineChartData} />
          </div>
        </div>

        {/* Doughnut Chart */}
        <div className="dash-card dash-chart-donut">
          <div className="dash-card-header">
            <h3>Vendas por Categoria</h3>
          </div>
          <div className="dash-donut-wrapper">
            <div className="dash-donut-chart">
              <Doughnut options={doughnutOptions as any} data={doughnutData} />
              <div className="dash-donut-center">
                <span className="donut-label">Alimentos</span>
                <span className="donut-value">R$ 15.000,00</span>
              </div>
            </div>
            <div className="dash-donut-legend">
              {categoriasVendas.map((cat) => (
                <div key={cat.nome} className="legend-item">
                  <span className="legend-dot" style={{ background: cat.cor }} />
                  <span className="legend-name">{cat.nome}</span>
                  <span className="legend-pct">{cat.valor}%</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ── BOTTOM ROW: Table + Top Produtos ── */}
      <div className="dash-bottom-row">
        {/* Vendas Recentes */}
        <div className="dash-card dash-vendas-recentes">
          <div className="dash-card-header">
            <h3>Vendas Recentes</h3>
          </div>
          <div className="dash-table-wrapper">
            <table className="dash-table">
              <thead>
                <tr>
                  <th>CLIENTE</th>
                  <th>DATA</th>
                  <th>PAGAMENTO</th>
                  <th>VALOR</th>
                  <th>STATUS</th>
                </tr>
              </thead>
              <tbody>
                {vendasRecentes.map((venda, i) => (
                  <tr key={i}>
                    <td>{venda.cliente}</td>
                    <td>{venda.data}</td>
                    <td>{venda.pagamento}</td>
                    <td className="valor">{formatarMoeda(venda.valor)}</td>
                    <td>
                      <span className={`dash-status ${getStatusClass(venda.status)}`}>
                        {venda.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Top Produtos */}
        <div className="dash-card dash-top-produtos">
          <div className="dash-card-header">
            <h3>Top Produtos</h3>
          </div>
          <div className="dash-top-list">
            {topProdutos.map((prod, i) => (
              <div key={prod.nome} className="top-item">
                <div className="top-rank" style={{ background: `${topBarColors[i]}20`, color: topBarColors[i] }}>
                  #{i + 1}
                </div>
                <div className="top-info">
                  <span className="top-name">{prod.nome}</span>
                  <div className="top-bar-track">
                    <div
                      className="top-bar-fill"
                      style={{
                        width: `${(prod.vendas / maxVendas) * 100}%`,
                        background: topBarColors[i],
                      }}
                    />
                  </div>
                </div>
                <span className="top-count">{prod.vendas} vendas</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
