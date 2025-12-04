import type { Metadata, Viewport } from "next";
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