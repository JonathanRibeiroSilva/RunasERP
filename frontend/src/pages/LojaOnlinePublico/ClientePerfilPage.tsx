import { useState, useEffect } from 'react';
import { FiUser, FiMail, FiPhone, FiFileText } from 'react-icons/fi';
import { apiPublica } from '@/services/api/apiPublica';
import { toast } from 'react-toastify';
import ClienteLayout from './components/ClienteLayout';
import './ClientePerfilPage.scss';

interface ClienteInfo {
  id: string;
  nome: string;
  email: string;
  telefone?: string;
  cpf?: string;
  criado_em: string;
}

const ClientePerfilPage = () => {
  const [cliente, setCliente] = useState<ClienteInfo | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    carregarPerfil();
  }, []);

  const carregarPerfil = async () => {
    try {
      setLoading(true);
      const response = await apiPublica.get('/clientes/me');
      setCliente(response.data);
    } catch (error) {
      console.error('Erro ao carregar perfil:', error);
      toast.error('Erro ao carregar perfil');
    } finally {
      setLoading(false);
    }
  };

  const formatarData = (dataStr: string) => {
    const data = new Date(dataStr);
    return new Intl.DateTimeFormat('pt-BR', {
      day: '2-digit',
      month: 'long',
      year: 'numeric',
    }).format(data);
  };

  const formatarCPF = (cpf: string) => {
    return cpf.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
  };

  const formatarTelefone = (telefone: string) => {
    if (telefone.length === 11) {
      return telefone.replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3');
    }
    return telefone.replace(/(\d{2})(\d{4})(\d{4})/, '($1) $2-$3');
  };

  if (loading) {
    return (
      <ClienteLayout title="Meu Perfil">
        <div className="loading-container">
          <div className="spinner" />
          <p>Carregando perfil...</p>
        </div>
      </ClienteLayout>
    );
  }

  if (!cliente) {
    return (
      <ClienteLayout title="Meu Perfil">
        <div className="error-container">
          <p>Erro ao carregar perfil</p>
        </div>
      </ClienteLayout>
    );
  }

  return (
    <ClienteLayout title="Meu Perfil">
      <div className="cliente-perfil-page">
        <div className="perfil-card">
          <div className="perfil-header">
            <div className="avatar">
              <FiUser />
            </div>
            <div className="header-info">
              <h2>{cliente.nome}</h2>
              <span className="membro-desde">
                Membro desde {formatarData(cliente.criado_em)}
              </span>
            </div>
          </div>

          <div className="perfil-body">
            <div className="info-section">
              <h3>Informações Pessoais</h3>
              <div className="info-grid">
                <div className="info-item">
                  <div className="info-label">
                    <FiUser />
                    <span>Nome Completo</span>
                  </div>
                  <div className="info-value">{cliente.nome}</div>
                </div>

                <div className="info-item">
                  <div className="info-label">
                    <FiMail />
                    <span>E-mail</span>
                  </div>
                  <div className="info-value">{cliente.email}</div>
                </div>

                {cliente.telefone && (
                  <div className="info-item">
                    <div className="info-label">
                      <FiPhone />
                      <span>Telefone</span>
                    </div>
                    <div className="info-value">
                      {formatarTelefone(cliente.telefone)}
                    </div>
                  </div>
                )}

                {cliente.cpf && (
                  <div className="info-item">
                    <div className="info-label">
                      <FiFileText />
                      <span>CPF</span>
                    </div>
                    <div className="info-value">{formatarCPF(cliente.cpf)}</div>
                  </div>
                )}
              </div>
            </div>

            {/* Placeholder para futuras funcionalidades */}
            <div className="info-section">
              <h3>Configurações</h3>
              <div className="configuracoes-info">
                <p>Em breve você poderá editar suas informações e gerenciar suas preferências.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </ClienteLayout>
  );
};

export default ClientePerfilPage;
