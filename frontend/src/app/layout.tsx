import { Inter } from "next/font/google";
import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";
import { ThemeProvider } from "@/lib/ThemeProvider";
import HydrationFix from '@/components/layout/HydrationFix';
import "@/app/globals.css";

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

export const metadata = {
  title: "Cryptoobmen - Обмен криптовалют",
  description: "Надежная платформа для обмена криптовалют с лучшими курсами"
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ru" suppressHydrationWarning>
      <head>
        <style dangerouslySetInnerHTML={{ __html: hydrationFadeInStyle }} />
      </head>
      <body suppressHydrationWarning className={`${inter.className} antialiased`}>
        <ThemeProvider>
          <div className="flex flex-col min-h-screen hydration-container">
            <HydrationFix />
            <Header />
            <main className="flex-1 overflow-auto">
              {children}
            </main>
            <Footer />
          </div>
        </ThemeProvider>
      </body>
    </html>
  )
}
