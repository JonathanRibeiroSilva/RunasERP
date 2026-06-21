import { useState, useEffect, InputHTMLAttributes } from 'react';
import './MaskedInput.scss';

type MaskType = 'cpf' | 'cnpj' | 'phone' | 'cep' | 'date' | 'creditCard' | 'currency';

interface MaskedInputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'onChange'> {
  mask?: MaskType;
  value: string;
  onChange: (value: string) => void;
  onValidate?: (value: string) => string | null;
  label?: string;
  error?: string;
  helperText?: string;
  showValidation?: boolean;
}

const MaskedInput: React.FC<MaskedInputProps> = ({
  mask,
  value,
  onChange,
  onValidate,
  label,
  error,
  helperText,
  showValidation = false,
  className = '',
  ...props
}) => {
  const [internalError, setInternalError] = useState<string | null>(null);
  const [touched, setTouched] = useState(false);

  // Aplica máscara baseado no tipo
  const applyMask = (rawValue: string): string => {
    if (!mask) return rawValue;

    const cleaned = rawValue.replace(/\D/g, '');

    switch (mask) {
      case 'cpf': {
        const match = cleaned.match(/^(\d{0,3})(\d{0,3})(\d{0,3})(\d{0,2})$/);
        if (!match) return rawValue;
        let formatted = '';
        if (match[1]) formatted += match[1];
        if (match[2]) formatted += '.' + match[2];
        if (match[3]) formatted += '.' + match[3];
        if (match[4]) formatted += '-' + match[4];
        return formatted;
      }

      case 'cnpj': {
        const match = cleaned.match(/^(\d{0,2})(\d{0,3})(\d{0,3})(\d{0,4})(\d{0,2})$/);
        if (!match) return rawValue;
        let formatted = '';
        if (match[1]) formatted += match[1];
        if (match[2]) formatted += '.' + match[2];
        if (match[3]) formatted += '.' + match[3];
        if (match[4]) formatted += '/' + match[4];
        if (match[5]) formatted += '-' + match[5];
        return formatted;
      }

      case 'phone': {
        const match = cleaned.match(/^(\d{0,2})(\d{0,5})(\d{0,4})$/);
        if (!match) return rawValue;
        let formatted = '';
        if (match[1]) formatted += '(' + match[1];
        if (match[2]) formatted += ') ' + match[2];
        if (match[3]) formatted += '-' + match[3];
        return formatted;
      }

      case 'cep': {
        const match = cleaned.match(/^(\d{0,5})(\d{0,3})$/);
        if (!match) return rawValue;
        let formatted = '';
        if (match[1]) formatted += match[1];
        if (match[2]) formatted += '-' + match[2];
        return formatted;
      }

      case 'date': {
        const match = cleaned.match(/^(\d{0,2})(\d{0,2})(\d{0,4})$/);
        if (!match) return rawValue;
        let formatted = '';
        if (match[1]) formatted += match[1];
        if (match[2]) formatted += '/' + match[2];
        if (match[3]) formatted += '/' + match[3];
        return formatted;
      }

      case 'creditCard': {
        const match = cleaned.match(/^(\d{0,4})(\d{0,4})(\d{0,4})(\d{0,4})$/);
        if (!match) return rawValue;
        let formatted = '';
        if (match[1]) formatted += match[1];
        if (match[2]) formatted += ' ' + match[2];
        if (match[3]) formatted += ' ' + match[3];
        if (match[4]) formatted += ' ' + match[4];
        return formatted;
      }

      default:
        return rawValue;
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    const masked = applyMask(newValue);
    onChange(masked);

    // Valida em tempo real se showValidation estiver ativo
    if (showValidation && onValidate && touched) {
      const validationError = onValidate(masked);
      setInternalError(validationError);
    }
  };

  const handleBlur = () => {
    setTouched(true);
    if (onValidate) {
      const validationError = onValidate(value);
      setInternalError(validationError);
    }
  };

  // Limpa erro interno quando error externo muda
  useEffect(() => {
    if (error) {
      setInternalError(null);
    }
  }, [error]);

  const displayError = error || internalError;
  const hasError = !!displayError;

  return (
    <div className={`masked-input ${className}`}>
      {label && (
        <label className="masked-input__label">
          {label}
          {props.required && <span className="required">*</span>}
        </label>
      )}
      <input
        {...props}
        type="text"
        value={value}
        onChange={handleChange}
        onBlur={handleBlur}
        className={`masked-input__field ${hasError ? 'error' : ''} ${props.disabled ? 'disabled' : ''}`}
      />
      {hasError && (
        <span className="masked-input__error">{displayError}</span>
      )}
      {!hasError && helperText && (
        <span className="masked-input__helper">{helperText}</span>
      )}
    </div>
  );
};

export default MaskedInput;
