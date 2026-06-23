# Guia: Máscaras e Validações

## 📚 Arquitetura Implementada

### Backend
- ✅ Aceita dados **com ou sem máscara**
- ✅ Normaliza automaticamente (remove formatação)
- ✅ Armazena **sem máscara** no banco de dados
- ✅ Valida CPF com dígitos verificadores

### Frontend
- ✅ Aplica máscaras visuais nos inputs
- ✅ Valida em tempo real
- ✅ Remove máscaras antes de enviar ao backend
- ✅ Notificações elegantes com Toast (sem alerts)

---

## 🎭 Usando Máscaras

### Importar Funções

```typescript
import { maskCPF, maskCNPJ, maskPhone, maskCEP, maskDate, unmask } from '@/utils/masks';
```

### Máscaras Disponíveis

| Máscara | Formato | Função |
|---------|---------|--------|
| CPF | 000.000.000-00 | `maskCPF(value)` |
| CNPJ | 00.000.000/0000-00 | `maskCNPJ(value)` |
| Telefone | (00) 00000-0000 | `maskPhone(value)` |
| CEP | 00000-000 | `maskCEP(value)` |
| Data | DD/MM/AAAA | `maskDate(value)` |
| Cartão | 0000 0000 0000 0000 | `maskCreditCard(value)` |
| Moeda | R$ 0.000,00 | `maskCurrency(value)` |

### Remover Máscaras

```typescript
import { unmask } from '@/utils/masks';

const cpfFormatado = '123.456.789-09';
const cpfLimpo = unmask(cpfFormatado); // '12345678909'
```

---

## ✅ Validações

### Importar Validadores

```typescript
import { validateCPF, validateEmail, validatePhone, validatePassword } from '@/utils/validators';
```

### Validadores Disponíveis

```typescript
// CPF (com dígitos verificadores)
const error = validateCPF('123.456.789-09');
if (error) console.log(error); // null se válido, string de erro se inválido

// CNPJ (com dígitos verificadores)
const error = validateCNPJ('00.000.000/0000-00');

// Email
const error = validateEmail('usuario@example.com');

// Telefone
const error = validatePhone('(11) 98765-4321');

// CEP
const error = validateCEP('01310-100');

// Senha Forte
const error = validatePassword('SenhaForte@123');
// Regras: mínimo 8 caracteres, 1 maiúscula, 1 minúscula, 1 número, 1 especial

// Data
const error = validateDate('31/12/2023');

// Campo obrigatório
const error = validateRequired(value, 'Nome');

// Tamanho mínimo/máximo
const error = validateMinLength(value, 3, 'Nome');
const error = validateMaxLength(value, 100, 'Nome');
```

---

## 🎨 Componente MaskedInput

### Uso Básico

```typescript
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
- `phone` - Telefone brasileiro
- `cep` - CEP brasileiro
- `date` - Data DD/MM/AAAA
- `creditCard` - Cartão de crédito

### Props do MaskedInput

```typescript
interface MaskedInputProps {
  mask?: 'cpf' | 'cnpj' | 'phone' | 'cep' | 'date' | 'creditCard';
  value: string;
  onChange: (value: string) => void;
  onValidate?: (value: string) => string | null;
  label?: string;
  error?: string; // Erro externo (do formulário)
  helperText?: string; // Texto de ajuda
  showValidation?: boolean; // Valida em tempo real
  required?: boolean;
  disabled?: boolean;
  placeholder?: string;
}
```

### Exemplo Completo

```typescript
import { useState } from 'react';
import MaskedInput from '@/components/common/MaskedInput/MaskedInput';
import { validateCPF, validatePhone, validateEmail } from '@/utils/validators';
import { unmask } from '@/utils/masks';
import { Toast } from '@/utils/toast';

const MeuFormulario = () => {
  const [cpf, setCpf] = useState('');
  const [telefone, setTelefone] = useState('');
  const [email, setEmail] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validar todos os campos
    const cpfError = validateCPF(cpf);
    const telefoneError = validatePhone(telefone);
    const emailError = validateEmail(email);

    if (cpfError || telefoneError || emailError) {
      Toast.error('Corrija os erros no formulário');
      return;
    }

    try {
      // Remover máscaras antes de enviar
      const payload = {
        cpf: unmask(cpf), // '12345678909'
        telefone: unmask(telefone), // '11987654321'
        email, // Email não tem máscara
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
        type="email"
        placeholder="usuario@exemplo.com"
        showValidation={true}
        required
      />

      <button type="submit">Cadastrar</button>
    </form>
  );
};
```

---

## 🔔 Sistema de Notificações (Toast)

### Importar

```typescript
import { Toast } from '@/utils/toast';
```

### Uso Básico

```typescript
// Sucesso
Toast.success('Operação realizada com sucesso!');

// Erro
Toast.error('Erro ao processar solicitação');

// Aviso
Toast.warning('Atenção: estoque baixo');

// Info
Toast.info('Processando pagamento...');
```

### Erros da API

```typescript
try {
  await api.post('/endpoint', data);
  Toast.success('Sucesso!');
} catch (error) {
  // Trata automaticamente erros 422, 400, 500, etc
  Toast.apiError(error);
}
```

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

### Opções Avançadas

```typescript
Toast.success('Mensagem', {
  autoClose: 5000, // 5 segundos
  position: 'bottom-right',
  onClose: () => console.log('Toast fechado'),
});
```

---

## 📝 Padrões de Envio ao Backend

### ❌ ERRADO

```typescript
// Não envie com máscara!
const payload = {
  cpf: '123.456.789-09', // ❌
  telefone: '(11) 98765-4321', // ❌
  cep: '01310-100', // ❌
};
```

### ✅ CORRETO

```typescript
import { unmask } from '@/utils/masks';

const payload = {
  cpf: unmask('123.456.789-09'), // ✅ '12345678909'
  telefone: unmask('(11) 98765-4321'), // ✅ '11987654321'
  cep: unmask('01310-100'), // ✅ '01310100'
};
```

---

## 🎯 Fluxo Completo

```
┌─────────────────┐
│   Usuário       │
│  digita com     │
│    máscara      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  MaskedInput    │
│  aplica máscara │
│  valida em      │
│  tempo real     │
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
│  aceita com ou  │
│  sem máscara    │
│  normaliza      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Banco de Dados │
│  armazena SEM   │
│    máscara      │
└─────────────────┘
```

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

- Máscaras: `/frontend/src/utils/masks.ts`
- Validadores: `/frontend/src/utils/validators.ts`
- Toast: `/frontend/src/utils/toast.ts`
- MaskedInput: `/frontend/src/components/common/MaskedInput/`
- Backend (normalização): `/services/clientes/utils/validators.py`

---

## ✨ Melhorias Futuras

- [ ] Máscaras customizáveis
- [ ] Validação assíncrona (ex: verificar CPF duplicado)
- [ ] Feedback visual de força de senha
- [ ] Autocompletar endereço por CEP
- [ ] Internacionalização de máscaras
