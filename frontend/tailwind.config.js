/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: "#7C3AED", // фиолетовый
          hover: "#6D28D9",
        },
        secondary: {
          DEFAULT: "#A855F7", // светло-фиолетовый
          hover: "#9333EA",
        },
        accent: {
          DEFAULT: "#8B5CF6", //  индиго
          hover: "#7C3AED",
        },
        background: {
          DEFAULT: "#FFFFFF",
          dark: "#0A0A0A",
        },
        foreground: {
          DEFAULT: "#111827",
          dark: "#FFFFFF",
        },
        card: {
          DEFAULT: "hsl(var(--card) / <alpha-value>)",
          hover: "hsl(var(--subcard-bg) / <alpha-value>)",
          foreground: "#111827",
          dark: "#1A1A1A",
          "dark-foreground": "#FFFFFF",
        },
        subcard: {
          DEFAULT: "hsl(var(--subcard-bg) / <alpha-value>)",
          text: "hsl(var(--subcard-text) / <alpha-value>)", // Цвет текста
        },
        muted: {
          DEFAULT: "#F3F4F6",
          dark: "#374151",
        },
        destructive: {
          DEFAULT: "#DC2626",
          foreground: "#FFFFFF",
        },
        border: {
          DEFAULT: "#E5E7EB",
          dark: "#323238",
        },
        input: {
          DEFAULT: "#E5E7EB",
          dark: "#323238",
        },
      },
      borderRadius: {
        lg: "0.5rem",
        md: "0.375rem",
        sm: "0.25rem",
      },
      boxShadow: {
        'light': '0 0 20px rgba(0, 0, 0, 0.3)',
        'dark': 'none'
      },
    },
  },
  plugins: [],
} 