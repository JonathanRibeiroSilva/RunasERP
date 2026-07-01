import axios from 'axios';

/**
 * Cliente HTTP público (storefront / loja online), sem autenticação de operador.
 * Cookies HTTP-only são enviados automaticamente via withCredentials.
 *
 * Fonte única — substitui as 11 cópias de `axios.create({ baseURL: '/api' })`
 * espalhadas pelas páginas da loja.
 */
export const apiPublica = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
});
