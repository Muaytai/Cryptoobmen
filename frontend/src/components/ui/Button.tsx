import React, { ButtonHTMLAttributes } from 'react';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline';
  size?: 'small' | 'medium' | 'large';
  fullWidth?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ 
    children, 
    variant = 'primary', 
    size = 'medium', 
    fullWidth = false,
    disabled,
    ...props 
  }, ref) => {
    const baseStyles = {
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center',
      fontWeight: 500,
      borderRadius: '8px',
      transition: 'all 0.2s ease',
      cursor: disabled ? 'not-allowed' : 'pointer',
      opacity: disabled ? 0.5 : 1,
      width: fullWidth ? '100%' : 'auto',
      border: 'none',
      outline: 'none',
    };

    const variants = {
      primary: {
        backgroundColor: '#8B5CF6',
        color: '#ffffff',
        ':hover': {
          backgroundColor: '#7C3AED',
        },
        ':active': {
          backgroundColor: '#6D28D9',
        },
      },
      secondary: {
        backgroundColor: 'rgba(255, 255, 255, 0.1)',
        color: '#ffffff',
        ':hover': {
          backgroundColor: 'rgba(255, 255, 255, 0.15)',
        },
        ':active': {
          backgroundColor: 'rgba(255, 255, 255, 0.2)',
        },
      },
      outline: {
        backgroundColor: 'transparent',
        color: '#8B5CF6',
        border: '1px solid #8B5CF6',
        ':hover': {
          backgroundColor: 'rgba(139, 92, 246, 0.1)',
        },
        ':active': {
          backgroundColor: 'rgba(139, 92, 246, 0.2)',
        },
      },
    };

    const sizes = {
      small: {
        height: '32px',
        padding: '0 12px',
        fontSize: '14px',
      },
      medium: {
        height: '40px',
        padding: '0 20px',
        fontSize: '14px',
      },
      large: {
        height: '48px',
        padding: '0 24px',
        fontSize: '16px',
      },
    };

    const style = {
      ...baseStyles,
      ...variants[variant],
      ...sizes[size],
    };

    return (
      <button
        ref={ref}
        type="button"
        disabled={disabled}
        style={style}
        {...props}
      >
        {children}
      </button>
    );
  }
);

Button.displayName = 'Button'; 