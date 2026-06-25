import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiPlus, FiSearch, FiEdit2, FiTrash2, FiEye, FiMapPin } from 'react-icons/fi';
import { toast } from 'react-toastify';
import { api } from '@/services/api/axios';
import './ClientesPage.scss';

interface Cliente {
  id: string;
  nome: string;
  cpf: string;
  email: string;
  telefone: string;
  limite_credito: number;
  credito_disponivel: number;
  bloqueado: boolean;
  ativo: boolean;
}

const ClientesPage = () => {
  const navigate = useNavigate();
  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filtroAtivo, setFiltroAtivo] = useState<boolean | null>(null);
  const [filtroBloqueado, setFiltroBloqueado] = useState<boolean | null>(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  const itemsPerPage = 10;

  useEffect(() => {
    let isMounted = true;
    
    const carregarClientesWrapper = async () => {
      try {
        setLoading(true);
        const params = new URLSearchParams({
          skip: ((page - 1) * itemsPerPage).toString(),
          limit: itemsPerPage.toString(),
        });

        if (searchTerm) {
          params.append('nome', searchTerm);
        }

        if (filtroAtivo !== null) {
          params.append('ativo', filtroAtivo.toString());
        }

        if (filtroBloqueado !== null) {
          params.append('bloqueado', filtroBloqueado.toString());
        }

        const response = await api.get(`/clientes?${params}`);
        
        // Só atualizar estado se o componente ainda estiver montado
        if (isMounted) {
          const { clientes: clientesData, total } = response.data;
          setClientes(clientesData || []);
          setTotalPages(Math.ceil((total || 0) / itemsPerPage));
        }
      } catch (error: any) {
        if (!isMounted) return;
        
        console.error('[ClientesPage] Erro ao carregar clientes:', error);
        
        if (error.response?.status >= 500) {
          toast.error('Erro no servidor. Tente novamente mais tarde.');
        } else if (error.response?.status === 404) {
          toast.error('Serviço de clientes indisponível');
        } else if (!error.response) {
          toast.error('Erro de conexão com o servidor');
        } else {
          toast.error('Erro ao carregar clientes');
        }
        
        setClientes([]);
        setTotalPages(1);
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };
    
    carregarClientesWrapper();
    
    return () => {
      isMounted = false;
    };
  }, [page, searchTerm, filtroAtivo, filtroBloqueado]);

  const carregarClientes = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        skip: ((page - 1) * itemsPerPage).toString(),
        limit: itemsPerPage.toString(),
      });

      if (searchTerm) {
        params.append('nome', searchTerm);
      }

      if (filtroAtivo !== null) {
        params.append('ativo', filtroAtivo.toString());
      }

      if (filtroBloqueado !== null) {
        params.append('bloqueado', filtroBloqueado.toString());
      }

      const response = await api.get(`/clientes?${params}`);
      const { clientes: clientesData, total } = response.data;

      setClientes(clientesData || []);
      setTotalPages(Math.ceil((total || 0) / itemsPerPage));
    } catch (error: any) {
      
      if (error.response?.status >= 500) {
        toast.error('Erro no servidor. Tente novamente mais tarde.');
      } else if (error.response?.status === 404) {
        toast.error('Serviço de clientes indisponível');
      } else if (!error.response) {
        toast.error('Erro de conexão com o servidor');
      } else {
        toast.error('Erro ao carregar clientes');
      }
      
      setClientes([]);
      setTotalPages(1);
    } finally {
      setLoading(false);
    }
  };

  const handleNovoCliente = () => {
    navigate('/clientes/novo');
  };

  const handleEditar = (id: string) => {
    navigate(`/clientes/${id}/editar`);
  };

  const handleVisualizar = (id: string) => {
    navigate(`/clientes/${id}`);
  };

  const handleDeletar = async (id: string) => {
    if (window.confirm('Tem certeza que deseja desativar este cliente?')) {
      try {
        await api.delete(`/clientes/${id}`);
        toast.success('Cliente desativado com sucesso');
        carregarClientes();
      } catch (error) {
        toast.error('Erro ao desativar cliente');
        console.error(error);
      }
    }
  };

  const formatarCPF = (cpf: string) => {
    return cpf.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
  };

  const formatarMoeda = (valor: number) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
    }).format(valor);
  };

  return (
    <div className="clientes-page">
      <div className="page-header">
        <div className="header-content">
          <h1>Clientes</h1>
          <p>Gestão de clientes e crédito</p>
        </div>
        <button className="btn btn-primary" onClick={handleNovoCliente}>
          <FiPlus /> Novo Cliente
        </button>
      </div>

      <div className="filters-section">
        <div className="search-box">
          <FiSearch className="search-icon" />
          <input
            type="text"
            placeholder="Buscar por nome ou CPF..."
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setPage(1);
            }}
          />
        </div>

        <div className="filter-buttons">
          <button
            className={`filter-btn ${filtroAtivo === true ? 'active' : ''}`}
            onClick={() => {
              setFiltroAtivo(filtroAtivo === true ? null : true);
              setPage(1);
            }}
          >
            Ativos
          </button>
          <button
            className={`filter-btn ${filtroAtivo === false ? 'active' : ''}`}
            onClick={() => {
              setFiltroAtivo(filtroAtivo === false ? null : false);
              setPage(1);
            }}
          >
            Inativos
          </button>
          <button
            className={`filter-btn ${filtroBloqueado === true ? 'active' : ''}`}
            onClick={() => {
              setFiltroBloqueado(filtroBloqueado === true ? null : true);
              setPage(1);
            }}
          >
            Bloqueados
          </button>
        </div>
      </div>

      {loading ? (
        <div className="loading">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Carregando...</span>
          </div>
        </div>
      ) : clientes && clientes.length === 0 ? (
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
                {clientes && clientes.map((cliente) => (
                  <tr key={cliente.id} className={!cliente.ativo ? 'inactive' : ''}>
                    <td className="nome">{cliente.nome}</td>
                    <td>{formatarCPF(cliente.cpf)}</td>
                    <td>{cliente.telefone}</td>
                    <td>{cliente.email || '-'}</td>
                    <td className="moeda">{formatarMoeda(cliente.limite_credito)}</td>
                    <td className="moeda">
                      <span className={cliente.credito_disponivel < 0 ? 'negativo' : ''}>
                        {formatarMoeda(cliente.credito_disponivel)}
                      </span>
                    </td>
                    <td>
                      <div className="status-badges">
                        {cliente.bloqueado && <span className="badge badge-danger">Bloqueado</span>}
                        {!cliente.ativo && <span className="badge badge-secondary">Inativo</span>}
                        {cliente.ativo && !cliente.bloqueado && (
                          <span className="badge badge-success">Ativo</span>
                        )}
                      </div>
                    </td>
                    <td className="acoes">
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
                        className="btn-icon btn-danger"
                        onClick={() => handleDeletar(cliente.id)}
                        title="Desativar"
                      >
                        <FiTrash2 />
                      </button>
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
    </div>
  );
};

export default ClientesPage;
