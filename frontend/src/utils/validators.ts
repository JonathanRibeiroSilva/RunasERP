/**
 * Validadores para formulários
 * Retornam string de erro ou null se válido
 */

/**
 * Valida CPF usando algoritmo dos dígitos verificadores
 */
export const validateCPF = (cpf: string): string | null => {
  // Remove formatação
  const cleaned = cpf.replace(/\D/g, '');
  
  // Verifica tamanho
  if (cleaned.length !== 11) {
    return 'CPF deve ter 11 dígitos';
  }
  
  // Verifica se não é sequência repetida
  if (/^(\d)\1{10}$/.test(cleaned)) {
    return 'CPF inválido';
  }
  
  // Valida primeiro dígito verificador
  let sum = 0;
  for (let i = 0; i < 9; i++) {
    sum += parseInt(cleaned.charAt(i)) * (10 - i);
  }
  let digit = 11 - (sum % 11);
  if (digit >= 10) digit = 0;
  
  if (digit !== parseInt(cleaned.charAt(9))) {
    return 'CPF inválido';
  }
  
  // Valida segundo dígito verificador
  sum = 0;
  for (let i = 0; i < 10; i++) {
    sum += parseInt(cleaned.charAt(i)) * (11 - i);
  }
  digit = 11 - (sum % 11);
  if (digit >= 10) digit = 0;
  
  if (digit !== parseInt(cleaned.charAt(10))) {
    return 'CPF inválido';
  }
  
  return null;
};

/**
 * Valida CNPJ usando algoritmo dos dígitos verificadores
 */
export const validateCNPJ = (cnpj: string): string | null => {
  const cleaned = cnpj.replace(/\D/g, '');
  
  if (cleaned.length !== 14) {
    return 'CNPJ deve ter 14 dígitos';
  }
  
  if (/^(\d)\1{13}$/.test(cleaned)) {
    return 'CNPJ inválido';
  }
  
  // Validação dos dígitos verificadores
  let tamanho = cleaned.length - 2;
  let numeros = cleaned.substring(0, tamanho);
  const digitos = cleaned.substring(tamanho);
  let soma = 0;
  let pos = tamanho - 7;
  
  for (let i = tamanho; i >= 1; i--) {
    soma += parseInt(numeros.charAt(tamanho - i)) * pos--;
    if (pos < 2) pos = 9;
  }
  
  let resultado = soma % 11 < 2 ? 0 : 11 - (soma % 11);
  if (resultado !== parseInt(digitos.charAt(0))) {
    return 'CNPJ inválido';
  }
  
  tamanho = tamanho + 1;
  numeros = cleaned.substring(0, tamanho);
  soma = 0;
  pos = tamanho - 7;
  
  for (let i = tamanho; i >= 1; i--) {
    soma += parseInt(numeros.charAt(tamanho - i)) * pos--;
    if (pos < 2) pos = 9;
  }
  
  resultado = soma % 11 < 2 ? 0 : 11 - (soma % 11);
  if (resultado !== parseInt(digitos.charAt(1))) {
    return 'CNPJ inválido';
  }
  
  return null;
};

/**
 * Valida email
 */
export const validateEmail = (email: string): string | null => {
  const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  
  if (!email) {
    return 'Email é obrigatório';
  }
  
  if (!regex.test(email)) {
    return 'Email inválido';
  }
  
  return null;
};

/**
 * Valida telefone brasileiro
 */
export const validatePhone = (phone: string): string | null => {
  const cleaned = phone.replace(/\D/g, '');
  
  // Deve ter 10 (fixo) ou 11 (celular) dígitos
  if (cleaned.length < 10 || cleaned.length > 11) {
    return 'Telefone deve ter 10 ou 11 dígitos';
  }
  
  // DDD não pode começar com 0
  if (cleaned.charAt(0) === '0') {
    return 'DDD inválido';
  }
  
  return null;
};

/**
 * Valida CEP
 */
export const validateCEP = (cep: string): string | null => {
  const cleaned = cep.replace(/\D/g, '');
  
  if (cleaned.length !== 8) {
    return 'CEP deve ter 8 dígitos';
  }
  
  return null;
};

/**
 * Valida senha forte
 */
export const validatePassword = (password: string): string | null => {
  if (!password) {
    return 'Senha é obrigatória';
  }
  
  if (password.length < 8) {
    return 'Senha deve ter no mínimo 8 caracteres';
  }
  
  if (!/[A-Z]/.test(password)) {
    return 'Senha deve ter pelo menos uma letra maiúscula';
  }
  
  if (!/[a-z]/.test(password)) {
    return 'Senha deve ter pelo menos uma letra minúscula';
  }
  
  if (!/[0-9]/.test(password)) {
    return 'Senha deve ter pelo menos um número';
  }
  
  if (!/[!@#$%^&*]/.test(password)) {
    return 'Senha deve ter pelo menos um caractere especial (!@#$%^&*)';
  }
  
  return null;
};

/**
 * Valida data no formato DD/MM/AAAA
 */
export const validateDate = (date: string): string | null => {
  const cleaned = date.replace(/\D/g, '');
  
  if (cleaned.length !== 8) {
    return 'Data inválida';
  }
  
  const day = parseInt(cleaned.substring(0, 2));
  const month = parseInt(cleaned.substring(2, 4));
  const year = parseInt(cleaned.substring(4, 8));
  
  if (month < 1 || month > 12) {
    return 'Mês inválido';
  }
  
  if (day < 1 || day > 31) {
    return 'Dia inválido';
  }
  
  // Validação de dias por mês
  const daysInMonth = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  
  // Ano bissexto
  if (year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0)) {
    daysInMonth[1] = 29;
  }
  
  if (day > daysInMonth[month - 1]) {
    return 'Dia inválido para este mês';
  }
  
  return null;
};

/**
 * Valida campo obrigatório
 */
export const validateRequired = (value: any, fieldName: string = 'Campo'): string | null => {
  if (!value || (typeof value === 'string' && value.trim() === '')) {
    return `${fieldName} é obrigatório`;
  }
  return null;
};

/**
 * Valida tamanho mínimo
 */
export const validateMinLength = (value: string, min: number, fieldName: string = 'Campo'): string | null => {
  if (value.length < min) {
    return `${fieldName} deve ter no mínimo ${min} caracteres`;
  }
  return null;
};

/**
 * Valida tamanho máximo
 */
export const validateMaxLength = (value: string, max: number, fieldName: string = 'Campo'): string | null => {
  if (value.length > max) {
    return `${fieldName} deve ter no máximo ${max} caracteres`;
  }
  return null;
};
