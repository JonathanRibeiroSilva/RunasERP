import React, { useState, useEffect } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { FiArrowLeft, FiSave, FiMapPin } from 'react-icons/fi';
import { toast } from 'react-toastify';
import { api } from '@/services/api/axios';
import './ClienteFormPage.scss';

// Schema de validação
const clienteSchema = z.object({
  nome: z.string().min(3, 'Nome deve ter no mínimo 3 caracteres'),
  cpf: z.string().regex(/^\d{11}$/, 'CPF deve ter 11 dígitos'),
  telefone: z.string().regex(/^\(\d{2}\)\s\d{4,5}-\d{4}$/, 'Telefone inválido'),
  email: z.string().email('Email inválido').optional().or(z.literal('')),
  data_nasc: z.string().optional().or(z.literal('')),
  limite_credito: z.number().min(0, 'Limite de crédito não pode ser negativo'),
  dia_vencimento: z.number().min(1).max(28, 'Dia deve estar entre 1 e 28').optional(),
  // Endereço (opcional)
  cep: z.string().regex(/^\d{8}$/, 'CEP deve ter 8 dígitos').optional().or(z.literal('')),
  logradouro: z.string().min(3, 'Logradouro deve ter no mínimo 3 caracteres').optional().or(z.literal('')),
  numero: z.string().optional().or(z.literal('')),
  complemento: z.string().optional().or(z.literal('')),
  bairro: z.string().min(2, 'Bairro deve ter no mínimo 2 caracteres').optional().or(z.literal('')),
  cidade: z.string().min(2, 'Cidade deve ter no mínimo 2 caracteres').optional().or(z.literal('')),
  uf: z.string().length(2, 'UF deve ter 2 caracteres').optional().or(z.literal('')),
});

type ClienteFormData = z.infer<typeof clienteSchema>;

interface Cliente extends ClienteFormData {
  id: string;
  ativo: boolean;
  bloqueado: boolean;
  credito_disponivel: number;
}

const ClienteFormPage = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [loading, setLoading] = useState(!!id);
  const [submitting, setSubmitting] = useState(false);
  const [cliente, setCliente] = useState<Cliente | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    setValue,
  } = useForm<ClienteFormData>({
    resolver: zodResolver(clienteSchema),
  });

  useEffect(() => {
    if (id) {
      carregarCliente();
    }
  }, [id]);

  const carregarCliente = async () => {
    try {
      setLoading(true);
      const [clienteRes, enderecosRes] = await Promise.all([
        api.get(`/clientes/${id}`),
        api.get(`/clientes/${id}/enderecos`),
      ]);
      
      setCliente(clienteRes.data);
      
      // Carregar endereço principal se existir
      const enderecos = enderecosRes.data;
      const enderecoPrincipal = enderecos.find((e: any) => e.principal);
      
      if (enderecoPrincipal) {
        reset({
          ...clienteRes.data,
          cep: enderecoPrincipal.cep,
          logradouro: enderecoPrincipal.logradouro,
          numero: enderecoPrincipal.numero,
          complemento: enderecoPrincipal.complemento || '',
          bairro: enderecoPrincipal.bairro,
          cidade: enderecoPrincipal.cidade,
          uf: enderecoPrincipal.uf,
        });
      } else {
        reset(clienteRes.data);
      }
    } catch (error) {
      toast.error('Erro ao carregar cliente');
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

  const onSubmit = async (data: ClienteFormData) => {
    try {
      setSubmitting(true);

      // Separar dados do cliente e endereço
      const { cep, logradouro, numero, complemento, bairro, cidade, uf, ...clienteData } = data;

      let clienteId = id;

      if (id) {
        // Editar cliente
        await api.put(`/clientes/${id}`, clienteData);
        toast.success('Cliente atualizado com sucesso');
      } else {
        // Criar cliente
        const response = await api.post('/clientes', clienteData);
        clienteId = response.data.id;
        toast.success('Cliente criado com sucesso');
      }

      // Se tem endereço preenchido, criar/atualizar
      if (cep && logradouro && numero && bairro && cidade && uf) {
        const enderecoData = {
          cep,
          logradouro,
          numero,
          complemento: complemento || '',
          bairro,
          cidade,
          uf,
          principal: true,
        };

        try {
          // Verificar se já existe endereço principal
          const enderecosResponse = await api.get(`/clientes/${clienteId}/enderecos`);
          const enderecos = enderecosResponse.data;
          const enderecoPrincipal = enderecos.find((e: any) => e.principal);

          if (enderecoPrincipal) {
            // Atualizar endereço principal existente
            await api.put(`/clientes/${clienteId}/enderecos/${enderecoPrincipal.id}`, enderecoData);
          } else {
            // Criar novo endereço principal
            await api.post(`/clientes/${clienteId}/enderecos`, enderecoData);
          }
        } catch (error) {
          console.error('Erro ao salvar endereço:', error);
          toast.warning('Cliente salvo, mas houve erro ao salvar o endereço');
        }
      }

      navigate('/clientes');
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Erro ao salvar cliente';
      toast.error(message);
      console.error(error);
    } finally {
      setSubmitting(false);
    }
  };

  const formatarTelefone = (value: string) => {
    const numbers = value.replace(/\D/g, '');
    if (numbers.length <= 2) return numbers;
    if (numbers.length <= 6) return `(${numbers.slice(0, 2)}) ${numbers.slice(2)}`;
    if (numbers.length <= 10)
      return `(${numbers.slice(0, 2)}) ${numbers.slice(2, 7)}-${numbers.slice(7)}`;
    return `(${numbers.slice(0, 2)}) ${numbers.slice(2, 7)}-${numbers.slice(7, 11)}`;
  };

  const formatarCPF = (value: string) => {
    return value.replace(/\D/g, '').slice(0, 11);
  };

  const formatarCEP = (value: string) => {
    return value.replace(/\D/g, '').slice(0, 8);
  };

  if (loading) {
    return (
      <div className="cliente-form-page">
        <div className="loading">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Carregando...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="cliente-form-page">
      <div className="page-header">
        <button className="btn-back" onClick={() => navigate('/clientes')}>
          <FiArrowLeft /> Voltar
        </button>
        <h1>{id ? 'Editar Cliente' : 'Novo Cliente'}</h1>
        {id && (
          <Link to={`/clientes/${id}/enderecos`} className="btn-enderecos">
            <FiMapPin /> Gerenciar Endereços
          </Link>
        )}
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="cliente-form">
        <div className="form-section">
          <h2>Informações Pessoais</h2>

          <div className="form-group">
            <label htmlFor="nome">Nome *</label>
            <input
              id="nome"
              type="text"
              placeholder="Nome completo"
              {...register('nome')}
              className={errors.nome ? 'is-invalid' : ''}
            />
            {errors.nome && <span className="error-message">{errors.nome.message}</span>}
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="cpf">CPF *</label>
              <input
                id="cpf"
                type="text"
                placeholder="00000000000"
                {...register('cpf', {
                  onChange: (e: React.ChangeEvent<HTMLInputElement>) => {
                    e.target.value = formatarCPF(e.target.value);
                  },
                })}
                className={errors.cpf ? 'is-invalid' : ''}
              />
              {errors.cpf && <span className="error-message">{errors.cpf.message}</span>}
            </div>

            <div className="form-group">
              <label htmlFor="telefone">Telefone *</label>
              <input
                id="telefone"
                type="text"
                placeholder="(00) 00000-0000"
                {...register('telefone', {
                  onChange: (e: React.ChangeEvent<HTMLInputElement>) => {
                    e.target.value = formatarTelefone(e.target.value);
                  },
                })}
                className={errors.telefone ? 'is-invalid' : ''}
              />
              {errors.telefone && <span className="error-message">{errors.telefone.message}</span>}
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="email">Email</label>
              <input
                id="email"
                type="email"
                placeholder="email@exemplo.com"
                {...register('email')}
                className={errors.email ? 'is-invalid' : ''}
              />
              {errors.email && <span className="error-message">{errors.email.message}</span>}
            </div>

            <div className="form-group">
              <label htmlFor="data_nasc">Data de Nascimento</label>
              <input
                id="data_nasc"
                type="date"
                {...register('data_nasc')}
                className={errors.data_nasc ? 'is-invalid' : ''}
              />
              {errors.data_nasc && <span className="error-message">{errors.data_nasc.message}</span>}
            </div>
          </div>
        </div>

        <div className="form-section">
          <h2>Informações de Crédito</h2>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="limite_credito">Limite de Crédito (R$) *</label>
              <input
                id="limite_credito"
                type="number"
                step="0.01"
                placeholder="0.00"
                {...register('limite_credito', { valueAsNumber: true })}
                className={errors.limite_credito ? 'is-invalid' : ''}
              />
              {errors.limite_credito && (
                <span className="error-message">{errors.limite_credito.message}</span>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="dia_vencimento">Dia de Vencimento</label>
              <input
                id="dia_vencimento"
                type="number"
                min="1"
                max="28"
                placeholder="1-28"
                {...register('dia_vencimento', { valueAsNumber: true })}
                className={errors.dia_vencimento ? 'is-invalid' : ''}
              />
              {errors.dia_vencimento && (
                <span className="error-message">{errors.dia_vencimento.message}</span>
              )}
            </div>
          </div>

          {cliente && (
            <div className="info-box">
              <div className="info-item">
                <span className="label">Crédito Disponível:</span>
                <span className="value">
                  R$ {cliente.credito_disponivel.toFixed(2).replace('.', ',')}
                </span>
              </div>
              <div className="info-item">
                <span className="label">Status:</span>
                <span className={`value ${cliente.bloqueado ? 'bloqueado' : 'ativo'}`}>
                  {cliente.bloqueado ? 'Bloqueado' : 'Ativo'}
                </span>
              </div>
            </div>
          )}
        </div>

        <div className="form-section">
          <h2>Endereço Principal (Opcional)</h2>
          <p className="section-description">
            Você pode adicionar o endereço principal agora ou depois em "Gerenciar Endereços"
          </p>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="cep">CEP</label>
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
              <label htmlFor="uf">UF</label>
              <input
                id="uf"
                type="text"
                placeholder="SP"
                maxLength={2}
                {...register('uf')}
                className={errors.uf ? 'is-invalid' : ''}
              />
              {errors.uf && <span className="error-message">{errors.uf.message}</span>}
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="logradouro">Logradouro</label>
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
              <label htmlFor="numero">Número</label>
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
              <label htmlFor="bairro">Bairro</label>
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
              <label htmlFor="cidade">Cidade</label>
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
        </div>

        <div className="form-actions">
          <button
            type="button"
            className="btn btn-outline-secondary"
            onClick={() => navigate('/clientes')}
          >
            Cancelar
          </button>
          <button type="submit" className="btn btn-primary" disabled={submitting}>
            <FiSave /> {submitting ? 'Salvando...' : 'Salvar'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default ClienteFormPage;
