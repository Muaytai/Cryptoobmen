import 'tailwindcss/tailwind.css'

// Это помогает TypeScript распознавать Tailwind CSS классы
declare module 'tailwindcss/tailwind.css' {
  export {}
}

// Для определения пользовательских классов
declare module 'react' {
  interface CSSProperties {
    '--tw-bg-opacity'?: string
    '--tw-text-opacity'?: string
    '--tw-border-opacity'?: string
  }
} 