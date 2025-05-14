import { Inter } from "next/font/google";
import { ThemeProvider } from "@/lib/ThemeProvider";
import React from "react";
import "@/app/globals.css";

const inter = Inter({
  subsets: ["latin", "cyrillic"],
  display: "swap"
});

export const metadata = {
  title: "Профиль - Cryptoobmen",
  description: "Личный кабинет пользователя Cryptoobmen"
};

// ВАЖНО: Этот layout полностью заменяет RootLayout
// и не наследует его компоненты
export default function ProfileLayout({children}: {
  children: React.ReactNode
}) {
  // Полностью независимый layout без Header и Footer
  return (
    <html lang="ru" suppressHydrationWarning className="dark">
      <head>
        <title>Профиль пользователя</title>
      </head>
      <body suppressHydrationWarning className={`${inter.className} antialiased bg-black text-white dark`}>
        <ThemeProvider>
          {/* Здесь нет компонентов Header и Footer */}
          <main className="min-h-screen">
            {children}
          </main>
        </ThemeProvider>
      </body>
    </html>
  );
} 