import type { Metadata } from "next";
import HomePageClient from "./HomePageClient";

export const metadata: Metadata = {
  title: "CTokenX — безопасный обмен и управление криптовалютой",
  description:
    "CTokenX — платформа для быстрого и безопасного обмена криптовалют, инвестиций и управления цифровыми активами. Выгодные курсы, поддержка 24/7 и строгая безопасность.",
  openGraph: {
    title: "CTokenX — платформа для обмена и инвестиций в криптовалюту",
    description:
      "Обменивайте и управляйте криптоактивами на CTokenX: выгодные курсы, удобный интерфейс и защита средств.",
    url: "https://cryptoobmen.com/",
    siteName: "CTokenX",
    type: "website",
  },
};

export default function HomePage() {
  return <HomePageClient />;
}


