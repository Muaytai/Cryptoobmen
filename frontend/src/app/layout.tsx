import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Header } from "@/components/layout/Header";
import "./globals.css";
import { useEffect, useState } from "react";

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
    <html lang="ru">
      <body 
        suppressHydrationWarning
        className={`${inter.className} antialiased bg-white text-black dark:bg-gray-900 dark:text-white min-h-screen`}
      >
        <div className="flex flex-col min-h-screen">
          <Header />
          <main className="flex-1">
            {children}
          </main>
          <footer className="py-6 border-t border-gray-200 dark:border-gray-800">
            <div className="container mx-auto px-4">
              <div className="flex flex-col md:flex-row justify-between items-center">
                <div className="mb-4 md:mb-0">
                  <p suppressHydrationWarning className="text-sm text-gray-600 dark:text-gray-400">
                    &copy; {new Date().getFullYear()} CryptoExchange. Все права защищены.
                  </p>
                </div>
                <div className="flex space-x-6">
                  <a 
                    href="#" 
                    className="text-sm text-gray-600 hover:text-blue-600 dark:text-gray-400 dark:hover:text-white"
                  >
                    Условия использования
                  </a>
                  <a 
                    href="#" 
                    className="text-sm text-gray-600 hover:text-blue-600 dark:text-gray-400 dark:hover:text-white"
                  >
                    Политика конфиденциальности
                  </a>
                  <a 
                    href="#" 
                    className="text-sm text-gray-600 hover:text-blue-600 dark:text-gray-400 dark:hover:text-white"
                  >
                    Контакты
                  </a>
                </div>
              </div>
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
}
