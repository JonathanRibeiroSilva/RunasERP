import { Card } from 'react-bootstrap';
import './ResponsiveCard.scss';

interface ResponsiveCardProps {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  className?: string;
  hoverable?: boolean;
  clickable?: boolean;
  onClick?: () => void;
  headerActions?: React.ReactNode;
  footer?: React.ReactNode;
}

/**
 * Card responsivo com estilos consistentes para o design system.
 * 
 * @param children - Conteúdo principal do card
 * @param title - Título do card (header)
 * @param subtitle - Subtítulo do card (header)
 * @param className - Classes CSS adicionais
 * @param hoverable - Adiciona efeito hover
 * @param clickable - Torna o card clicável (adiciona cursor pointer)
 * @param onClick - Função executada ao clicar (se clickable)
 * @param headerActions - Ações no header (botões, etc)
 * @param footer - Conteúdo do footer
 */
export const ResponsiveCard: React.FC<ResponsiveCardProps> = ({
  children,
  title,
  subtitle,
  className = '',
  hoverable = false,
  clickable = false,
  onClick,
  headerActions,
  footer,
}) => {
  const cardClasses = [
    'responsive-card',
    hoverable && 'hoverable',
    clickable && 'clickable',
    className,
  ]
    .filter(Boolean)
    .join(' ');

  const handleClick = () => {
    if (clickable && onClick) {
      onClick();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (clickable && onClick && (e.key === 'Enter' || e.key === ' ')) {
      e.preventDefault();
      onClick();
    }
  };

  return (
    <Card
      className={cardClasses}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      tabIndex={clickable ? 0 : undefined}
      role={clickable ? 'button' : undefined}
    >
      {(title || subtitle || headerActions) && (
        <Card.Header className="card-header-custom">
          <div className="card-header-content">
            {(title || subtitle) && (
              <div className="card-header-text">
                {title && <Card.Title className="card-title-custom">{title}</Card.Title>}
                {subtitle && <Card.Subtitle className="card-subtitle-custom">{subtitle}</Card.Subtitle>}
              </div>
            )}
            {headerActions && <div className="card-header-actions">{headerActions}</div>}
          </div>
        </Card.Header>
      )}

      <Card.Body className="card-body-custom">{children}</Card.Body>

      {footer && <Card.Footer className="card-footer-custom">{footer}</Card.Footer>}
    </Card>
  );
};

export default ResponsiveCard;
