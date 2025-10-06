import React, { InputHTMLAttributes } from 'react';

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: boolean;
  errorMessage?: string;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, errorMessage, type = 'text', ...props }, ref) => {
    const inputStyles = {
      display: 'flex',
      width: '100%',
      height: '48px',
      padding: '8px 12px',
      fontSize: '14px',
      border: `1px solid ${error ? '#ef4444' : 'rgba(255, 255, 255, 0.1)'}`,
      borderRadius: '8px',
      backgroundColor: 'rgba(255, 255, 255, 0.05)',
      color: '#fff',
      transition: 'all 0.2s ease',
      outline: 'none',
    };

    const labelStyles = {
      display: 'block',
      marginBottom: '8px',
      fontSize: '14px',
      color: 'rgba(255, 255, 255, 0.7)',
    };

    const errorStyles = {
      marginTop: '4px',
      fontSize: '12px',
      color: '#ef4444',
    };

    return (
      <div style={{ marginBottom: '16px' }}>
        {label && (
          <label style={labelStyles}>
            {label}
          </label>
        )}
        <input
          type={type}
          style={inputStyles}
          ref={ref}
          {...props}
        />
        {error && errorMessage && (
          <p style={errorStyles}>
            {errorMessage}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input'; 