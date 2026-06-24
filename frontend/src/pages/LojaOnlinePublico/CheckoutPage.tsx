import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { FiArrowLeft, FiUser, FiTruck, FiCreditCard, FiCheck, FiAlertCircle, FiLogIn, FiUserPlus } from 'react-icons/fi';
import axios from 'axios';
import { useCarrinho } from '@/hooks/useCarrinho';
import MaskedInput from '@/components/common/MaskedInput/MaskedInput';
import { validateCPF, validateEmail, validatePhone, validateCEP, validateRequired } from '@/utils/validators';
import { unmask, maskCurrency } from '@/utils/masks';
import { Toast } from '@/utils/toast';
import './CheckoutPage.scss';

// API Configuration
const apiPublica = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

// Types - Checkout Form Data Structures
interface ClienteNovo {
  nome: string;
  telefone: string;
  email?: string;
  cpf?: string;
}

interface Endereco {
  cep: string;
  logradouro: string;
  numero: string;
  complemento?: string;
  bairro: string;
  cidade: string;
  estado: string;
}

interface Pagamento {
  forma_pagamento: 'PIX' | 'DEBITO' | 'CREDITO' | 'DINHEIRO' | 'FIADO';
  valor: number;
}

type TipoEntrega = 'RETIRADA' | 'DELIVERY';
type Step = 1 | 2 | 3;
type ModoCheckout = 'selecao' | 'login' | 'guest';

const CheckoutPage = () => {
  const { empresaSlug } = useParams<{ empresaSlug: string }>();
  const navigate = useNavigate();
  const { carrinho, limparCarrinho } = useCarrinho({ empresaSlug });

  // Modo de checkout
  const [modoCheckout, setModoCheckout] = useState<ModoCheckout>('selecao');
  const [criarConta, setCriarConta] = useState(false);

  // Login
  const [loginEmail, setLoginEmail] = useState('');
  const [loginSenha, setLoginSenha] = useState('');
  const [fazendoLogin, setFazendoLogin] = useState(false);

  // Steps
  const [currentStep, setCurrentStep] = useState<Step>(1);

  // Step 1: Dados do Cliente
  const [clienteNovo, setClienteNovo] = useState<ClienteNovo>({
    nome: '',
    telefone: '',
    email: '',
    cpf: '',
  });

  // Step 2: Entrega
  const [tipoEntrega, setTipoEntrega] = useState<TipoEntrega>('RETIRADA');
  const [endereco, setEndereco] = useState<Endereco>({
    cep: '',
    logradouro: '',
    numero: '',
    complemento: '',
    bairro: '',
    cidade: '',
    estado: '',
  });
  const [frete, setFrete] = useState<number>(0);
  const [buscandoCep, setBuscandoCep] = useState(false);

  // Step 3: Pagamento
  const [formaPagamento, setFormaPagamento] = useState<'PIX' | 'DEBITO' | 'CREDITO' | 'DINHEIRO' | 'FIADO'>('PIX');
  const [valorDinheiro, setValorDinheiro] = useState<string>('');
  const [troco, setTroco] = useState<number>(0);

  // Estados gerais
  const [finalizando, setFinalizando] = useState(false);
  const [erro, setErro] = useState('');

  // Calcular troco quando forma for DINHEIRO
  useEffect(() => {
    if (formaPagamento === 'DINHEIRO' && valorDinheiro && carrinho) {
      const valor = parseFloat(valorDinheiro.replace(',', '.'));
      const subtotalNum = parseFloat(carrinho.subtotal);
      const total = subtotalNum + frete;
      setTroco(Math.max(0, valor - total));
    } else {
      setTroco(0);
    }
  }, [valorDinheiro, formaPagamento, carrinho, frete]);

  // Função de Login
  const fazerLogin = async () => {
    if (!loginEmail || !loginSenha) {
      Toast.error('Preencha email e senha');
      return;
    }

    setFazendoLogin(true);
    try {
      const response = await apiPublica.post(`/auth/cliente/login?empresaSlug=${empresaSlug}`, {
        email: loginEmail,
        senha: loginSenha,
      });

      const { access_token, cliente } = response.data;

      // Salvar token
      localStorage.setItem('cliente_token', access_token);
      
      // Preencher dados do cliente
      setClienteNovo({
        nome: cliente.nome,
        telefone: cliente.telefone || '',
        email: cliente.email,
        cpf: cliente.cpf || '',
      });

      // Ir para step 1 (dados já preenchidos)
      setModoCheckout('guest');
      setCurrentStep(1);
      
      Toast.success(`Bem-vindo de volta, ${cliente.nome}!`);
    } catch (error: any) {
      const mensagem = error.response?.data?.detail || 'Erro ao fazer login';
      Toast.error(mensagem);
    } finally {
      setFazendoLogin(false);
    }
  };

  // Buscar CEP via ViaCEP
  const buscarCep = async (cep: string) => {
    const cepLimpo = cep.replace(/\D/g, '');
    if (cepLimpo.length !== 8) return;

    try {
      setBuscandoCep(true);
      const response = await fetch(`https://viacep.com.br/ws/${cepLimpo}/json/`);
      const data = await response.json();

      if (data.erro) {
        setErro('CEP não encontrado');
        return;
      }

      setEndereco((prev) => ({
        ...prev,
        cep: cepLimpo,
        logradouro: data.logradouro || '',
        bairro: data.bairro || '',
        cidade: data.localidade || '',
        estado: data.uf || '',
      }));

      // Calcular frete (simulação - backend faz o cálculo real)
      setFrete(8.0); // Valor fixo por enquanto
    } catch (error) {
      setErro('Erro ao buscar CEP');
    } finally {
      setBuscandoCep(false);
    }
  };

  // Validações por step
  const validarStep1 = (): boolean => {
    setErro('');
    
    const nomeError = validateRequired(clienteNovo.nome, 'Nome');
    if (nomeError) {
      Toast.error(nomeError);
      return false;
    }
    
    const telefoneError = validatePhone(clienteNovo.telefone);
    if (telefoneError) {
      Toast.error(telefoneError);
      return false;
    }
    
    // Email é opcional, mas se preenchido deve ser válido
    if (clienteNovo.email) {
      const emailError = validateEmail(clienteNovo.email);
      if (emailError) {
        Toast.error(emailError);
        return false;
      }
    }
    
    // CPF é opcional, mas se preenchido deve ser válido
    if (clienteNovo.cpf) {
      const cpfError = validateCPF(clienteNovo.cpf);
      if (cpfError) {
        Toast.error(cpfError);
        return false;
      }
    }
    
    return true;
  };

  const validarStep2 = (): boolean => {
    setErro('');
    
    if (tipoEntrega === 'DELIVERY') {
      const cepError = validateCEP(endereco.cep);
      if (cepError) {
        Toast.error(cepError);
        return false;
      }
      
      if (!endereco.logradouro || !endereco.numero || !endereco.bairro) {
        Toast.error('Preencha todos os campos obrigatórios do endereço');
        return false;
      }
    }
    return true;
  };

  const proximoStep = () => {
    setErro('');
    
    if (currentStep === 1 && !validarStep1()) return;
    if (currentStep === 2 && !validarStep2()) return;
    
    setCurrentStep((prev) => Math.min(3, prev + 1) as Step);
  };

  const voltarStep = () => {
    setErro('');
    setCurrentStep((prev) => Math.max(1, prev - 1) as Step);
  };

  // Finalizar Compra
  const finalizarCompra = async () => {
    setErro('');
    setFinalizando(true);

    // Toast de loading
    const toastId = Toast.loading('Processando pedido...');

    try {
      const payload: any = {
        cliente_novo: {
          nome: clienteNovo.nome,
          telefone: unmask(clienteNovo.telefone), // Remove máscara
          email: clienteNovo.email || undefined, // Não envia se vazio
          cpf: clienteNovo.cpf ? unmask(clienteNovo.cpf) : undefined, // Remove máscara
        },
        criar_conta: criarConta, // Flag para criar conta automaticamente
        tipo_entrega: tipoEntrega,
        endereco_entrega: tipoEntrega === 'DELIVERY' ? {
          cep: unmask(endereco.cep), // Remove máscara
          logradouro: endereco.logradouro,
          numero: endereco.numero,
          complemento: endereco.complemento || undefined,
          bairro: endereco.bairro,
          cidade: endereco.cidade,
          estado: endereco.estado,
        } : undefined,
        pagamentos: [
          {
            forma_pagamento: formaPagamento,
            valor: parseFloat(carrinho.subtotal) + frete,
          },
        ],
      };

      console.log('📦 Payload enviado:', JSON.stringify(payload, null, 2));

      const response = await apiPublica.post(`/loja/checkout?empresaSlug=${empresaSlug}`, payload);
      const { venda_id, numero_venda, mercadopago_init_point } = response.data;

      // Atualiza toast para sucesso
      Toast.update(toastId, 'success', 'Pedido realizado com sucesso!');

      // Se pagamento online (PIX/Cartão), redirecionar IMEDIATAMENTE para Mercado Pago
      // O backend já limpou o carrinho, não precisamos fazer no frontend antes de sair
      if (mercadopago_init_point) {
        // Redirecionar imediatamente sem limpar carrinho no frontend
        // (evita mostrar carrinho vazio antes de redirecionar)
        window.location.href = mercadopago_init_point;
        return; // Importante: retornar para não executar código abaixo
      }

      // Se pagamento offline, limpar carrinho e ir para rastreamento
      await limparCarrinho();
      navigate(`/c/${empresaSlug}/pedido/${numero_venda}`, {
        state: { sucesso: true },
      });
    } catch (error: any) {
      // Atualiza toast para erro e usa tratamento de erro da API
      Toast.dismiss(toastId);
      
      // Extrair mensagem de erro do objeto
      let mensagemErro = 'Erro ao processar pedido';
      
      if (error.response?.data) {
        const { detail } = error.response.data;
        
        // Se detail for um array de erros de validação
        if (Array.isArray(detail)) {
          mensagemErro = detail.map((err: any) => err.msg || err.message || JSON.stringify(err)).join('; ');
        }
        // Se detail for uma string
        else if (typeof detail === 'string') {
          mensagemErro = detail;
        }
        // Se detail for um objeto
        else if (typeof detail === 'object') {
          mensagemErro = detail.msg || detail.message || JSON.stringify(detail);
        }
      } else if (error.message) {
        mensagemErro = error.message;
      }
      
      Toast.error(mensagemErro);
      setErro(mensagemErro);
    } finally {
      setFinalizando(false);
    }
  };

  // Formatadores
  const formatarTelefone = (value: string) => {
    const limpo = value.replace(/\D/g, '');
    if (limpo.length <= 10) {
      return limpo.replace(/(\d{2})(\d{4})(\d{0,4})/, '($1) $2-$3');
    }
    return limpo.replace(/(\d{2})(\d{5})(\d{0,4})/, '($1) $2-$3');
  };

  const formatarCep = (value: string) => {
    const limpo = value.replace(/\D/g, '');
    return limpo.replace(/(\d{5})(\d{0,3})/, '$1-$2');
  };

  const formatarCpf = (value: string) => {
    const limpo = value.replace(/\D/g, '');
    return limpo.replace(/(\d{3})(\d{3})(\d{3})(\d{0,2})/, '$1.$2.$3-$4');
  };

  const formatarPreco = (valor: string | number) => {
    const valorNum = typeof valor === 'string' ? parseFloat(valor) : valor;
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valorNum);
  };

  // Early return se carrinho vazio
  if (!carrinho || carrinho.itens.length === 0) {
    return (
      <div className="checkout-page">
        <div className="checkout-vazio">
          <div className="vazio-icon">🛒</div>
          <h2>Seu carrinho está vazio</h2>
          <p>Adicione produtos para continuar</p>
          <button onClick={() => navigate(`/c/${empresaSlug}`)}>
            Ver produtos
          </button>
        </div>
      </div>
    );
  }

  const total = parseFloat(carrinho.subtotal) + frete;

  return (
    <div className="checkout-page">
      {/* Header */}
      <header className="checkout-header">
        <button className="btn-voltar" onClick={() => navigate(`/c/${empresaSlug}/carrinho`)}>
          <FiArrowLeft /> Voltar ao carrinho
        </button>
        <h1>Finalizar Compra</h1>
      </header>

      {/* Steps Indicator - Temporariamente oculto */}
      {/* TODO: Implementar stepper em modal/drawer separado */}
      {/* <div className="steps-indicator">...</div> */}

      {erro && (
        <div className="erro-mensagem">
          <FiAlertCircle /> {erro}
        </div>
      )}

      <div className="checkout-container">
        {/* Seleção de Modo: Login ou Guest */}
        {modoCheckout === 'selecao' && (
          <div className="modo-checkout-selecao">
            <div className="modo-card">
              <div className="modo-header">
                <FiLogIn size={32} />
                <h2>Já sou cliente</h2>
              </div>
              <p>Faça login para checkout mais rápido com seus dados salvos</p>
              <ul className="beneficios">
                <li><FiCheck /> Endereços salvos</li>
                <li><FiCheck /> Histórico de pedidos</li>
                <li><FiCheck /> Recompra rápida</li>
              </ul>
              <button className="btn-primary" onClick={() => setModoCheckout('login')}>
                Fazer Login
              </button>
            </div>

            <div className="modo-card">
              <div className="modo-header">
                <FiUserPlus size={32} />
                <h2>Continuar como convidado</h2>
              </div>
              <p>Compra rápida sem precisar criar uma conta</p>
              <ul className="beneficios">
                <li><FiCheck /> Checkout rápido</li>
                <li><FiCheck /> Sem cadastro obrigatório</li>
                <li><FiCheck /> Opção de criar conta depois</li>
              </ul>
              <button className="btn-secondary" onClick={() => setModoCheckout('guest')}>
                Continuar
              </button>
            </div>
          </div>
        )}

        {/* Tela de Login */}
        {modoCheckout === 'login' && (
          <div className="login-checkout">
            <div className="login-card">
              <h2><FiUser /> Login</h2>
              <p>Entre com seus dados para continuar</p>

              {/* Social Login Buttons */}
              <div className="social-login-buttons">
                <button
                  className="btn-google"
                  onClick={() => {
                    // TODO: Implementar login com Google
                    alert('Login com Google em desenvolvimento');
                  }}
                  disabled={fazendoLogin}
                >
                  <svg viewBox="0 0 24 24" width="18" height="18">
                    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                  </svg>
                  Continuar com Google
                </button>

                <button
                  className="btn-microsoft"
                  onClick={() => {
                    // TODO: Implementar login com Microsoft
                    alert('Login com Microsoft em desenvolvimento');
                  }}
                  disabled={fazendoLogin}
                >
                  <svg viewBox="0 0 24 24" width="18" height="18">
                    <path fill="#f25022" d="M1 1h10v10H1z"/>
                    <path fill="#00a4ef" d="M13 1h10v10H13z"/>
                    <path fill="#7fba00" d="M1 13h10v10H1z"/>
                    <path fill="#ffb900" d="M13 13h10v10H13z"/>
                  </svg>
                  Continuar com Microsoft
                </button>
              </div>

              <div className="divider">
                <span>ou entre com email</span>
              </div>

              <div className="form-group">
                <label>Email *</label>
                <input
                  type="email"
                  value={loginEmail}
                  onChange={(e) => setLoginEmail(e.target.value)}
                  placeholder="seu@email.com"
                  disabled={fazendoLogin}
                />
              </div>

              <div className="form-group">
                <label>Senha *</label>
                <input
                  type="password"
                  value={loginSenha}
                  onChange={(e) => setLoginSenha(e.target.value)}
                  placeholder="••••••••"
                  disabled={fazendoLogin}
                />
              </div>

              <div className="login-actions">
                <button
                  className="btn-primary"
                  onClick={fazerLogin}
                  disabled={fazendoLogin}
                >
                  {fazendoLogin ? 'Entrando...' : 'Entrar'}
                </button>
                <button
                  className="btn-link"
                  onClick={() => setModoCheckout('selecao')}
                  disabled={fazendoLogin}
                >
                  Voltar
                </button>
              </div>

              <div className="login-footer">
                <p>
                  Não tem conta?{' '}
                  <button
                    className="btn-link-inline"
                    onClick={() => setModoCheckout('guest')}
                  >
                    Continue como convidado
                  </button>
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Formulário - Só exibe se modo for 'guest' */}
        {modoCheckout === 'guest' && (
          <>
        <div className="checkout-form">
          {/* Step 1: Dados do Cliente */}
          {currentStep === 1 && (
            <div className="form-section">
              <h2>Seus dados</h2>
              <p className="section-description">Informe seus dados para contato</p>

              <div className="form-group">
                <label>Nome completo *</label>
                <input
                  type="text"
                  value={clienteNovo.nome}
                  onChange={(e) => setClienteNovo({ ...clienteNovo, nome: e.target.value })}
                  placeholder="Ex: João Silva"
                />
              </div>

              <MaskedInput
                mask="phone"
                value={clienteNovo.telefone}
                onChange={(value) => setClienteNovo({ ...clienteNovo, telefone: value })}
                onValidate={validatePhone}
                label="Telefone (WhatsApp)"
                placeholder="(11) 99999-9999"
                helperText="Usaremos para enviar atualizações do pedido"
                showValidation={true}
                required
              />

              <MaskedInput
                value={clienteNovo.email || ''}
                onChange={(value) => setClienteNovo({ ...clienteNovo, email: value })}
                onValidate={validateEmail}
                label="E-mail"
                placeholder="seu@email.com"
                type="email"
                showValidation={true}
              />

              <MaskedInput
                mask="cpf"
                value={clienteNovo.cpf || ''}
                onChange={(value) => setClienteNovo({ ...clienteNovo, cpf: value })}
                onValidate={validateCPF}
                label="CPF (opcional)"
                placeholder="000.000.000-00"
                showValidation={true}
              />

              {/* Checkbox Criar Conta */}
              <div className="criar-conta-checkbox">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={criarConta}
                    onChange={(e) => setCriarConta(e.target.checked)}
                  />
                  <span className="checkbox-text">
                    <strong>Criar uma conta para mim</strong>
                    <small>
                      Facilita rastreamento de pedidos e recompras rápidas. 
                      Você receberá suas credenciais por email.
                    </small>
                  </span>
                </label>
              </div>

              <button className="btn-proximo" onClick={proximoStep}>
                Continuar <FiCheck />
              </button>
            </div>
          )}

          {/* Step 2: Entrega */}
          {currentStep === 2 && (
            <div className="form-section">
              <h2>Tipo de entrega</h2>

              <div className="entrega-opcoes">
                <label className={`entrega-opcao ${tipoEntrega === 'RETIRADA' ? 'selected' : ''}`}>
                  <input
                    type="radio"
                    name="entrega"
                    value="RETIRADA"
                    checked={tipoEntrega === 'RETIRADA'}
                    onChange={() => {
                      setTipoEntrega('RETIRADA');
                      setFrete(0);
                    }}
                  />
                  <div className="opcao-content">
                    <strong>Retirar no local</strong>
                    <span className="opcao-preco">Grátis</span>
                  </div>
                </label>

                <label className={`entrega-opcao ${tipoEntrega === 'DELIVERY' ? 'selected' : ''}`}>
                  <input
                    type="radio"
                    name="entrega"
                    value="DELIVERY"
                    checked={tipoEntrega === 'DELIVERY'}
                    onChange={() => setTipoEntrega('DELIVERY')}
                  />
                  <div className="opcao-content">
                    <strong>Entrega em domicílio</strong>
                    <span className="opcao-preco">
                      {frete > 0 ? formatarPreco(frete) : 'Calcular'}
                    </span>
                  </div>
                </label>
              </div>

              {tipoEntrega === 'DELIVERY' && (
                <div className="endereco-form">
                  <h3>Endereço de entrega</h3>

                  <MaskedInput
                    mask="cep"
                    value={endereco.cep}
                    onChange={(value) => {
                      setEndereco({ ...endereco, cep: value });
                      // Busca CEP quando estiver completo
                      const cleaned = unmask(value);
                      if (cleaned.length === 8) {
                        buscarCep(value);
                      }
                    }}
                    onValidate={validateCEP}
                    label="CEP"
                    placeholder="00000-000"
                    helperText={buscandoCep ? 'Buscando endereço...' : ''}
                    showValidation={true}
                    required
                  />

                  <div className="form-row">
                    <div className="form-group">
                      <label>Logradouro *</label>
                      <input
                        type="text"
                        value={endereco.logradouro}
                        onChange={(e) => setEndereco({ ...endereco, logradouro: e.target.value })}
                        placeholder="Rua, Avenida..."
                      />
                    </div>

                    <div className="form-group form-group-small">
                      <label>Número *</label>
                      <input
                        type="text"
                        value={endereco.numero}
                        onChange={(e) => setEndereco({ ...endereco, numero: e.target.value })}
                        placeholder="123"
                      />
                    </div>
                  </div>

                  <div className="form-group">
                    <label>Complemento</label>
                    <input
                      type="text"
                      value={endereco.complemento}
                      onChange={(e) => setEndereco({ ...endereco, complemento: e.target.value })}
                      placeholder="Apto, Bloco..."
                    />
                  </div>

                  <div className="form-row">
                    <div className="form-group">
                      <label>Bairro *</label>
                      <input
                        type="text"
                        value={endereco.bairro}
                        onChange={(e) => setEndereco({ ...endereco, bairro: e.target.value })}
                        placeholder="Centro"
                      />
                    </div>

                    <div className="form-group">
                      <label>Cidade *</label>
                      <input
                        type="text"
                        value={endereco.cidade}
                        onChange={(e) => setEndereco({ ...endereco, cidade: e.target.value })}
                        placeholder="São Paulo"
                      />
                    </div>

                    <div className="form-group form-group-small">
                      <label>UF *</label>
                      <input
                        type="text"
                        value={endereco.estado}
                        onChange={(e) => setEndereco({ ...endereco, estado: e.target.value.toUpperCase() })}
                        placeholder="SP"
                        maxLength={2}
                      />
                    </div>
                  </div>
                </div>
              )}

              <div className="form-buttons">
                <button className="btn-voltar-step" onClick={voltarStep}>
                  <FiArrowLeft /> Voltar
                </button>
                <button className="btn-proximo" onClick={proximoStep}>
                  Continuar <FiCheck />
                </button>
              </div>
            </div>
          )}

          {/* Step 3: Pagamento */}
          {currentStep === 3 && (
            <div className="form-section">
              <h2>Forma de pagamento</h2>

              <div className="pagamento-opcoes">
                <label className={`pagamento-opcao ${formaPagamento === 'PIX' ? 'selected' : ''}`}>
                  <input
                    type="radio"
                    name="pagamento"
                    value="PIX"
                    checked={formaPagamento === 'PIX'}
                    onChange={() => setFormaPagamento('PIX')}
                  />
                  <div className="opcao-content">
                    <strong>PIX</strong>
                    <span>Pagamento instantâneo via Mercado Pago</span>
                  </div>
                </label>

                <label className={`pagamento-opcao ${formaPagamento === 'DEBITO' ? 'selected' : ''}`}>
                  <input
                    type="radio"
                    name="pagamento"
                    value="DEBITO"
                    checked={formaPagamento === 'DEBITO'}
                    onChange={() => setFormaPagamento('DEBITO')}
                  />
                  <div className="opcao-content">
                    <strong>Cartão de Débito</strong>
                    <span>Aprovação imediata</span>
                  </div>
                </label>

                <label className={`pagamento-opcao ${formaPagamento === 'CREDITO' ? 'selected' : ''}`}>
                  <input
                    type="radio"
                    name="pagamento"
                    value="CREDITO"
                    checked={formaPagamento === 'CREDITO'}
                    onChange={() => setFormaPagamento('CREDITO')}
                  />
                  <div className="opcao-content">
                    <strong>Cartão de Crédito</strong>
                    <span>Parcelamento disponível</span>
                  </div>
                </label>

                <label className={`pagamento-opcao ${formaPagamento === 'DINHEIRO' ? 'selected' : ''}`}>
                  <input
                    type="radio"
                    name="pagamento"
                    value="DINHEIRO"
                    checked={formaPagamento === 'DINHEIRO'}
                    onChange={() => setFormaPagamento('DINHEIRO')}
                  />
                  <div className="opcao-content">
                    <strong>Dinheiro</strong>
                    <span>Pagamento na entrega/retirada</span>
                  </div>
                </label>
              </div>

              {formaPagamento === 'DINHEIRO' && (
                <div className="form-group">
                  <label>Troco para quanto?</label>
                  <input
                    type="text"
                    value={valorDinheiro}
                    onChange={(e) => setValorDinheiro(e.target.value)}
                    placeholder="Ex: 100.00"
                  />
                  {troco > 0 && (
                    <small className="troco-info">Troco: {formatarPreco(troco)}</small>
                  )}
                </div>
              )}

              <div className="form-buttons">
                <button className="btn-voltar-step" onClick={voltarStep}>
                  <FiArrowLeft /> Voltar
                </button>
                <button
                  className="btn-finalizar"
                  onClick={finalizarCompra}
                  disabled={finalizando}
                >
                  {finalizando ? 'Processando...' : 'Finalizar Pedido'}
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Resumo - Exibe tanto para guest quanto para login */}
        {(modoCheckout === 'guest' || modoCheckout === 'login') && (
        <div className="checkout-resumo">
          <h3>Resumo do pedido</h3>

          <div className="resumo-itens">
            {carrinho.itens.map((item) => {
              const itemKey = `${item.produto_id}-${item.variante_id || 'null'}`;
              const quantidadeNum = parseFloat(item.quantidade);
              
              return (
                <div key={itemKey} className="resumo-item">
                  <span className="item-nome">
                    {quantidadeNum}x {item.descricao_produto}
                  </span>
                  <span className="item-preco">{formatarPreco(item.subtotal)}</span>
                </div>
              );
            })}
          </div>

          <div className="resumo-totais">
            <div className="total-linha">
              <span>Subtotal</span>
              <span>{formatarPreco(carrinho.subtotal)}</span>
            </div>
            <div className="total-linha">
              <span>Frete</span>
              <span>{frete > 0 ? formatarPreco(frete) : 'Grátis'}</span>
            </div>
            <div className="total-linha total-final">
              <span>Total</span>
              <span>{formatarPreco(total)}</span>
            </div>
          </div>
        </div>
        )}
          </>
        )}
      </div>

      <footer className="loja-online-footer">
        <p>Powered by <strong>Runas ERP</strong></p>
      </footer>
    </div>
  );
};

export default CheckoutPage;
