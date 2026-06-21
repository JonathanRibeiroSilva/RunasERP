/**
 * Máscaras para inputs
 * Aplicam formatação visual enquanto o usuário digita
 */

/**
 * Aplica máscara de CPF: 000.000.000-00
 */
export const maskCPF = (value: string): string => {
  const cleaned = value.replace(/\D/g, '');
  const match = cleaned.match(/^(\d{0,3})(\d{0,3})(\d{0,3})(\d{0,2})$/);
  
  if (!match) return value;
  
  let formatted = '';
  if (match[1]) formatted += match[1];
  if (match[2]) formatted += '.' + match[2];
  if (match[3]) formatted += '.' + match[3];
  if (match[4]) formatted += '-' + match[4];
  
  return formatted;
};

/**
 * Aplica máscara de CNPJ: 00.000.000/0000-00
 */
export const maskCNPJ = (value: string): string => {
  const cleaned = value.replace(/\D/g, '');
  const match = cleaned.match(/^(\d{0,2})(\d{0,3})(\d{0,3})(\d{0,4})(\d{0,2})$/);
  
  if (!match) return value;
  
  let formatted = '';
  if (match[1]) formatted += match[1];
  if (match[2]) formatted += '.' + match[2];
  if (match[3]) formatted += '.' + match[3];
  if (match[4]) formatted += '/' + match[4];
  if (match[5]) formatted += '-' + match[5];
  
  return formatted;
};

/**
 * Aplica máscara de telefone: (00) 00000-0000 ou (00) 0000-0000
 */
export const maskPhone = (value: string): string => {
  const cleaned = value.replace(/\D/g, '');
  
  // Celular: (00) 00000-0000
  if (cleaned.length <= 11) {
    const match = cleaned.match(/^(\d{0,2})(\d{0,5})(\d{0,4})$/);
    if (!match) return value;
    
    let formatted = '';
    if (match[1]) formatted += '(' + match[1];
    if (match[2]) formatted += ') ' + match[2];
    if (match[3]) formatted += '-' + match[3];
    
    return formatted;
  }
  
  return value;
};

/**
 * Aplica máscara de CEP: 00000-000
 */
export const maskCEP = (value: string): string => {
  const cleaned = value.replace(/\D/g, '');
  const match = cleaned.match(/^(\d{0,5})(\d{0,3})$/);
  
  if (!match) return value;
  
  let formatted = '';
  if (match[1]) formatted += match[1];
  if (match[2]) formatted += '-' + match[2];
  
  return formatted;
};

/**
 * Aplica máscara de moeda: R$ 0.000,00
 */
export const maskCurrency = (value: string | number): string => {
  const numValue = typeof value === 'string' ? parseFloat(value.replace(/\D/g, '')) / 100 : value;
  
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(numValue);
};

/**
 * Aplica máscara de data: DD/MM/AAAA
 */
export const maskDate = (value: string): string => {
  const cleaned = value.replace(/\D/g, '');
  const match = cleaned.match(/^(\d{0,2})(\d{0,2})(\d{0,4})$/);
  
  if (!match) return value;
  
  let formatted = '';
  if (match[1]) formatted += match[1];
  if (match[2]) formatted += '/' + match[2];
  if (match[3]) formatted += '/' + match[3];
  
  return formatted;
};

/**
 * Aplica máscara de cartão de crédito: 0000 0000 0000 0000
 */
export const maskCreditCard = (value: string): string => {
  const cleaned = value.replace(/\D/g, '');
  const match = cleaned.match(/^(\d{0,4})(\d{0,4})(\d{0,4})(\d{0,4})$/);
  
  if (!match) return value;
  
  let formatted = '';
  if (match[1]) formatted += match[1];
  if (match[2]) formatted += ' ' + match[2];
  if (match[3]) formatted += ' ' + match[3];
  if (match[4]) formatted += ' ' + match[4];
  
  return formatted;
};

/**
 * Remove toda formatação, deixando apenas números
 */
export const unmask = (value: string): string => {
  return value.replace(/\D/g, '');
};

/**
 * Remove formatação de moeda e retorna número
 */
export const unmaskCurrency = (value: string): number => {
  const cleaned = value.replace(/[^\d,]/g, '').replace(',', '.');
  return parseFloat(cleaned) || 0;
};
