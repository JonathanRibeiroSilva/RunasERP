import ReactDOM from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { ToastContainer } from 'react-toastify';
import { AuthProvider } from '@/contexts/AuthContext';
import { env } from '@/config/env';
import ErrorBoundary from '@/components/common/ErrorBoundary/ErrorBoundary';
import App from './App';

// Styles
import 'bootstrap/dist/css/bootstrap.min.css';
import '@/styles/global.scss'; // Importar DEPOIS do Bootstrap para permitir sobrescrita
import 'react-toastify/dist/ReactToastify.css';

// Configurar React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes (antes era cacheTime)
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <QueryClientProvider client={queryClient}>
    <AuthProvider>
      <ErrorBoundary>
        <App />
      </ErrorBoundary>
      <ToastContainer
        position="top-right"
        autoClose={3000}
        hideProgressBar={false}
        newestOnTop
        closeOnClick
        rtl={false}
        pauseOnFocusLoss
        draggable
        pauseOnHover
        theme="dark"
      />
    </AuthProvider>
    {env.enableDevtools && <ReactQueryDevtools initialIsOpen={false} />}
  </QueryClientProvider>
);
