import React, { useState, useEffect } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useQueryClient } from '@tanstack/react-query';
import { FiX, FiSave, FiEdit2, FiUserPlus } from 'react-icons/fi';
import { toast } from 'react-toastify';
import { clientesApi } from '@/services/api/clientesApi';
import type { Cliente } from '@/types/clientes';
import { getErrorMessage } from '@/services/api/axios';
import { useAuth } from '@/hooks/useAuth';
import './ClienteFormPage.scss';

const clienteSchema = z.object({
  nome: z.string().min(3, 'Nome deve ter no mínimo 3 caracteres'),
  // CPF/telefone podem vir vazios em clientes criados via loja online/OAuth
  cpf: z.string().regex(/^\d{11}$/, 'CPF deve ter 11 dígitos').or(z.literal('')),
  telefone: z.string().regex(/^\(\d{2}\)\s\d{4,5}-\d{4}$/, 'Telefone inválido').or(z.literal('')),
  email: z.string().email('Email inválido').optional().or(z.literal('')),
  data_nasc: z.string().optional().or(z.literal('')),
  limite_credito: z.number().min(0, 'Limite de crédito não pode ser negativo'),
  // Campo numérico vazio vira NaN (valueAsNumber) — tratar como "não informado"
  dia_vencimento: z.preprocess(
    (v) => (typeof v === 'number' && Number.isNaN(v) ? undefined : v),
    z.number().min(1, 'Dia deve estar entre 1 e 28').max(28, 'Dia deve estar entre 1 e 28').optional()
  ),
  observacoes: z.string().optional().or(z.literal('')),
  ativo: z.union([z.boolean(), z.string()]).default(true),
  cep: z.string().regex(/^\d{8}$/, 'CEP deve ter 8 dígitos').optional().or(z.literal('')),
  logradouro: z.string().min(3, 'Logradouro deve ter no mínimo 3 caracteres').optional().or(z.literal('')),
  numero: z.string().optional().or(z.literal('')),
  complemento: z.string().optional().or(z.literal('')),
  bairro: z.string().min(2, 'Bairro deve ter no mínimo 2 caracteres').optional().or(z.literal('')),
  cidade: z.string().min(2, 'Cidade deve ter no mínimo 2 caracteres').optional().or(z.literal('')),
  uf: z.string().length(2, 'UF deve ter 2 caracteres').optional().or(z.literal('')),
});

type ClienteFormData = z.infer<typeof clienteSchema>;

interface ClienteFormPageProps {
  // Modal mode
  isModal?: boolean;
  clienteId?: string | null;
  onClose?: () => void;
}

const ClienteFormPage: React.FC<ClienteFormPageProps> = ({ isModal, clienteId: modalClienteId, onClose }) => {
  const navigate = useNavigate();
  const { id: routeId } = useParams<{ id: string }>();
  const { user } = useAuth();
  const queryClient = useQueryClient();

  const id = isModal ? (modalClienteId ?? undefined) : routeId;
  const [loading, setLoading] = useState(!!id);
  const [submitting, setSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    setValue,
  } = useForm<ClienteFormData>({
    resolver: zodResolver(clienteSchema),
    defaultValues: { limite_credito: 0, ativo: true },
  });

  useEffect(() => {
    if (id) carregarCliente();
    else { reset({ limite_credito: 0 }); setLoading(false); }
  }, [id]);

  const carregarCliente = async () => {
    try {
      setLoading(true);
      const [clienteData, enderecos] = await Promise.all([
        clientesApi.obter(id!),
        clientesApi.listarEnderecos(id!),
      ]);
      const enderecoPrincipal = enderecos.find((e) => e.principal);
      // Backend guarda telefone em E.164 (+5544...); exibir com a máscara nacional
      const clienteForm = {
        ...clienteData,
        cpf: clienteData.cpf ?? '',
        telefone: telefoneParaMascara(clienteData.telefone),
      };
      if (enderecoPrincipal) {
        reset({ ...clienteForm, cep: enderecoPrincipal.cep, logradouro: enderecoPrincipal.logradouro, numero: enderecoPrincipal.numero, complemento: enderecoPrincipal.complemento || '', bairro: enderecoPrincipal.bairro, cidade: enderecoPrincipal.cidade, uf: enderecoPrincipal.uf });
      } else {
        reset(clienteForm);
      }
    } catch (error) {
      toast.error('Erro ao carregar cliente');
      handleClose();
    } finally {
      setLoading(false);
    }
  };

  const buscarCEP = async (cep: string) => {
    if (cep.length !== 8) return;
    try {
      const response = await fetch(`https://viacep.com.br/ws/${cep}/json/`);
      const data = await response.json();
      if (data.erro) { toast.error('CEP não encontrado'); return; }
      setValue('logradouro', data.logradouro);
      setValue('bairro', data.bairro);
      setValue('cidade', data.localidade);
      setValue('uf', data.uf);
      toast.success('CEP encontrado!');
    } catch { toast.error('Erro ao buscar CEP'); }
  };

  const handleClose = () => {
    if (isModal && onClose) onClose();
    else navigate('/clientes');
  };

  const onSubmit = async (data: ClienteFormData) => {
    try {
      setSubmitting(true);
      const { cep, logradouro, numero, complemento, bairro, cidade, uf } = data;

      if (!id && !data.cpf) { toast.error('CPF é obrigatório'); return; }
      if (!id && !data.telefone) { toast.error('Telefone é obrigatório'); return; }

      // PATCH /clientes aceita apenas dados pessoais; crédito tem endpoint próprio
      const dadosPessoais: Partial<Cliente> = { nome: data.nome };
      if (data.telefone) dadosPessoais.telefone = data.telefone;
      if (data.email) dadosPessoais.email = data.email;
      if (data.data_nasc) dadosPessoais.data_nasc = data.data_nasc;

      let clienteId = id;
      if (id) {
        await clientesApi.atualizar(id, dadosPessoais);
      } else {
        const novo = await clientesApi.criar({ ...dadosPessoais, cpf: data.cpf, empresa_id: user!.empresa_id });
        clienteId = novo.id;
      }

      await clientesApi.atualizarCredito(clienteId!, {
        limite_credito: data.limite_credito,
        dia_vencimento: data.dia_vencimento ?? null,
      });
      toast.success(id ? 'Cliente atualizado com sucesso' : 'Cliente criado com sucesso');
      if (cep && logradouro && numero && bairro && cidade && uf) {
        const enderecoData = { cep, logradouro, numero, complemento: complemento || '', bairro, cidade, uf, principal: true };
        try {
          const enderecos = await clientesApi.listarEnderecos(clienteId!);
          const enderecoPrincipal = enderecos.find((e) => e.principal);
          if (enderecoPrincipal) await clientesApi.atualizarEndereco(clienteId!, enderecoPrincipal.id, enderecoData);
          else await clientesApi.criarEndereco(clienteId!, enderecoData);
        } catch { toast.warning('Cliente salvo, mas houve erro ao salvar o endereço'); }
      }
      await queryClient.invalidateQueries({ queryKey: ['clientes'] });
      handleClose();
    } catch (error) {
      toast.error(getErrorMessage(error, 'Erro ao salvar cliente'));
    } finally {
      setSubmitting(false);
    }
  };

  const formatarTelefone = (value: string) => {
    const n = value.replace(/\D/g, '');
    if (n.length <= 2) return n;
    if (n.length <= 6) return `(${n.slice(0,2)}) ${n.slice(2)}`;
    if (n.length <= 10) return `(${n.slice(0,2)}) ${n.slice(2,7)}-${n.slice(7)}`;
    return `(${n.slice(0,2)}) ${n.slice(2,7)}-${n.slice(7,11)}`;
  };

  /** E.164 (+5544991479093) → máscara nacional ((44) 99147-9093); o +55 fica implícito. */
  const telefoneParaMascara = (telefone: string | null | undefined) => {
    if (!telefone) return '';
    let n = telefone.replace(/\D/g, '');
    if (n.length > 11 && n.startsWith('55')) n = n.slice(2);
    return formatarTelefone(n);
  };

  const formatarCPF = (value: string) => value.replace(/\D/g, '').slice(0, 11);
  const formatarCEP = (value: string) => value.replace(/\D/g, '').slice(0, 8);

  // ── MODAL WRAPPER ──────────────────────────────────────────────────────────
  const formContent = (
    <div className={`cliente-form-modal${isModal ? ' is-modal' : ''}`}>
      {/* Header */}
      <div className="cfm-header">
        <div className="cfm-title">
          <span className="cfm-icon">{id ? <FiEdit2 /> : <FiUserPlus />}</span>
          <h2>{id ? 'Editar Cliente' : 'Novo Cliente'}</h2>
        </div>
        <button className="cfm-close" onClick={handleClose} type="button" title="Fechar">
          <FiX />
        </button>
      </div>

      {loading ? (
        <div className="cfm-loading">Carregando...</div>
      ) : (
        <form onSubmit={handleSubmit(onSubmit)} className="cfm-form">

          {/* ── SEÇÃO: Informações Pessoais ── */}
          <div className="cfm-section">
            <h3 className="cfm-section-title">Informações Pessoais</h3>

            {/* Nome */}
            <div className="cfm-group">
              <label htmlFor="nome">Nome *</label>
              <input id="nome" type="text" placeholder="Nome completo" {...register('nome')} className={errors.nome ? 'invalid' : ''} />
              {errors.nome && <span className="cfm-error">{errors.nome.message}</span>}
            </div>

            {/* CPF + Telefone */}
            <div className="cfm-row">
              <div className="cfm-group">
                <label htmlFor="cpf">CPF *</label>
                <input id="cpf" type="text" placeholder="00000000000" readOnly={!!id} title={id ? 'CPF não pode ser alterado' : undefined} {...register('cpf', { onChange: (e: React.ChangeEvent<HTMLInputElement>) => { e.target.value = formatarCPF(e.target.value); } })} className={errors.cpf ? 'invalid' : ''} />
                {errors.cpf && <span className="cfm-error">{errors.cpf.message}</span>}
              </div>
              <div className="cfm-group">
                <label htmlFor="telefone">Telefone *</label>
                <input id="telefone" type="text" placeholder="(00) 00000-0000" {...register('telefone', { onChange: (e: React.ChangeEvent<HTMLInputElement>) => { e.target.value = formatarTelefone(e.target.value); } })} className={errors.telefone ? 'invalid' : ''} />
                {errors.telefone && <span className="cfm-error">{errors.telefone.message}</span>}
              </div>
            </div>

            {/* Email + Data de Nascimento */}
            <div className="cfm-row">
              <div className="cfm-group">
                <label htmlFor="email">Email</label>
                <input id="email" type="email" placeholder="email@exemplo.com" {...register('email')} className={errors.email ? 'invalid' : ''} />
                {errors.email && <span className="cfm-error">{errors.email.message}</span>}
              </div>
              <div className="cfm-group">
                <label htmlFor="data_nasc">Data de Nascimento</label>
                <input id="data_nasc" type="date" placeholder="dd/mm/aaaa" {...register('data_nasc')} />
              </div>
            </div>
          </div>

          {/* ── SEÇÃO: Informações de Crédito ── */}
          <div className="cfm-section">
            <h3 className="cfm-section-title">Informações de Crédito</h3>

            <div className="cfm-row">
              <div className="cfm-group">
                <label htmlFor="limite_credito">Limite de Crédito (R$) *</label>
                <input id="limite_credito" type="number" step="0.01" placeholder="0.00" {...register('limite_credito', { valueAsNumber: true })} className={errors.limite_credito ? 'invalid' : ''} />
                {errors.limite_credito && <span className="cfm-error">{errors.limite_credito.message}</span>}
              </div>
              <div className="cfm-group">
                <label htmlFor="dia_vencimento">Dia de Vencimento</label>
                <input id="dia_vencimento" type="number" min={1} max={28} placeholder="1-28" {...register('dia_vencimento', { valueAsNumber: true })} className={errors.dia_vencimento ? 'invalid' : ''} />
                {errors.dia_vencimento && <span className="cfm-error">{errors.dia_vencimento.message}</span>}
              </div>
            </div>
          </div>

          {/* ── SEÇÃO: Endereço Principal ── */}
          <div className="cfm-section">
            <h3 className="cfm-section-title">Endereço Principal (Opcional)</h3>
            <p className="cfm-section-hint">
              Você pode adicionar o endereço principal agora ou depois em "Gerenciar Endereços"
            </p>

            {/* CEP + UF */}
            <div className="cfm-row">
              <div className="cfm-group">
                <label htmlFor="cep">CEP</label>
                <input
                  id="cep"
                  type="text"
                  placeholder="00000000"
                  {...register('cep', {
                    onChange: (e: React.ChangeEvent<HTMLInputElement>) => {
                      e.target.value = formatarCEP(e.target.value);
                      if (e.target.value.length === 8) buscarCEP(e.target.value);
                    },
                  })}
                  className={errors.cep ? 'invalid' : ''}
                />
                {errors.cep && <span className="cfm-error">{errors.cep.message}</span>}
              </div>
              <div className="cfm-group">
                <label htmlFor="uf">UF</label>
                <input id="uf" type="text" placeholder="SP" maxLength={2} {...register('uf')} className={errors.uf ? 'invalid' : ''} />
                {errors.uf && <span className="cfm-error">{errors.uf.message}</span>}
              </div>
            </div>

            {/* Logradouro */}
            <div className="cfm-group">
              <label htmlFor="logradouro">Logradouro</label>
              <input id="logradouro" type="text" placeholder="Rua, Avenida, etc." {...register('logradouro')} className={errors.logradouro ? 'invalid' : ''} />
              {errors.logradouro && <span className="cfm-error">{errors.logradouro.message}</span>}
            </div>

            {/* Número + Complemento */}
            <div className="cfm-row">
              <div className="cfm-group">
                <label htmlFor="numero">Número</label>
                <input id="numero" type="text" placeholder="123" {...register('numero')} />
              </div>
              <div className="cfm-group">
                <label htmlFor="complemento">Complemento</label>
                <input id="complemento" type="text" placeholder="Apto, Bloco, etc." {...register('complemento')} />
              </div>
            </div>

            {/* Bairro + Cidade */}
            <div className="cfm-row">
              <div className="cfm-group">
                <label htmlFor="bairro">Bairro</label>
                <input id="bairro" type="text" placeholder="Bairro" {...register('bairro')} className={errors.bairro ? 'invalid' : ''} />
                {errors.bairro && <span className="cfm-error">{errors.bairro.message}</span>}
              </div>
              <div className="cfm-group">
                <label htmlFor="cidade">Cidade</label>
                <input id="cidade" type="text" placeholder="Cidade" {...register('cidade')} className={errors.cidade ? 'invalid' : ''} />
                {errors.cidade && <span className="cfm-error">{errors.cidade.message}</span>}
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="cfm-actions">
            <button type="button" className="cfm-btn-cancel" onClick={handleClose}>Cancelar</button>
            <button type="submit" className="cfm-btn-save" disabled={submitting}>
              {submitting ? 'Salvando...' : 'Salvar Cliente'}
            </button>
          </div>
        </form>
      )}
    </div>
  );

  if (isModal) {
    return (
      <div className="cfm-overlay">
        {formContent}
      </div>
    );
  }

  // Standalone page fallback
  return <div className="cliente-form-page">{formContent}</div>;
};

export default ClienteFormPage;
