import { useEffect } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { empresaSchema, type EmpresaFormData } from './empresaSchema';
import { FiBriefcase, FiSave } from 'react-icons/fi';
import { toast } from 'react-toastify';
import MaskedInput from '@/components/common/MaskedInput/MaskedInput';
import { validateCNPJ } from '@/utils/validators';
import { getErrorMessage } from '@/services/api/axios';
import { useAuth } from '@/hooks/useAuth';
import { useEmpresaCadastro, useAtualizarEmpresaCadastro } from '@/hooks/useEmpresa';
import type { EmpresaCadastroUpdate } from '@/types/empresa';
import './Configuracoes.scss';

const REGIMES: Array<{ value: EmpresaFormData['regime_tributario']; label: string }> = [
  { value: 'SIMPLES_NACIONAL', label: 'Simples Nacional' },
  { value: 'LUCRO_PRESUMIDO', label: 'Lucro Presumido' },
  { value: 'LUCRO_REAL', label: 'Lucro Real' },
  { value: 'MEI', label: 'MEI' },
];

/** Strings vazias viram undefined para não gravar '' por cima de um campo opcional. */
const semVazios = (data: EmpresaFormData): EmpresaCadastroUpdate =>
  Object.fromEntries(Object.entries(data).filter(([, v]) => v !== ''));

const EmpresaPage = () => {
  const { user } = useAuth();
  const { data: empresa, isLoading } = useEmpresaCadastro(user?.empresa_id);
  const atualizar = useAtualizarEmpresaCadastro(user?.empresa_id);

  const {
    register,
    control,
    handleSubmit,
    reset,
    setValue,
    formState: { errors },
  } = useForm<EmpresaFormData>({ resolver: zodResolver(empresaSchema) });

  useEffect(() => {
    if (!empresa) return;
    reset({
      razao_social: empresa.razao_social,
      nome_fantasia: empresa.nome_fantasia,
      slug: empresa.slug,
      cnpj: empresa.cnpj,
      inscricao_estadual: empresa.inscricao_estadual ?? '',
      inscricao_municipal: empresa.inscricao_municipal ?? '',
      regime_tributario: empresa.regime_tributario,
      cep: empresa.cep,
      logradouro: empresa.logradouro,
      numero: empresa.numero,
      complemento: empresa.complemento ?? '',
      bairro: empresa.bairro,
      cidade: empresa.cidade,
      uf: empresa.uf,
      telefone: empresa.telefone ?? '',
      celular: empresa.celular ?? '',
      email: empresa.email ?? '',
      site: empresa.site ?? '',
    });
  }, [empresa, reset]);

  const buscarCEP = async (cep: string) => {
    const digitos = cep.replace(/\D/g, '');
    if (digitos.length !== 8) return;
    try {
      const response = await fetch(`https://viacep.com.br/ws/${digitos}/json/`);
      const data = await response.json();
      if (data.erro) {
        toast.error('CEP não encontrado');
        return;
      }
      setValue('logradouro', data.logradouro);
      setValue('bairro', data.bairro);
      setValue('cidade', data.localidade);
      setValue('uf', data.uf);
    } catch {
      toast.error('Erro ao buscar CEP');
    }
  };

  const onSubmit = async (data: EmpresaFormData) => {
    try {
      await atualizar.mutateAsync(semVazios(data));
      toast.success('Dados da empresa atualizados');
    } catch (error) {
      toast.error(getErrorMessage(error, 'Erro ao salvar dados da empresa'));
    }
  };

  return (
    <div className="page-container empresa-page">
      <div className="page-header">
        <h1><FiBriefcase className="title-icon" /> Dados da Empresa</h1>
        <p className="page-description">
          Configure os dados cadastrais, endereço e informações fiscais da empresa
        </p>
      </div>

      {isLoading ? (
        <div className="loading">Carregando...</div>
      ) : (
        <form onSubmit={handleSubmit(onSubmit)}>
          <div className="form-section">
            <h2>Identificação</h2>

            <div className="form-group">
              <label htmlFor="razao_social">Razão social *</label>
              <input id="razao_social" type="text" {...register('razao_social')} />
              {errors.razao_social && <span className="field-error">{errors.razao_social.message}</span>}
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="nome_fantasia">Nome fantasia *</label>
                <input id="nome_fantasia" type="text" {...register('nome_fantasia')} />
                {errors.nome_fantasia && <span className="field-error">{errors.nome_fantasia.message}</span>}
              </div>
              <div className="form-group">
                <label htmlFor="slug">Slug da loja *</label>
                <input id="slug" type="text" placeholder="minha-loja" {...register('slug')} />
                {errors.slug && <span className="field-error">{errors.slug.message}</span>}
              </div>
            </div>
          </div>

          <div className="form-section">
            <h2>Documentos fiscais</h2>

            <div className="form-row">
              <div className="form-group">
                <Controller
                  name="cnpj"
                  control={control}
                  render={({ field }) => (
                    <MaskedInput
                      mask="cnpj"
                      label="CNPJ"
                      required
                      placeholder="00.000.000/0000-00"
                      value={field.value ?? ''}
                      onChange={field.onChange}
                      onValidate={validateCNPJ}
                      error={errors.cnpj?.message}
                    />
                  )}
                />
              </div>
              <div className="form-group">
                <label htmlFor="regime_tributario">Regime tributário *</label>
                <select id="regime_tributario" {...register('regime_tributario')}>
                  {REGIMES.map((r) => (
                    <option key={r.value} value={r.value}>{r.label}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="inscricao_estadual">Inscrição estadual</label>
                <input id="inscricao_estadual" type="text" placeholder="ISENTO" {...register('inscricao_estadual')} />
              </div>
              <div className="form-group">
                <label htmlFor="inscricao_municipal">Inscrição municipal</label>
                <input id="inscricao_municipal" type="text" {...register('inscricao_municipal')} />
              </div>
            </div>
          </div>

          <div className="form-section">
            <h2>Endereço</h2>

            <div className="form-row">
              <div className="form-group">
                <Controller
                  name="cep"
                  control={control}
                  render={({ field }) => (
                    <MaskedInput
                      mask="cep"
                      label="CEP"
                      required
                      placeholder="00000-000"
                      value={field.value ?? ''}
                      onChange={(v) => { field.onChange(v); buscarCEP(v); }}
                      error={errors.cep?.message}
                    />
                  )}
                />
              </div>
              <div className="form-group">
                <label htmlFor="uf">UF *</label>
                <input id="uf" type="text" maxLength={2} {...register('uf')} />
                {errors.uf && <span className="field-error">{errors.uf.message}</span>}
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="logradouro">Logradouro *</label>
                <input id="logradouro" type="text" {...register('logradouro')} />
                {errors.logradouro && <span className="field-error">{errors.logradouro.message}</span>}
              </div>
              <div className="form-group">
                <label htmlFor="numero">Número *</label>
                <input id="numero" type="text" {...register('numero')} />
                {errors.numero && <span className="field-error">{errors.numero.message}</span>}
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="complemento">Complemento</label>
                <input id="complemento" type="text" {...register('complemento')} />
              </div>
              <div className="form-group">
                <label htmlFor="bairro">Bairro *</label>
                <input id="bairro" type="text" {...register('bairro')} />
                {errors.bairro && <span className="field-error">{errors.bairro.message}</span>}
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="cidade">Cidade *</label>
              <input id="cidade" type="text" {...register('cidade')} />
              {errors.cidade && <span className="field-error">{errors.cidade.message}</span>}
            </div>
          </div>

          <div className="form-section">
            <h2>Contato</h2>

            <div className="form-row">
              <div className="form-group">
                <Controller
                  name="telefone"
                  control={control}
                  render={({ field }) => (
                    <MaskedInput
                      mask="phone"
                      label="Telefone"
                      placeholder="(00) 0000-0000"
                      value={field.value ?? ''}
                      onChange={field.onChange}
                    />
                  )}
                />
              </div>
              <div className="form-group">
                <Controller
                  name="celular"
                  control={control}
                  render={({ field }) => (
                    <MaskedInput
                      mask="phone"
                      label="Celular"
                      placeholder="(00) 00000-0000"
                      value={field.value ?? ''}
                      onChange={field.onChange}
                    />
                  )}
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="email">E-mail</label>
                <input id="email" type="email" {...register('email')} />
                {errors.email && <span className="field-error">{errors.email.message}</span>}
              </div>
              <div className="form-group">
                <label htmlFor="site">Site</label>
                <input id="site" type="text" placeholder="https://" {...register('site')} />
              </div>
            </div>
          </div>

          <div className="form-section plano-card">
            <h2>Plano e limites</h2>
            <p className="section-hint">
              Definido pela plataforma. Para mudar de plano, fale com o suporte.
            </p>
            <dl className="plano-grid">
              <div><dt>Plano</dt><dd>{empresa?.plano ?? '—'}</dd></div>
              <div><dt>Status</dt><dd>{empresa?.status ?? '—'}</dd></div>
              <div><dt>Usuários</dt><dd>{empresa?.max_usuarios ?? '—'}</dd></div>
              <div><dt>Produtos</dt><dd>{empresa?.max_produtos ?? 'Ilimitado'}</dd></div>
            </dl>
          </div>

          <div className="form-actions">
            <button type="submit" className="btn btn-primary" disabled={atualizar.isPending}>
              <FiSave /> {atualizar.isPending ? 'Salvando...' : 'Salvar alterações'}
            </button>
          </div>
        </form>
      )}
    </div>
  );
};

export default EmpresaPage;
