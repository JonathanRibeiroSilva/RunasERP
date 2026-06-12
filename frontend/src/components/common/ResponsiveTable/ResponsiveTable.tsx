import { Table } from 'react-bootstrap';
import './ResponsiveTable.scss';

interface ResponsiveTableProps {
  children: React.ReactNode;
  striped?: boolean;
  hover?: boolean;
  bordered?: boolean;
  borderless?: boolean;
  size?: 'sm' | 'lg';
  variant?: 'dark' | 'light';
  responsive?: boolean | 'sm' | 'md' | 'lg' | 'xl' | 'xxl';
  className?: string;
}

/**
 * Tabela responsiva com scroll horizontal automático em telas pequenas.
 * 
 * @param children - Conteúdo da tabela (thead, tbody, tfoot)
 * @param striped - Linhas zebradas
 * @param hover - Efeito hover nas linhas
 * @param bordered - Bordas em todas as células
 * @param borderless - Sem bordas
 * @param size - Tamanho da tabela (sm para compacta, lg para espaçosa)
 * @param variant - Tema dark ou light
 * @param responsive - Ativa scroll horizontal (true ou breakpoint específico)
 * @param className - Classes CSS adicionais
 */
export const ResponsiveTable: React.FC<ResponsiveTableProps> = ({
  children,
  striped = true,
  hover = true,
  bordered = false,
  borderless = false,
  size,
  variant = 'dark',
  responsive = true,
  className = '',
}) => {
  return (
    <div className="responsive-table-wrapper">
      <Table
        striped={striped}
        hover={hover}
        bordered={bordered}
        borderless={borderless}
        size={size}
        variant={variant}
        responsive={responsive}
        className={`responsive-table ${className}`}
      >
        {children}
      </Table>
    </div>
  );
};

export default ResponsiveTable;
