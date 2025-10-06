declare module 'react-hot-toast' {
  export function toast(message: string, options?: any): string;
  export function toast(options: any): string;
  
  export const Toaster: React.FC<{
    position?: 'top-left' | 'top-center' | 'top-right' | 'bottom-left' | 'bottom-center' | 'bottom-right';
    reverseOrder?: boolean;
    gutter?: number;
    containerClassName?: string;
    containerStyle?: React.CSSProperties;
    toastOptions?: {
      className?: string;
      style?: React.CSSProperties;
      duration?: number;
      success?: any;
      error?: any;
      loading?: any;
      custom?: any;
      [key: string]: any;
    };
    [key: string]: any;
  }>;

  export namespace toast {
    function success(message: string, options?: any): string;
    function error(message: string, options?: any): string;
    function loading(message: string, options?: any): string;
    function custom(message: React.ReactNode, options?: any): string;
    function dismiss(toastId?: string): void;
    function remove(toastId?: string): void;
  }
} 