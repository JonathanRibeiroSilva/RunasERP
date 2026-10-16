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
  FiMaximize,
  FiCamera,
  FiFileText,
  FiAperture,
} from 'react-icons/fi';
import { toast } from 'react-toastify';
import { useEstoques, useRelatorioEstoque } from '@/hooks/useEstoque';
import { useProdutoResolver } from '@/hooks/useProdutos';
import { produtosApi } from '@/services/api/produtosApi';
import type { Estoque } from '@/types/estoque';
import EstoqueStatusBadge from './components/EstoqueStatusBadge';
import ScannerEanModal from './components/ScannerEanModal';
import ConferenciaVisualModal from './components/ConferenciaVisualModal';
import ImportarNfeModal from './components/ImportarNfeModal';
import { cameraSuportada } from './scannerEan';
import EstoqueOperacaoModal, { type OperacaoEstoque } from './components/EstoqueOperacaoModal';
import { formatarQuantidade } from './estoqueFormat';
import './EstoquePage.scss';

type StatusFiltro = 'todos' | 'baixo' | 'zerado' | 'reservado';
type SortKey = 'produto' | 'quantidade' | 'reservada' | 'disponivel';
type SortDir = 'asc' | 'desc';

/** Projeção Produto LEFT JOIN Estoque: produto sem linha de estoque aparece como "Nunca recebido". */
type LinhaEstoque = { chave: string; produtoId: string; estoque: Estoque | null };

const PAGE_SIZE = 10;

const EstoquePage = () => {
  const navigate = useNavigate();

  const [searchTerm, setSearchTerm] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<StatusFiltro>('todos');
  const [sortKey, setSortKey] = useState<SortKey>('produto');
  const [sortDir, setSortDir] = useState<SortDir>('asc');
  const [page, setPage] = useState(1);
  const [modal, setModal] = useState<{
    operacao: OperacaoEstoque;
    estoque: Estoque | null;
    produtoId?: string;
    /** Nome vindo da leitura do código: o lookup é limitado a 100 produtos e pode não conhecê-lo. */
    produtoNomeLido?: string;
  } | null>(null);
  const [codigoLido, setCodigoLido] = useState('');
  const [lendo, setLendo] = useState(false);
  const [camera, setCamera] = useState(false);
  const [conferencia, setConferencia] = useState(false);
  const [importandoNfe, setImportandoNfe] = useState(false);
  const [temCamera] = useState(cameraSuportada);
  // A conferência visual não usa BarcodeDetector, só câmera em contexto seguro.
  const [podeConferir] = useState(() => window.isSecureContext && !!navigator.mediaDevices?.getUserMedia);

  const { data: estoques = [], isLoading, isError } = useEstoques({ limit: 1000 });
  const { data: relatorio } = useRelatorioEstoque();
  const { mapa: produtoMap, nome: nomeProduto } = useProdutoResolver();

  // Composição no cliente: linhas reais de estoque + linha sintética para cada
  // produto cadastrado sem estoque. Linhas de estoque continuam sendo criadas
  // exclusivamente pelo serviço de Estoque — aqui é só visualização.
  const linhasProjetadas = useMemo<LinhaEstoque[]>(() => {
    const rows: LinhaEstoque[] = estoques.map((estoque) => ({
      chave: estoque.id,
      produtoId: estoque.produto_id,
      estoque,
    }));
    const produtosComEstoque = new Set(estoques.map((estoque) => estoque.produto_id));
    for (const produto of produtoMap?.values() ?? []) {
      if (!produtosComEstoque.has(produto.id)) {
        rows.push({ chave: `sem-estoque-${produto.id}`, produtoId: produto.id, estoque: null });
      }
    }
    return rows;
  }, [estoques, produtoMap]);

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

    const passaStatus = (linha: LinhaEstoque): boolean => {
      if (statusFilter === 'baixo') return linha.estoque?.alerta_estoque_baixo ?? false;
      if (statusFilter === 'zerado') return linha.estoque ? linha.estoque.alerta_estoque_zerado : true;
      if (statusFilter === 'reservado') return (linha.estoque?.quantidade_reservada ?? 0) > 0;
      return true;
    };

    const passaBusca = (linha: LinhaEstoque): boolean => {
      if (!termo) return true;
      return nomeProduto(linha.produtoId).toLowerCase().includes(termo);
    };

    const valorOrdenacao = (linha: LinhaEstoque): string | number => {
      if (sortKey === 'produto') return nomeProduto(linha.produtoId).toLowerCase();
      if (sortKey === 'quantidade') return linha.estoque?.quantidade ?? 0;
      if (sortKey === 'reservada') return linha.estoque?.quantidade_reservada ?? 0;
      return linha.estoque?.quantidade_disponivel ?? 0;
    };

    return linhasProjetadas
      .filter((linha) => passaStatus(linha) && passaBusca(linha))
      .sort((a, b) => {
        const va = valorOrdenacao(a);
        const vb = valorOrdenacao(b);
        if (va < vb) return sortDir === 'asc' ? -1 : 1;
        if (va > vb) return sortDir === 'asc' ? 1 : -1;
        return 0;
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [linhasProjetadas, statusFilter, debouncedSearch, sortKey, sortDir, produtoMap]);

  const totalPages = Math.max(1, Math.ceil(filtrados.length / PAGE_SIZE));
  const paginaAtual = Math.min(page, totalPages);
  const linhas = filtrados.slice((paginaAtual - 1) * PAGE_SIZE, paginaAtual * PAGE_SIZE);

  // Leitor USB/Bluetooth é um teclado: digita o código e dá Enter. O mesmo campo
  // atende digitação manual. Casa EAN ou SKU exato; a busca do backend também
  // casa nome parcial, então o filtro abaixo descarta o que não é o código.
  const lerCodigo = async (lido: string = codigoLido) => {
    const codigo = lido.trim();
    if (!codigo || lendo) return;
    setLendo(true);
    try {
      const { items } = await produtosApi.listar({ busca: codigo, limit: 10 });
      const achados = items.filter((p) => p.codigo_barras === codigo || p.sku === codigo);
      if (achados.length === 0) {
        toast.warn(`Nenhum produto com o código ${codigo}. Cadastre o código no produto.`);
        return;
      }
      if (achados.length > 1) {
        toast.warn(`Mais de um produto com o código ${codigo}. Escolha na lista.`);
        return;
      }
      const produto = achados[0];
      const estoque = estoques.find((e) => e.produto_id === produto.id) ?? null;
      setModal({
        operacao: 'entrada',
        estoque,
        produtoId: estoque ? undefined : produto.id,
        produtoNomeLido: produto.nome,
      });
      setCodigoLido('');
    } catch {
      toast.error('Erro ao buscar o código');
    } finally {
      setLendo(false);
    }
  };

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
    { chave: 'todos' as const, label: 'Total de itens', valor: linhasProjetadas.length, icon: <FiPackage /> },
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
        <button type="button" className="btn btn-primary" onClick={() => setImportandoNfe(true)}>
          <FiFileText /> Importar NF-e (XML)
        </button>
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
          <FiMaximize className="search-icon" />
          <input
            type="text"
            inputMode="numeric"
            placeholder="Ler código de barras (Enter)..."
            aria-label="Código de barras"
            value={codigoLido}
            disabled={lendo}
            onChange={(event) => setCodigoLido(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter') {
                event.preventDefault();
                void lerCodigo();
              }
            }}
          />
        </div>
        <div className="search-box">
          <FiSearch className="search-icon" />
          <input
            type="text"
            placeholder="Buscar por produto..."
            value={searchTerm}
            onChange={(event) => setSearchTerm(event.target.value)}
          />
          {podeConferir && (
            <button
              type="button"
              className="btn-icon"
              title="Conferência visual (detecção de objetos)"
              onClick={() => setConferencia(true)}
            >
              <FiAperture />
            </button>
          )}
          {temCamera && (
            <button type="button" className="btn-icon" title="Ler pela câmera" onClick={() => setCamera(true)}>
              <FiCamera />
            </button>
          )}
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
            <table className="estoque-table estoque-table--cards">
              <thead>
                <tr>
                  <th className="sortable" onClick={() => toggleSort('produto')}>
                    Produto {indicadorSort('produto')}
                  </th>
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
                {linhas.map((linha) => (
                  <tr key={linha.chave}>
                    <td data-label="Produto" className="nome">{nomeProduto(linha.produtoId)}</td>
                    <td data-label="Físico" className="num">{formatarQuantidade(linha.estoque?.quantidade ?? 0)}</td>
                    <td data-label="Reservado" className="num">{formatarQuantidade(linha.estoque?.quantidade_reservada ?? 0)}</td>
                    <td data-label="Disponível" className="num strong">{formatarQuantidade(linha.estoque?.quantidade_disponivel ?? 0)}</td>
                    <td data-label="Mín." className="num muted">
                      {linha.estoque ? formatarQuantidade(linha.estoque.estoque_minimo) : '—'}
                    </td>
                    <td data-label="Status">
                      {linha.estoque ? (
                        <EstoqueStatusBadge estoque={linha.estoque} />
                      ) : (
                        <span className="estoque-badge estoque-badge--neutral">Nunca recebido</span>
                      )}
                    </td>
                    <td data-label="Ações" className="acoes">
                      {linha.estoque ? (
                        <>
                          <button
                            className="btn-icon btn-info"
                            onClick={() => navigate(`/estoque/${linha.estoque!.id}`)}
                            title="Ver detalhes"
                          >
                            <FiEye />
                          </button>
                          <button
                            className="btn-icon btn-success"
                            onClick={() => setModal({ operacao: 'entrada', estoque: linha.estoque })}
                            title="Entrada"
                          >
                            <FiPlus />
                          </button>
                          <button
                            className="btn-icon btn-danger"
                            onClick={() => setModal({ operacao: 'saida', estoque: linha.estoque })}
                            title="Saída"
                          >
                            <FiMinus />
                          </button>
                          <button
                            className="btn-icon btn-warning"
                            onClick={() => setModal({ operacao: 'ajuste', estoque: linha.estoque })}
                            title="Ajuste"
                          >
                            <FiEdit2 />
                          </button>
                        </>
                      ) : (
                        <button
                          className="btn-icon btn-success"
                          onClick={() =>
                            setModal({ operacao: 'entrada', estoque: null, produtoId: linha.produtoId })
                          }
                          title="Primeira entrada"
                        >
                          <FiPlus />
                        </button>
                      )}
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

      {conferencia && <ConferenciaVisualModal onClose={() => setConferencia(false)} />}

      {camera && (
        <ScannerEanModal
          onClose={() => setCamera(false)}
          onCodigo={(codigo) => {
            setCamera(false);
            void lerCodigo(codigo);
          }}
        />
      )}

      {importandoNfe && <ImportarNfeModal onClose={() => setImportandoNfe(false)} />}

      {modal && (
        <EstoqueOperacaoModal
          operacao={modal.operacao}
          estoque={modal.estoque}
          produtoNome={
            modal.produtoNomeLido ?? nomeProduto(modal.estoque ? modal.estoque.produto_id : modal.produtoId ?? '')
          }
          produtoIdInicial={modal.produtoId}
          onClose={() => setModal(null)}
        />
      )}
    </div>
  );
};

export default EstoquePage;
