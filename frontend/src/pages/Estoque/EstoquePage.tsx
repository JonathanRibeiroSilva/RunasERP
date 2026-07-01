import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FiBox,
  FiSearch,
  FiEye,
  FiPlus,
  FiMinus,
  FiEdit2,
  FiArrowUp,
  FiArrowDown,
  FiPackage,
  FiLayers,
  FiAlertTriangle,
  FiXCircle,
} from 'react-icons/fi';
import { toast } from 'react-toastify';
import { useEstoques, useRelatorioEstoque } from '@/hooks/useEstoque';
import { useProdutoResolver } from '@/hooks/useProdutos';
import type { Estoque } from '@/types/estoque';
import EstoqueStatusBadge from './components/EstoqueStatusBadge';
import EstoqueOperacaoModal, { type OperacaoEstoque } from './components/EstoqueOperacaoModal';
import { formatarQuantidade } from './estoqueFormat';
import './EstoquePage.scss';

type StatusFiltro = 'todos' | 'baixo' | 'zerado' | 'reservado';
type SortKey = 'produto' | 'quantidade' | 'reservada' | 'disponivel';
type SortDir = 'asc' | 'desc';

const PAGE_SIZE = 10;

const EstoquePage = () => {
  const navigate = useNavigate();

  const [searchTerm, setSearchTerm] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<StatusFiltro>('todos');
  const [sortKey, setSortKey] = useState<SortKey>('produto');
  const [sortDir, setSortDir] = useState<SortDir>('asc');
  const [page, setPage] = useState(1);
  const [modal, setModal] = useState<{ operacao: OperacaoEstoque; estoque: Estoque } | null>(null);

  const { data: estoques = [], isLoading, isError } = useEstoques({ limit: 1000 });
  const { data: relatorio } = useRelatorioEstoque();
  const { mapa: produtoMap, nome: nomeProduto } = useProdutoResolver();

  const nomeDe = (estoque: Estoque): string => nomeProduto(estoque.produto_id);

  // Debounce da busca (300ms) — alinhado ao padrão de Produtos
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(searchTerm), 300);
    return () => clearTimeout(timer);
  }, [searchTerm]);

  useEffect(() => setPage(1), [debouncedSearch, statusFilter]);

  useEffect(() => {
    if (isError) toast.error('Erro ao carregar o estoque');
  }, [isError]);

  const filtrados = useMemo(() => {
    const termo = debouncedSearch.trim().toLowerCase();

    const passaStatus = (estoque: Estoque): boolean => {
      if (statusFilter === 'baixo') return estoque.alerta_estoque_baixo;
      if (statusFilter === 'zerado') return estoque.alerta_estoque_zerado;
      if (statusFilter === 'reservado') return estoque.quantidade_reservada > 0;
      return true;
    };

    const passaBusca = (estoque: Estoque): boolean => {
      if (!termo) return true;
      const alvo = `${nomeDe(estoque)} ${estoque.localizacao ?? ''}`.toLowerCase();
      return alvo.includes(termo);
    };

    const valorOrdenacao = (estoque: Estoque): string | number => {
      if (sortKey === 'produto') return nomeDe(estoque).toLowerCase();
      if (sortKey === 'quantidade') return estoque.quantidade;
      if (sortKey === 'reservada') return estoque.quantidade_reservada;
      return estoque.quantidade_disponivel;
    };

    return estoques
      .filter((estoque) => passaStatus(estoque) && passaBusca(estoque))
      .sort((a, b) => {
        const va = valorOrdenacao(a);
        const vb = valorOrdenacao(b);
        if (va < vb) return sortDir === 'asc' ? -1 : 1;
        if (va > vb) return sortDir === 'asc' ? 1 : -1;
        return 0;
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [estoques, statusFilter, debouncedSearch, sortKey, sortDir, produtoMap]);

  const totalPages = Math.max(1, Math.ceil(filtrados.length / PAGE_SIZE));
  const paginaAtual = Math.min(page, totalPages);
  const linhas = filtrados.slice((paginaAtual - 1) * PAGE_SIZE, paginaAtual * PAGE_SIZE);

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir((dir) => (dir === 'asc' ? 'desc' : 'asc'));
      return;
    }
    setSortKey(key);
    setSortDir('asc');
  };

  const indicadorSort = (key: SortKey) => {
    if (sortKey !== key) return null;
    return sortDir === 'asc' ? <FiArrowUp /> : <FiArrowDown />;
  };

  const kpis = [
    { chave: 'todos' as const, label: 'Total de itens', valor: relatorio?.total_produtos, icon: <FiPackage /> },
    { chave: 'reservado' as const, label: 'Em estoque (un.)', valor: relatorio?.total_em_estoque, icon: <FiLayers />, somenteLeitura: true },
    { chave: 'baixo' as const, label: 'Estoque baixo', valor: relatorio?.produtos_estoque_baixo, icon: <FiAlertTriangle />, tom: 'warning' },
    { chave: 'zerado' as const, label: 'Sem estoque', valor: relatorio?.produtos_sem_estoque, icon: <FiXCircle />, tom: 'danger' },
  ];

  return (
    <div className="estoque-page">
      <div className="page-header">
        <div className="header-content">
          <h1>
            <FiBox /> Estoque
          </h1>
          <p>Saldo físico, reservas e movimentações de cada produto</p>
        </div>
      </div>

      <div className="kpi-grid">
        {kpis.map((kpi) => (
          <button
            key={kpi.label}
            type="button"
            className={`kpi-card ${kpi.tom ? `kpi-card--${kpi.tom}` : ''} ${
              statusFilter === kpi.chave && !kpi.somenteLeitura ? 'kpi-card--active' : ''
            }`}
            onClick={() => !kpi.somenteLeitura && setStatusFilter(kpi.chave)}
            disabled={kpi.somenteLeitura}
          >
            <span className="kpi-icon">{kpi.icon}</span>
            <span className="kpi-meta">
              <span className="kpi-valor">{kpi.valor === undefined ? '—' : formatarQuantidade(kpi.valor)}</span>
              <span className="kpi-label">{kpi.label}</span>
            </span>
          </button>
        ))}
      </div>

      <div className="filters-section">
        <div className="search-box">
          <FiSearch className="search-icon" />
          <input
            type="text"
            placeholder="Buscar por produto ou localização..."
            value={searchTerm}
            onChange={(event) => setSearchTerm(event.target.value)}
          />
        </div>
        <div className="filter-buttons">
          {(['todos', 'baixo', 'zerado', 'reservado'] as StatusFiltro[]).map((status) => (
            <button
              key={status}
              type="button"
              className={`filter-btn ${statusFilter === status ? 'active' : ''}`}
              onClick={() => setStatusFilter(status)}
            >
              {status === 'todos' && 'Todos'}
              {status === 'baixo' && 'Baixo'}
              {status === 'zerado' && 'Zerado'}
              {status === 'reservado' && 'Com reserva'}
            </button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <div className="loading">
          <div className="spinner-border" role="status">
            <span className="visually-hidden">Carregando...</span>
          </div>
        </div>
      ) : linhas.length === 0 ? (
        <div className="empty-state">
          <p>Nenhum registro de estoque encontrado</p>
        </div>
      ) : (
        <>
          <div className="table-responsive">
            <table className="estoque-table">
              <thead>
                <tr>
                  <th className="sortable" onClick={() => toggleSort('produto')}>
                    Produto {indicadorSort('produto')}
                  </th>
                  <th>Localização</th>
                  <th className="sortable num" onClick={() => toggleSort('quantidade')}>
                    Físico {indicadorSort('quantidade')}
                  </th>
                  <th className="sortable num" onClick={() => toggleSort('reservada')}>
                    Reservado {indicadorSort('reservada')}
                  </th>
                  <th className="sortable num" onClick={() => toggleSort('disponivel')}>
                    Disponível {indicadorSort('disponivel')}
                  </th>
                  <th className="num">Mín.</th>
                  <th>Status</th>
                  <th>Ações</th>
                </tr>
              </thead>
              <tbody>
                {linhas.map((estoque) => (
                  <tr key={estoque.id}>
                    <td className="nome">{nomeDe(estoque)}</td>
                    <td>{estoque.localizacao || '—'}</td>
                    <td className="num">{formatarQuantidade(estoque.quantidade)}</td>
                    <td className="num">{formatarQuantidade(estoque.quantidade_reservada)}</td>
                    <td className="num strong">{formatarQuantidade(estoque.quantidade_disponivel)}</td>
                    <td className="num muted">{formatarQuantidade(estoque.estoque_minimo)}</td>
                    <td>
                      <EstoqueStatusBadge estoque={estoque} />
                    </td>
                    <td className="acoes">
                      <button
                        className="btn-icon btn-info"
                        onClick={() => navigate(`/estoque/${estoque.id}`)}
                        title="Ver detalhes"
                      >
                        <FiEye />
                      </button>
                      <button
                        className="btn-icon btn-success"
                        onClick={() => setModal({ operacao: 'entrada', estoque })}
                        title="Entrada"
                      >
                        <FiPlus />
                      </button>
                      <button
                        className="btn-icon btn-danger"
                        onClick={() => setModal({ operacao: 'saida', estoque })}
                        title="Saída"
                      >
                        <FiMinus />
                      </button>
                      <button
                        className="btn-icon btn-warning"
                        onClick={() => setModal({ operacao: 'ajuste', estoque })}
                        title="Ajuste"
                      >
                        <FiEdit2 />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="pagination">
            <button
              className="btn"
              onClick={() => setPage((prev) => Math.max(1, prev - 1))}
              disabled={paginaAtual === 1}
            >
              Anterior
            </button>
            <span className="page-info">
              Página {paginaAtual} de {totalPages} ({filtrados.length} itens)
            </span>
            <button
              className="btn"
              onClick={() => setPage((prev) => Math.min(totalPages, prev + 1))}
              disabled={paginaAtual === totalPages}
            >
              Próxima
            </button>
          </div>
        </>
      )}

      {modal && (
        <EstoqueOperacaoModal
          operacao={modal.operacao}
          estoque={modal.estoque}
          produtoNome={nomeDe(modal.estoque)}
          onClose={() => setModal(null)}
        />
      )}
    </div>
  );
};

export default EstoquePage;
