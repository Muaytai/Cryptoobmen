"use client";

import React, { JSX } from "react";
import styles from "./details.module.css";
import { Button } from "@/components/ui/Button";
import { Card, CardContent } from "@/components/ui/card";
import { clsx } from "clsx";

const wallets = [
  {
    id: 1,
    system: "USDT (TRC20)",
    name: "USDT (TRC20)",
    address: "TOkZnS4EUpxz1A9FjEtGbZqLTxYm5FdqVu",
    date: "24.05.2025",
    status: "✓ Подтверждён",
    comment: ""
  },
  {
    id: 2,
    system: "USDT (TRC20)",
    name: "Новый кошелёк 1",
    address: "TDm3zvPjX7Aef5X0YdELskBwHXgPRthP",
    date: "18.03.2025",
    status: "✓ Подтверждён",
    comment: ""
  },
  {
    id: 3,
    system: "USDT (TRC20)",
    name: "Новый кошелёк 2",
    address: "TXJ9aTvmKzLXq1Gb3WpjYTYEqP3e62uNp4",
    date: "09.01.2025",
    status: "✓ Подтверждён",
    comment: ""
  },
  {
    id: 4,
    system: "USDT (TRC20)",
    name: "Кошелёк 3",
    address: "TAylMZm8qQg8f0OWnRtHZDsspw4CVjLUE",
    date: "22.12.2024",
    status: "✓ Подтверждён",
    comment: ""
  }
];

export const Details = (): JSX.Element => {
  return (
    <section className={styles.container}>
      <h2 className="text-violet-600 text-3xl font-normal mb-8 [font-family:'Manrope',Helvetica]">
        Реквизиты
      </h2>

      <div className={styles.content}>
        <Card className="flex gap-4 w-full p-5 mb-[160px] text-subcard-text shadow-[0px_0px_20px_#0000004c] rounded-[15px] md:rounded-[25px] ">
          <CardContent className="w-full p-0 md:p-0">
            <div className="w-full max-w-full bg-card rounded-lg overflow-hidden">
              {/* Заголовки */}
              <div
                className="grid"
                style={{
                  gridTemplateColumns:
                    "minmax(80px, 0.8fr) minmax(80px, 0.8fr) minmax(160px, 1.5fr) minmax(50px, 0.6fr) minmax(80px, 0.8fr) minmax(100px, 1.2fr)",
                  width: "100%",
                }}
              >
                <div
                  className="px-4 py-3 bg-subcard text-left font-medium text-subcard-text text-base md:text-lg  tracking-wider border-b border-subcard">
                  Система
                </div>
                <div
                  className="px-4 py-3 bg-subcard text-left font-medium text-subcard-text text-base md:text-lg  tracking-wider border-b border-subcard">
                  Название
                </div>
                <div
                  className="px-4 py-3 bg-subcard text-left font-medium text-subcard-text text-base md:text-lg  tracking-wider border-b border-subcard">
                  Адрес реквизита
                </div>
                <div
                  className="px-4 py-3 bg-subcard text-left font-medium text-subcard-text text-base md:text-lg  tracking-wider border-b border-subcard">
                  Дата
                </div>
                <div
                  className="px-4 py-3 bg-subcard text-left font-medium text-subcard-text text-base md:text-lg  tracking-wider border-b border-subcard">
                  Статус
                </div>
                <div
                  className="px-4 py-3 bg-subcard text-left font-medium text-subcard-text text-base md:text-lg  tracking-wider border-b border-subcard">
                  Комментарий
                </div>
              </div>

              {/* Строки данных */}
              <div className="w-full">
                {wallets.map((item) => (
                  <div
                    key={item.id}
                    className="grid hover:bg-card-hover/50 transition-colors"
                    style={{
                      gridTemplateColumns:
                        "minmax(80px, 0.8fr) minmax(80px, 0.8fr) minmax(160px, 1.5fr) minmax(50px, 0.6fr) minmax(80px, 0.8fr) minmax(100px, 1.2fr)",
                      width: "100%",
                    }}
                  >
                    <div className="px-4 py-4 text-sm text-subcard-text/70 ">
                      {item.system}
                    </div>
                    <div className="px-4 py-4 text-sm text-subcard-text/70 ">
                      {item.name}
                    </div>
                    <div className="px-4 py-4 text-sm text-subcard-text/70 truncate">
                      <span>
                        {item.address}
                      </span>
                    </div>
                    <div className="px-4 py-4 text-sm text-subcard-text/70">
                      {item.date}
                    </div>
                    <div className="px-4 py-4 text-sm text-subcard-text/70">
                      <span>
                        {item.status}
                      </span>
                    </div>
                    <div className="px-4 py-4 text-sm text-subcard-text/70">
                      <span>
                        {item.comment}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </section>
  );
};
