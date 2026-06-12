import { Container } from 'react-bootstrap';
import './ResponsiveContainer.scss';

interface ResponsiveContainerProps {
  children: React.ReactNode;
  fluid?: boolean;
  className?: string;
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | 'xxl' | 'full';
}

/**
 * Container responsivo que adapta padding e largura máxima
 * baseado no tamanho da tela.
 * 
 * @param children - Conteúdo do container
 * @param fluid - Se true, ocupa 100% da largura
 * @param className - Classes CSS adicionais
 * @param maxWidth - Largura máxima do container
 */
export const ResponsiveContainer: React.FC<ResponsiveContainerProps> = ({
  children,
  fluid = false,
  className = '',
  maxWidth = 'xl',
}) => {
  const maxWidthClass = maxWidth !== 'full' ? `max-width-${maxWidth}` : '';

  return (
    <Container 
      fluid={fluid} 
      className={`responsive-container ${maxWidthClass} ${className}`}
    >
      {children}
    </Container>
  );
};

export default ResponsiveContainer;
