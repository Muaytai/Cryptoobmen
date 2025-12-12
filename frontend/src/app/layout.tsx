<<<<<<< HEAD
import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";
import { ThemeProvider } from "@/lib/ThemeProvider";
import HydrationFix from '@/components/layout/HydrationFix';
import "@/app/globals.css";
import { AuthProvider } from "@/components/AuthProvider";

const inter = Inter({
  subsets: ["latin", "cyrillic"],
  display: "swap"
});

// Отдельный экспорт для настроек вьюпорта (Next.js 14+)
export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 5,
  userScalable: true,
  // Если у вас был themeColor, его тоже лучше добавить сюда:
  // themeColor: 'black', 
};

export const metadata: Metadata = {
  title: "Cryptoobmen - Обмен криптовалют",
  description: "Надежная платформа для обмена криптовалют с лучшими курсами",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ru" suppressHydrationWarning className="dark">
      <body suppressHydrationWarning className={`${inter.className} antialiased bg-black text-white dark`}>
        <ThemeProvider>
          <AuthProvider>
            <div className="flex flex-col min-h-screen hydration-container">
              <HydrationFix />
              <Header />
              <main className="flex-1 overflow-auto">
                {children}
              </main>
              <Footer />
            </div>
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}
=======
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";
import { ThemeProvider } from "@/lib/ThemeProvider";
import HydrationFix from '@/components/layout/HydrationFix';
import "@/app/globals.css";
import { AuthProvider } from "@/components/AuthProvider";
import ReCaptchaProvider from "@/components/ui/ReCaptchaProvider";

const inter = Inter({
  subsets: ["latin", "cyrillic"],
  display: "swap"
});

// Стили для скрытия контента во время гидратации
const hydrationFadeInStyle = `
  @keyframes fade-in {
    from { opacity: 0; }
    to { opacity: 1; }
  }
  
  .hydration-container {
    animation: fade-in 0.3s ease-in;
  }
`;

// Критический CSS для предотвращения layout shift в Firefox
const criticalLayoutFix = `
  html { 
    overflow-y: scroll !important; 
    scrollbar-gutter: stable both-edges !important; 
    height: 100% !important;
    --header-h: 64px;
    contain: layout style !important;
    will-change: auto !important;
  }
  body { 
    height: 100vh !important; 
    min-height: 100vh !important; 
    overflow-y: auto !important;
    margin: 0 !important;
    padding: 0 !important;
    contain: layout style !important;
    will-change: auto !important;
    box-sizing: border-box !important;
  }
  * { 
    box-sizing: border-box !important; 
    contain: layout style !important;
  }
  img {
    contain: layout style !important;
    will-change: auto !important;
  }
  [data-fixed] {
    contain: layout style paint !important;
  }
  div, main, section, article, header, footer {
    contain: layout style !important;
    will-change: auto !important;
  }
`;

export const metadata: Metadata = {
  title: "Cryptoobmen - Обмен криптовалют",
  description: "Надежная платформа для обмена криптовалют с лучшими курсами"
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ru" suppressHydrationWarning className="dark">
      <head>
        <style dangerouslySetInnerHTML={{ __html: criticalLayoutFix }} />
        <style dangerouslySetInnerHTML={{ __html: hydrationFadeInStyle }} />
      </head>
      <body suppressHydrationWarning className={`${inter.className} antialiased bg-black text-white dark`}>
        <ThemeProvider>
          <AuthProvider>
            <ReCaptchaProvider>
              <div className="flex flex-col min-h-screen hydration-container">
                <HydrationFix />
                <Header />
                <main className="flex-1 overflow-auto">
                  {children}
                </main>
                <Footer />
              </div>
            </ReCaptchaProvider>
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}
>>>>>>> 15289855a991ed48da9be2cf9124ebfb7d590251
