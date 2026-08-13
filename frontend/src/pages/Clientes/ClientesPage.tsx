import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiPlus, FiSearch, FiEdit2, FiTrash2, FiEye, FiMapPin, FiDollarSign, FiUsers, FiUserCheck, FiUserX, FiAlertCircle, FiRotateCcw } from 'react-icons/fi';
import { toast } from 'react-toastify';
import { getErrorMessage } from '@/services/api/axios';
import { useClientes, useDesativarCliente, useReativarCliente } from '@/hooks/useClientes';
import ClienteFormPage from './ClienteFormPage';
import './ClientesPage.scss';

const ClientesPage = () => {
  const navigate = useNavigate();

  const [searchTerm, setSearchTerm] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [filtroAtivo, setFiltroAtivo] = useState<boolean | null>(null);
  const [filtroBloqueado, setFiltroBloqueado] = useState<boolean | null>(null);
  const [page, setPage] = useState(1);

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedClienteId, setSelectedClienteId] = useState<string | null>(null);

  const itemsPerPage = 10;

  // Debounce da busca (300ms) — evita refetch a cada tecla
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchTerm);
      setPage(1);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchTerm]);

  const { data, isLoading, isError } = useClientes({
    skip: (page - 1) * itemsPerPage,
    limit: itemsPerPage,
    nome: debouncedSearch || undefined,
    ativo: filtroAtivo ?? undefined,
    bloqueado: filtroBloqueado ?? undefined,
  });

  // Totals for stat cards
  const { data: dataTotal }     = useClientes({ skip: 0, limit: 1 });
  const { data: dataAtivos }    = useClientes({ skip: 0, limit: 1, ativo: true });
  const { data: dataInativos }  = useClientes({ skip: 0, limit: 1, ativo: false });
  const { data: dataBloqueados }= useClientes({ skip: 0, limit: 1, bloqueado: true });

  const desativarCliente = useDesativarCliente();
  const reativarCliente = useReativarCliente();

  const clientes = data?.clientes ?? [];
  const total = data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / itemsPerPage));

  useEffect(() => {
    if (isError) {
      toast.error('Erro ao carregar clientes');
    }
  }, [isError]);

  const handleNovoCliente = () => {
    setSelectedClienteId(null);
    setIsModalOpen(true);
  };

  const handleEditar = (id: string) => {
    setSelectedClienteId(id);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedClienteId(null);
  };

  const handleVisualizar = (id: string) => {
    navigate(`/clientes/${id}`);
  };

  const handleDeletar = (id: string) => {
    if (!window.confirm('Tem certeza que deseja desativar este cliente?')) {
      return;
    }
    desativarCliente.mutate(id, {
      onSuccess: () => toast.success('Cliente desativado com sucesso'),
      onError: (error) => toast.error(getErrorMessage(error)),
    });
  };

  const handleReativar = (id: string) => {
    reativarCliente.mutate(id, {
      onSuccess: () => toast.success('Cliente reativado com sucesso'),
      onError: (error) => toast.error(getErrorMessage(error)),
    });
  };

  const formatarCPF = (cpf: string | null | undefined) => {
    if (!cpf) return '-';
    return cpf.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
  };

  const formatarTelefone = (telefone: string | null | undefined) => {
    if (!telefone) return '-';
    // Backend guarda em E.164 (+5544...): remover código do país antes da máscara
    let n = telefone.replace(/\D/g, '');
    if (n.length > 11 && n.startsWith('55')) n = n.slice(2);
    if (n.length === 11) return n.replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3');
    if (n.length === 10) return n.replace(/(\d{2})(\d{4})(\d{4})/, '($1) $2-$3');
    return telefone;
  };

  const formatarMoeda = (valor: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
    }).format(valor);
  };

  const getAvatarColors = (nome: string) => {
    const colors = [
      { bg: 'rgba(14,165,233,0.2)',  color: '#0EA5E9' },
      { bg: 'rgba(99,102,241,0.2)', color: '#6366F1' },
      { bg: 'rgba(16,185,129,0.2)', color: '#10B981' },
      { bg: 'rgba(245,158,11,0.2)', color: '#F59E0B' },
      { bg: 'rgba(239,68,68,0.2)',  color: '#EF4444' },
      { bg: 'rgba(168,85,247,0.2)', color: '#A855F7' },
      { bg: 'rgba(236,72,153,0.2)', color: '#EC4899' },
    ];
    const idx = nome.charCodeAt(0) % colors.length;
    return colors[idx];
  };

  const getInitials = (nome: string) => {
    const parts = nome.trim().split(' ');
    return parts.length >= 2
      ? `${parts[0][0]}${parts[1][0]}`
      : parts[0].substring(0, 2);
  };

  return (
    <div className="clientes-page">
      <div className="page-header">
        <div className="header-content">
          <h1><FiUsers className="title-icon" /> Clientes</h1>
          <p>Gerencie sua base de clientes</p>
        </div>
        <button className="btn-new" onClick={handleNovoCliente}>
          <FiPlus /> Novo Cliente
        </button>
      </div>

      {/* Stat Cards */}
      <div className="stats-row">
        <div
          className={`stat-card total${filtroAtivo === null && filtroBloqueado === null ? ' active' : ''}`}
          onClick={() => { setFiltroAtivo(null); setFiltroBloqueado(null); setPage(1); }}
          title="Ver todos"
        >
          <div className="stat-icon"><FiUsers /></div>
          <div className="stat-info">
            <span className="stat-label">Total</span>
            <span className="stat-value">{dataTotal?.total ?? '—'}</span>
          </div>
        </div>

        <div
          className={`stat-card ativos${filtroAtivo === true && filtroBloqueado === null ? ' active' : ''}`}
          onClick={() => { setFiltroAtivo(filtroAtivo === true ? null : true); setFiltroBloqueado(null); setPage(1); }}
          title="Filtrar ativos"
        >
          <div className="stat-icon"><FiUserCheck /></div>
          <div className="stat-info">
            <span className="stat-label">Ativos</span>
            <span className="stat-value">{dataAtivos?.total ?? '—'}</span>
          </div>
        </div>

        <div
          className={`stat-card inativos${filtroAtivo === false ? ' active' : ''}`}
          onClick={() => { setFiltroAtivo(filtroAtivo === false ? null : false); setFiltroBloqueado(null); setPage(1); }}
          title="Filtrar inativos"
        >
          <div className="stat-icon"><FiUserX /></div>
          <div className="stat-info">
            <span className="stat-label">Inativos</span>
            <span className="stat-value">{dataInativos?.total ?? '—'}</span>
          </div>
        </div>

        <div
          className={`stat-card bloqueados${filtroBloqueado === true ? ' active' : ''}`}
          onClick={() => { setFiltroBloqueado(filtroBloqueado === true ? null : true); setFiltroAtivo(null); setPage(1); }}
          title="Filtrar bloqueados"
        >
          <div className="stat-icon"><FiAlertCircle /></div>
          <div className="stat-info">
            <span className="stat-label">Bloqueados</span>
            <span className="stat-value">{dataBloqueados?.total ?? '—'}</span>
          </div>
        </div>
      </div>

      {/* Search */}
      <div className="filters-section">
        <div className="search-box">
          <FiSearch className="search-icon" />
          <input
            type="text"
            placeholder="Buscar por nome, CPF/CNPJ, telefone ou email..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      {isLoading ? (
        <div className="loading">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Carregando...</span>
          </div>
        </div>
      ) : clientes.length === 0 ? (
        <div className="empty-state">
          <p>Nenhum cliente encontrado</p>
        </div>
      ) : (
        <>
          <div className="table-responsive">
            <table className="clientes-table">
              <thead>
                <tr>
                  <th>Nome</th>
                  <th>CPF</th>
                  <th>Telefone</th>
                  <th>Email</th>
                  <th>Limite de Crédito</th>
                  <th>Crédito Disponível</th>
                  <th>Status</th>
                  <th>Ações</th>
                </tr>
              </thead>
              <tbody>
                {clientes.map((cliente) => (
                  <tr key={cliente.id} className={!cliente.ativo ? 'inactive' : ''}>
                    <td data-label="Nome" className="nome">
                      <div className="nome-cell">
                        {(() => {
                          const c = getAvatarColors(cliente.nome);
                          return (
                            <span className="client-avatar" style={{ background: c.bg, color: c.color }}>
                              {getInitials(cliente.nome)}
                            </span>
                          );
                        })()}
                        {cliente.nome}
                      </div>
                    </td>
                    <td data-label="CPF">{formatarCPF(cliente.cpf)}</td>
                    <td data-label="Telefone">{formatarTelefone(cliente.telefone)}</td>
                    <td data-label="Email">{cliente.email || '-'}</td>
                    <td data-label="Lim. Crédito" className="moeda">{formatarMoeda(cliente.limite_credito)}</td>
                    <td data-label="Disp." className="moeda">
                      <span className={cliente.credito_disponivel < 0 ? 'negativo' : ''}>
                        {formatarMoeda(cliente.credito_disponivel)}
                      </span>
                    </td>
                    <td data-label="Status">
                      <div className="status-badges">
                        {cliente.bloqueado && <span className="badge badge-danger">Bloqueado</span>}
                        {!cliente.ativo && <span className="badge badge-secondary">Inativo</span>}
                        {cliente.ativo && !cliente.bloqueado && (
                          <span className="badge badge-success">Ativo</span>
                        )}
                      </div>
                    </td>
                    <td data-label="Ações" className="acoes">
                      <div className="actions-group">
                        <button
                          className="btn-icon btn-info"
                          onClick={() => handleVisualizar(cliente.id)}
                          title="Visualizar"
                        >
                          <FiEye />
                        </button>
                        <button
                          className="btn-icon btn-warning"
                          onClick={() => handleEditar(cliente.id)}
                          title="Editar"
                        >
                          <FiEdit2 />
                        </button>
                        <button
                          className="btn-icon btn-secondary"
                          onClick={() => navigate(`/clientes/${cliente.id}/enderecos`)}
                          title="Endereços"
                        >
                          <FiMapPin />
                        </button>
                        <button
                          className="btn-icon btn-success"
                          onClick={() => navigate(`/clientes/${cliente.id}/credito`)}
                          title="Crédito"
                        >
                          <FiDollarSign />
                        </button>
                        {cliente.ativo ? (
                          <button
                            className="btn-icon btn-danger"
                            onClick={() => handleDeletar(cliente.id)}
                            title="Desativar"
                          >
                            <FiTrash2 />
                          </button>
                        ) : (
                          <button
                            className="btn-icon btn-success"
                            onClick={() => handleReativar(cliente.id)}
                            title="Reativar"
                          >
                            <FiRotateCcw />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="pagination">
            <button
              disabled={page === 1}
              onClick={() => setPage(page - 1)}
              className="btn btn-sm btn-outline-primary"
            >
              Anterior
            </button>
            <span className="page-info">
              Página {page} de {totalPages}
            </span>
            <button
              disabled={page === totalPages}
              onClick={() => setPage(page + 1)}
              className="btn btn-sm btn-outline-primary"
            >
              Próxima
            </button>
          </div>
        </>
      )}

      {/* MODAL CLIENTE FORM */}
      {isModalOpen && (
        <ClienteFormPage
          isModal={true}
          clienteId={selectedClienteId}
          onClose={handleCloseModal}
        />
      )}
    </div>
  );
};

export default ClientesPage;
