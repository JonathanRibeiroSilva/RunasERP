import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { FiArrowLeft, FiPlus, FiEdit2, FiTrash2, FiSave, FiX } from 'react-icons/fi';
import { toast } from 'react-toastify';
import { api } from '@/services/api/axios';
import './ClienteEnderecosPage.scss';

// Schema de validação
const enderecoSchema = z.object({
  logradouro: z.string().min(3, 'Logradouro deve ter no mínimo 3 caracteres'),
  numero: z.string().min(1, 'Número é obrigatório'),
  complemento: z.string().optional().or(z.literal('')),
  bairro: z.string().min(2, 'Bairro deve ter no mínimo 2 caracteres'),
  cidade: z.string().min(2, 'Cidade deve ter no mínimo 2 caracteres'),
  uf: z.string().length(2, 'UF deve ter 2 caracteres'),
  cep: z.string().regex(/^\d{8}$/, 'CEP deve ter 8 dígitos'),
  principal: z.boolean().default(false),
});

type EnderecoFormData = z.infer<typeof enderecoSchema>;

interface Endereco extends EnderecoFormData {
  id: string;
  cliente_id: string;
}

interface Cliente {
  id: string;
  nome: string;
  cpf: string;
}

const ClienteEnderecosPage = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [cliente, setCliente] = useState<Cliente | null>(null);
  const [enderecos, setEnderecos] = useState<Endereco[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [editando, setEditando] = useState<string | null>(null);
  const [mostrarForm, setMostrarForm] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    setValue,
  } = useForm<EnderecoFormData>({
    resolver: zodResolver(enderecoSchema),
  });

  useEffect(() => {
    if (id) {
      carregarDados();
    }
  }, [id]);

  const carregarDados = async () => {
    try {
      setLoading(true);
      const [clienteRes, enderecosRes] = await Promise.all([
        api.get(`/clientes/${id}`),
        api.get(`/clientes/${id}/enderecos`),
      ]);
      setCliente(clienteRes.data);
      setEnderecos(enderecosRes.data);
    } catch (error) {
      toast.error('Erro ao carregar dados');
      console.error(error);
      navigate('/clientes');
    } finally {
      setLoading(false);
    }
  };

  const buscarCEP = async (cep: string) => {
    if (cep.length !== 8) return;

    try {
      const response = await fetch(`https://viacep.com.br/ws/${cep}/json/`);
      const data = await response.json();

      if (data.erro) {
        toast.error('CEP não encontrado');
        return;
      }

      setValue('logradouro', data.logradouro);
      setValue('bairro', data.bairro);
      setValue('cidade', data.localidade);
      setValue('uf', data.uf);
      toast.success('CEP encontrado!');
    } catch (error) {
      toast.error('Erro ao buscar CEP');
      console.error(error);
    }
  };

  const onSubmit = async (data: EnderecoFormData) => {
    try {
      setSubmitting(true);

      if (editando) {
        // Editar
        await api.put(`/clientes/${id}/enderecos/${editando}`, data);
        toast.success('Endereço atualizado com sucesso');
      } else {
        // Criar
        await api.post(`/clientes/${id}/enderecos`, data);
        toast.success('Endereço criado com sucesso');
      }

      setMostrarForm(false);
      setEditando(null);
      reset();
      carregarDados();
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Erro ao salvar endereço';
      toast.error(message);
      console.error(error);
    } finally {
      setSubmitting(false);
    }
  };

  const handleEditar = (endereco: Endereco) => {
    setEditando(endereco.id);
    setMostrarForm(true);
    reset(endereco);
  };

  const handleDeletar = async (enderecoId: string) => {
    if (window.confirm('Tem certeza que deseja excluir este endereço?')) {
      try {
        await api.delete(`/clientes/${id}/enderecos/${enderecoId}`);
        toast.success('Endereço excluído com sucesso');
        carregarDados();
      } catch (error) {
        toast.error('Erro ao excluir endereço');
        console.error(error);
      }
    }
  };

  const handleNovoEndereco = () => {
    setEditando(null);
    setMostrarForm(true);
    reset({
      logradouro: '',
      numero: '',
      complemento: '',
      bairro: '',
      cidade: '',
      uf: '',
      cep: '',
      principal: false,
    });
  };

  const handleCancelar = () => {
    setMostrarForm(false);
    setEditando(null);
    reset();
  };

  const formatarCEP = (value: string) => {
    return value.replace(/\D/g, '').slice(0, 8);
  };

  if (loading) {
    return (
      <div className="cliente-enderecos-page">
        <div className="loading">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Carregando...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="cliente-enderecos-page">
      <div className="page-header">
        <button className="btn-back" onClick={() => navigate('/clientes')}>
          <FiArrowLeft /> Voltar
        </button>
        <div className="header-content">
          <h1>Endereços de {cliente?.nome}</h1>
          <p className="subtitle">CPF: {cliente?.cpf}</p>
        </div>
        {!mostrarForm && (
          <button className="btn btn-primary" onClick={handleNovoEndereco}>
            <FiPlus /> Novo Endereço
          </button>
        )}
      </div>

      {mostrarForm && (
        <div className="form-container">
          <div className="form-header">
            <h2>{editando ? 'Editar Endereço' : 'Novo Endereço'}</h2>
            <button className="btn-close" onClick={handleCancelar}>
              <FiX />
            </button>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="endereco-form">
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="cep">CEP *</label>
                <input
                  id="cep"
                  type="text"
                  placeholder="00000000"
                  {...register('cep', {
                    onChange: (e: React.ChangeEvent<HTMLInputElement>) => {
                      const cep = formatarCEP(e.target.value);
                      e.target.value = cep;
                      if (cep.length === 8) {
                        buscarCEP(cep);
                      }
                    },
                  })}
                  className={errors.cep ? 'is-invalid' : ''}
                />
                {errors.cep && <span className="error-message">{errors.cep.message}</span>}
              </div>

              <div className="form-group">
                <label htmlFor="uf">UF *</label>
                <input
                  id="uf"
                  type="text"
                  placeholder="UF"
                  maxLength={2}
                  {...register('uf')}
                  className={errors.uf ? 'is-invalid' : ''}
                />
                {errors.uf && <span className="error-message">{errors.uf.message}</span>}
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="logradouro">Logradouro *</label>
              <input
                id="logradouro"
                type="text"
                placeholder="Rua, Avenida, etc."
                {...register('logradouro')}
                className={errors.logradouro ? 'is-invalid' : ''}
              />
              {errors.logradouro && (
                <span className="error-message">{errors.logradouro.message}</span>
              )}
            </div>

            <div className="form-row">
              <div className="form-group" style={{ flex: 1 }}>
                <label htmlFor="numero">Número *</label>
                <input
                  id="numero"
                  type="text"
                  placeholder="123"
                  {...register('numero')}
                  className={errors.numero ? 'is-invalid' : ''}
                />
                {errors.numero && <span className="error-message">{errors.numero.message}</span>}
              </div>

              <div className="form-group" style={{ flex: 2 }}>
                <label htmlFor="complemento">Complemento</label>
                <input
                  id="complemento"
                  type="text"
                  placeholder="Apto, Bloco, etc."
                  {...register('complemento')}
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="bairro">Bairro *</label>
                <input
                  id="bairro"
                  type="text"
                  placeholder="Bairro"
                  {...register('bairro')}
                  className={errors.bairro ? 'is-invalid' : ''}
                />
                {errors.bairro && <span className="error-message">{errors.bairro.message}</span>}
              </div>

              <div className="form-group">
                <label htmlFor="cidade">Cidade *</label>
                <input
                  id="cidade"
                  type="text"
                  placeholder="Cidade"
                  {...register('cidade')}
                  className={errors.cidade ? 'is-invalid' : ''}
                />
                {errors.cidade && <span className="error-message">{errors.cidade.message}</span>}
              </div>
            </div>

            <div className="form-group">
              <label className="checkbox-label">
                <input type="checkbox" {...register('principal')} />
                <span>Definir como endereço principal</span>
              </label>
            </div>

            <div className="form-actions">
              <button type="button" className="btn btn-outline-secondary" onClick={handleCancelar}>
                Cancelar
              </button>
              <button type="submit" className="btn btn-primary" disabled={submitting}>
                <FiSave /> {submitting ? 'Salvando...' : 'Salvar'}
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="enderecos-list">
        {enderecos.length === 0 ? (
          <div className="empty-state">
            <p>Nenhum endereço cadastrado</p>
            <button className="btn btn-primary" onClick={handleNovoEndereco}>
              <FiPlus /> Adicionar Primeiro Endereço
            </button>
          </div>
        ) : (
          <div className="enderecos-grid">
            {enderecos.map((endereco: Endereco) => (
              <div key={endereco.id} className={`endereco-card ${endereco.principal ? 'principal' : ''}`}>
                {endereco.principal && <span className="badge-principal">Principal</span>}
                <div className="endereco-content">
                  <p className="endereco-linha">
                    {endereco.logradouro}, {endereco.numero}
                    {endereco.complemento && ` - ${endereco.complemento}`}
                  </p>
                  <p className="endereco-linha">
                    {endereco.bairro} - {endereco.cidade}/{endereco.uf}
                  </p>
                  <p className="endereco-cep">CEP: {endereco.cep.replace(/(\d{5})(\d{3})/, '$1-$2')}</p>
                </div>
                <div className="endereco-actions">
                  <button
                    className="btn-icon btn-warning"
                    onClick={() => handleEditar(endereco)}
                    title="Editar"
                  >
                    <FiEdit2 />
                  </button>
                  <button
                    className="btn-icon btn-danger"
                    onClick={() => handleDeletar(endereco.id)}
                    title="Excluir"
                  >
                    <FiTrash2 />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ClienteEnderecosPage;
