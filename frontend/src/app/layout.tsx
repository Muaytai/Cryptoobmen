import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Header } from "@/components/layout/Header";
import "@/app/globals.css";
import { Footer } from "@/components/layout/Footer";
import { ThemeProvider } from "@/lib/ThemeProvider";

const inter = Inter({
  subsets: ["latin", "cyrillic"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "CryptoExchange - Обмен криптовалют",
  description: "Надежная платформа для обмена криптовалют с современным интерфейсом",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ru" suppressHydrationWarning>
      <body className={`${inter.className} antialiased`}>
        <ThemeProvider>
        <div className="flex flex-col min-h-screen">
          <Header />
          <main className="flex-1 overflow-auto pb-[50px]">
            {children}
          </main>
          <div id="footer-container">
            <Footer />
          </div>
        </div>
        </ThemeProvider>
      </body>
    </html>
  );
}
