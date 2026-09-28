# Guia: Máscaras e Validações

## 📚 Como está implementado

### Backend

O comportamento **não é uniforme** entre serviços. Confira o schema do serviço antes de decidir se envia com ou sem máscara:

| Campo | Serviço / schema | Aceita | Armazena | Validação |
|-------|------------------|--------|----------|-----------|
| CPF | clientes — `ClienteBase.cpf` (`services/clientes/schemas/cliente.py`) | com ou sem máscara (11 a 14 caracteres) | só dígitos | dígito verificador via `validate_docbr` (`services/clientes/utils/validators.py`) |
| CPF | vendas — `ClienteCheckout.cpf` (`services/vendas/schemas/loja.py`), opcional | com ou sem máscara (11 a 14 caracteres) | só dígitos | dígito verificador em `ClienteValidacaoService.validar_cpf` (`services/vendas/services/cliente_validacao_service.py`) |
| CPF | api-gateway — `ClienteRegisterRequest.cpf` (`api-gateway/schemas/cliente.py`, registro de comprador em `auth_cliente.py`) | **somente sem máscara** (exatamente 11 dígitos) | repassa ao serviço de clientes | só dígitos; o dígito verificador fica a cargo do serviço de clientes |
| Telefone | clientes — `ClienteBase.telefone` | qualquer formato | **E.164** (`+55` + DDD + número), via `normalizar_telefone` | 10 ou 11 dígitos sem `+`, ou E.164 válido |
| Telefone | vendas — `ClienteCheckout.telefone` | com ou sem máscara (10 a 15 caracteres) | só dígitos | 10 ou 11 dígitos |
| CNPJ | empresas — `EmpresaBase.cnpj` (`services/empresas/schemas/empresa.py`) | **somente com máscara** `XX.XXX.XXX/XXXX-XX` (18 caracteres) | com máscara | formato + dígito verificador via `validate_docbr` (`services/empresas/utils/validators.py`) |
| CEP | clientes — `EnderecoBase.cep` | exatamente 8 caracteres (ou seja, **sem** máscara) | sem máscara | só tamanho |
| CEP | vendas — `EnderecoEntregaCheckout.cep` | regex `^\d{8}$` (**sem** máscara) | sem máscara | só formato |
| CEP | empresas — `EmpresaBase.cep` | **somente com máscara** `XXXXX-XXX` (9 caracteres) | com máscara | só formato |

Resumo: para clientes e vendas, envie CEP sem máscara; para empresas, envie CNPJ e CEP **com** máscara.

### Frontend

- Máscaras visuais nos inputs via componente `MaskedInput`
- Validação no blur e, com `showValidation`, também durante a digitação (depois do primeiro blur)
- Remoção de máscara com `unmask()` antes do envio, quando o backend exige só dígitos
- Notificações com `Toast` (wrapper do react-toastify). Ainda restam 3 `alert()` em `frontend/src/pages/LojaOnlinePublico/` (`LojaOnlinePublicoPage.tsx`, `ProdutoDetalhePage.tsx`)

---

## 🎭 Usando Máscaras

### Importar Funções

```typescript
import { maskCurrency, unmask } from '@/utils/masks';
```

### Funções de `frontend/src/utils/masks.ts`

| Máscara | Formato | Função | Usada hoje? |
|---------|---------|--------|-------------|
| CPF | 000.000.000-00 | `maskCPF(value: string): string` | Não (sem chamadores) |
| CNPJ | 00.000.000/0000-00 | `maskCNPJ(value: string): string` | Não (sem chamadores) |
| Telefone | (00) 00000-0000 | `maskPhone(value: string): string` | Não (sem chamadores) |
| CEP | 00000-000 | `maskCEP(value: string): string` | Não (sem chamadores) |
| Data | DD/MM/AAAA | `maskDate(value: string): string` | Não (sem chamadores) |
| Cartão | 0000 0000 0000 0000 | `maskCreditCard(value: string): string` | Não (sem chamadores) |
| Moeda | R$ 0.000,00 (`Intl.NumberFormat` pt-BR/BRL) | `maskCurrency(value: string \| number): string` | Sim (`CheckoutPage.tsx`) |
| Remove formatação | só dígitos | `unmask(value: string): string` | Sim (`CheckoutPage.tsx`) |
| Moeda → número | `number` | `unmaskCurrency(value: string): number` | Não (sem chamadores) |

As funções `maskCPF`, `maskCNPJ`, `maskPhone`, `maskCEP`, `maskDate` e `maskCreditCard` existem mas são código morto: o `MaskedInput` reimplementa a mesma formatação internamente (`applyMask`) e não importa `masks.ts`. Para mascarar um input, use o `MaskedInput`.

### Remover Máscaras

```typescript
import { unmask } from '@/utils/masks';

const cpfFormatado = '123.456.789-09';
const cpfLimpo = unmask(cpfFormatado); // '12345678909'
```

---

## ✅ Validações

Todos os validadores de `frontend/src/utils/validators.ts` retornam `string | null`: `null` se válido, mensagem de erro se inválido.

### Importar Validadores

```typescript
import { validateCPF, validateEmail, validatePhone } from '@/utils/validators';
```

### Validadores Disponíveis

| Função | Regra | Usada hoje? |
|--------|-------|-------------|
| `validateCPF(cpf: string)` | 11 dígitos, rejeita sequência repetida, dígitos verificadores | Sim (`CheckoutPage.tsx`) |
| `validateCNPJ(cnpj: string)` | 14 dígitos, rejeita sequência repetida, dígitos verificadores | Sim (`EmpresaPage.tsx`, `PlataformaPage.tsx`) |
| `validateEmail(email: string)` | obrigatório + regex `^[^\s@]+@[^\s@]+\.[^\s@]+$` | Sim (`CheckoutPage.tsx`) |
| `validatePhone(phone: string)` | 10 ou 11 dígitos, DDD não começa com 0 | Sim (`CheckoutPage.tsx`) |
| `validateCEP(cep: string)` | 8 dígitos | Sim (`CheckoutPage.tsx`) |
| `validateRequired(value: any, fieldName = 'Campo')` | não vazio / não só espaços | Sim (`CheckoutPage.tsx`) |
| `validatePassword(password: string)` | mín. 8 caracteres, 1 maiúscula, 1 minúscula, 1 número, 1 especial de `!@#$%^&*` | Não (sem chamadores) |
| `validateDate(date: string)` | DD/MM/AAAA, mês 1-12, dias por mês, ano bissexto | Não (sem chamadores) |
| `validateMinLength(value: string, min: number, fieldName = 'Campo')` | tamanho mínimo | Não (sem chamadores) |
| `validateMaxLength(value: string, max: number, fieldName = 'Campo')` | tamanho máximo | Não (sem chamadores) |

```typescript
const error = validateCPF('123.456.789-09');
if (error) console.log(error);

const erroNome = validateRequired(nome, 'Nome');
```

A tela `Configuracoes/EmpresaPage.tsx` também usa Zod (`empresaSchema.ts`, via `zodResolver` do react-hook-form) além do `MaskedInput`.

---

## 🎨 Componente MaskedInput

Arquivo: `frontend/src/components/common/MaskedInput/MaskedInput.tsx` (export default; não está no `components/common/index.ts`).

### Uso Básico

```typescript
import { useState } from 'react';
import MaskedInput from '@/components/common/MaskedInput/MaskedInput';
import { validateCPF } from '@/utils/validators';

const [cpf, setCpf] = useState('');

<MaskedInput
  mask="cpf"
  value={cpf}
  onChange={setCpf}
  onValidate={validateCPF}
  label="CPF"
  placeholder="000.000.000-00"
  showValidation={true}
  required
/>
```

### Máscaras Disponíveis no Componente

- `cpf` - CPF brasileiro
- `cnpj` - CNPJ brasileiro
- `phone` - Telefone brasileiro (formato de celular `(00) 00000-0000`)
- `cep` - CEP brasileiro
- `date` - Data DD/MM/AAAA
- `creditCard` - Cartão de crédito

O tipo aceita também `currency`, mas `applyMask` não tem `case` para ele: o valor passa sem formatação.

Em uso hoje: `cpf`, `cnpj`, `phone` e `cep` (em `EmpresaPage.tsx`, `PlataformaPage.tsx` e `CheckoutPage.tsx`).

### Props do MaskedInput

```typescript
type MaskType = 'cpf' | 'cnpj' | 'phone' | 'cep' | 'date' | 'creditCard' | 'currency';

interface MaskedInputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'onChange'> {
  mask?: MaskType;
  value: string;
  onChange: (value: string) => void; // recebe o valor JÁ mascarado
  onValidate?: (value: string) => string | null;
  label?: string;
  error?: string;        // erro externo (do formulário); tem prioridade sobre o interno
  helperText?: string;   // mostrado quando não há erro
  showValidation?: boolean; // default false
}
```

Comportamento:

- `onChange` recebe o valor mascarado; use `unmask()` no envio quando o backend exigir só dígitos.
- `onValidate` roda sempre no blur; com `showValidation`, roda também a cada digitação depois do primeiro blur.
- As demais props de `<input>` (`required`, `disabled`, `placeholder`, `name` etc.) são repassadas. O `type` é sempre forçado para `"text"`: passar `type="email"` não tem efeito.

### Exemplo Completo

```typescript
import { useState } from 'react';
import MaskedInput from '@/components/common/MaskedInput/MaskedInput';
import { validateCPF, validatePhone, validateEmail } from '@/utils/validators';
import { unmask } from '@/utils/masks';
import { Toast } from '@/utils/toast';
import { api } from '@/services/api/axios';

const MeuFormulario = () => {
  const [cpf, setCpf] = useState('');
  const [telefone, setTelefone] = useState('');
  const [email, setEmail] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const cpfError = validateCPF(cpf);
    const telefoneError = validatePhone(telefone);
    const emailError = validateEmail(email);

    if (cpfError || telefoneError || emailError) {
      Toast.error('Corrija os erros no formulário');
      return;
    }

    try {
      const payload = {
        cpf: unmask(cpf),           // '12345678909'
        telefone: unmask(telefone), // '11987654321' (o serviço de clientes converte para E.164)
        email,
      };

      await api.post('/clientes', payload);
      Toast.success('Cliente cadastrado com sucesso!');
    } catch (error) {
      Toast.apiError(error);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <MaskedInput
        mask="cpf"
        value={cpf}
        onChange={setCpf}
        onValidate={validateCPF}
        label="CPF"
        placeholder="000.000.000-00"
        showValidation={true}
        required
      />

      <MaskedInput
        mask="phone"
        value={telefone}
        onChange={setTelefone}
        onValidate={validatePhone}
        label="Telefone"
        placeholder="(00) 00000-0000"
        showValidation={true}
        required
      />

      <MaskedInput
        value={email}
        onChange={setEmail}
        onValidate={validateEmail}
        label="Email"
        placeholder="usuario@exemplo.com"
        showValidation={true}
        required
      />

      <button type="submit">Cadastrar</button>
    </form>
  );
};
```

O payload acima é ilustrativo: `ClienteCreate` exige também `nome` e `empresa_id`. No código real, a criação passa por `clientesApi` (`frontend/src/services/api/clientesApi.ts`, `api.post('/clientes', data)`).

---

## 🔔 Sistema de Notificações (Toast)

Arquivo: `frontend/src/utils/toast.ts`. O `ToastContainer` é montado em `frontend/src/main.tsx`.

### Importar

```typescript
import { Toast } from '@/utils/toast';
```

### Uso Básico

```typescript
Toast.success('Operação realizada com sucesso!'); // autoClose 4000 ms
Toast.error('Erro ao processar solicitação');     // autoClose 5000 ms
Toast.warning('Atenção: estoque baixo');
Toast.info('Processando pagamento...');
```

### Erros da API

```typescript
try {
  await api.post('/endpoint', data);
  Toast.success('Sucesso!');
} catch (error) {
  Toast.apiError(error);
}
```

`Toast.apiError` lê `error.response.data.detail`: se for array (erro 422 do Pydantic), mostra um toast por item no formato `campo: mensagem`; se for string, mostra a string; caso contrário, uma mensagem genérica. Sem `detail`, usa `error.message`.

### Loading com Atualização

```typescript
const handleSave = async () => {
  const toastId = Toast.loading('Salvando...');

  try {
    await api.post('/endpoint', data);
    Toast.update(toastId, 'success', 'Salvo com sucesso!');
  } catch (error) {
    Toast.update(toastId, 'error', 'Erro ao salvar');
  }
};
```

`Toast.dismiss(toastId?)` fecha um toast específico ou todos.

### Opções Avançadas

`success`, `error`, `warning` e `info` aceitam `ToastOptions` do react-toastify como segundo argumento:

```typescript
Toast.success('Mensagem', {
  autoClose: 5000,
  position: 'bottom-right',
  onClose: () => console.log('Toast fechado'),
});
```

---

## 📝 Padrões de Envio ao Backend

### Clientes e checkout da loja (vendas): sem máscara

```typescript
import { unmask } from '@/utils/masks';

const payload = {
  cpf: unmask('123.456.789-09'),       // '12345678909' (o backend também aceitaria com máscara)
  telefone: unmask('(11) 98765-4321'), // '11987654321'
  cep: unmask('01310-100'),            // '01310100' (obrigatório: com máscara é rejeitado)
};
```

### Empresas: com máscara

```typescript
const payload = {
  cnpj: '12.345.678/0001-95', // formato XX.XXX.XXX/XXXX-XX obrigatório
  cep: '01310-100',           // formato XXXXX-XXX obrigatório
};
```

---

## 🎯 Fluxo (clientes / checkout)

```
┌─────────────────┐
│   Usuário       │
│   digita        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  MaskedInput    │
│  aplica máscara │
│  valida no blur │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   onSubmit      │
│  remove máscara │
│  com unmask()   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Backend      │
│  Pydantic       │
│  normaliza e    │
│  valida         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Banco de Dados │
│  CPF/CEP sem    │
│  máscara        │
└─────────────────┘
```

No serviço de empresas o fluxo é diferente: CNPJ e CEP seguem mascarados até o banco.

---

## 🔧 Migração de Código Existente

### Substituir alerts

```typescript
// ❌ Antes
alert('Erro ao salvar!');

// ✅ Depois
Toast.error('Erro ao salvar!');
```

### Adicionar máscara a input existente

```typescript
// ❌ Antes
<input
  type="text"
  value={cpf}
  onChange={(e) => setCpf(e.target.value)}
/>

// ✅ Depois
<MaskedInput
  mask="cpf"
  value={cpf}
  onChange={setCpf}
  onValidate={validateCPF}
  showValidation={true}
/>
```

### Validar antes de enviar

```typescript
// ❌ Antes
const handleSubmit = async () => {
  await api.post('/clientes', { cpf });
};

// ✅ Depois
const handleSubmit = async () => {
  const error = validateCPF(cpf);
  if (error) {
    Toast.error(error);
    return;
  }

  await api.post('/clientes', {
    cpf: unmask(cpf)
  });
};
```

---

## 📚 Referências

- Máscaras: `frontend/src/utils/masks.ts`
- Validadores: `frontend/src/utils/validators.ts`
- Toast: `frontend/src/utils/toast.ts`
- MaskedInput: `frontend/src/components/common/MaskedInput/`
- Backend clientes (CPF, telefone): `services/clientes/utils/validators.py`, `services/clientes/schemas/cliente.py`
- Backend empresas (CNPJ, CEP): `services/empresas/utils/validators.py`, `services/empresas/schemas/empresa.py`
- Backend vendas (checkout): `services/vendas/schemas/loja.py`, `services/vendas/services/cliente_validacao_service.py`

---

## ✨ Melhorias Futuras

- [ ] Fazer o `MaskedInput` usar as funções de `masks.ts` (hoje há duas cópias da mesma formatação) ou remover os exports mortos
- [ ] Implementar `currency` no `MaskedInput` ou tirá-lo do `MaskType`
- [ ] Padronizar o formato de CEP entre os serviços (empresas guarda com máscara; clientes e vendas, sem)
- [ ] Validação assíncrona (ex: verificar CPF duplicado)
- [ ] Feedback visual de força de senha

Autocompletar endereço por CEP já existe: `ClienteFormPage.tsx`, `ClienteEnderecosPage.tsx`, `EmpresaPage.tsx` e `CheckoutPage.tsx` consultam o ViaCEP.
