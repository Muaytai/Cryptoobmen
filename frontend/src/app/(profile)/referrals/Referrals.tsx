"use client";

import React, {JSX, useState} from "react";
import styles from "./referalls.module.css";
import {Button} from "@/components/ui/Button";
import {Card, CardContent} from "@/components/ui/card";
import {clsx} from "clsx";
import {ReferralsModal} from "@/app/(profile)/components/modals/referralsModal/ReferralsModal";
import {Modal} from "@/app/(profile)/components/modals/Modal";

const referralsData = [
  {
    number: 5,
    registrationDate: "24.04.2025",
    referralCount: 0,
    email: "h********7@gmail.com",
    profit: "0.0",
  },
  {
    number: 4,
    registrationDate: "07.04.2025",
    referralCount: 0,
    email: "d**********r@mail.ru",
    profit: "0.0",
  },
  {
    number: 3,
    registrationDate: "15.03.2025",
    referralCount: 0,
    email: "z**********z@yandex.ru",
    profit: "1.25",
  },
  {
    number: 2,
    registrationDate: "09.02.2025",
    referralCount: 0,
    email: "k***********9@yandex.ru",
    profit: "0.0",
  },
  {
    number: 1,
    registrationDate: "22.01.2025",
    referralCount: 3,
    email: "t**********5@gmail.com",
    profit: "4.71",
  },
];

export const Referrals = (): JSX.Element => {
  const [modalOpen, setModalOpen] = useState(false);

  return (
    <>
      <section className={styles.container}>
        <h2 className="text-violet-600 text-3xl font-normal mb-8 [font-family:'Manrope',Helvetica]">
          Твоя реферальная программа
        </h2>

        <div
          className={clsx(
            styles.gridGroup,
            "flex gap-4 w-full bg-card p-5 text-subcard-text shadow-[0px_0px_20px_#0000004c] rounded-[15px] md:rounded-[25px] "
          )}
        >
          <Card
            className={clsx(styles.div1, "flex gap-1 w-full text-subcard-text ")}
          >
            <CardContent className="p-0 w-full flex gap-2 items-center justify-between">
              <h2 className="text-lg">Приглашай друзей и зарабатывай!</h2>
              <Button className="w-[160px] h-[36px] md:h-[48px] bg-violet-600 rounded-[15px] "
              onClick={() => setModalOpen(true)}>
              <span className="font-medium text-white text-sm md:text-lg text-center [font-family:'Manrope',Helvetica]">
                Подробнее
              </span>
              </Button>
            </CardContent>
          </Card>

          <Card
            className={clsx(styles.div2, "bg-subcard rounded-[15px] col-span-2")}
          >
            <CardContent className="p-3 md:p-5 h-[80px] md:h-[104px] relative">
            <span className="font-medium text-subcard-text/60 text-xs md:text-sm [font-family:'Manrope',Helvetica]">
              Реферальная ссылка
            </span>
              <div className="flex w-full items-center justify-between mt-4 ">
              <span className="font-medium text-subcard-text text-base md:text-lg [font-family:'Manrope',Helvetica] ">
                https://сrypto.com/referral/USERNAME
              </span>
                <img
                  className="w-[14px] h-[14px] md:w-[18px] md:h-[18px] ml-2"
                  alt="Copy"
                  src="/images/profile/vector-7_2.svg"
                />
              </div>
            </CardContent>
          </Card>

          <Card
            className={clsx(styles.div3, "bg-subcard rounded-[15px] col-span-2")}
          >
            <CardContent className="p-3 md:p-5 h-[80px] md:h-[104px] relative">
              <div className="flex w-full items-center justify-between ">
              <span className="font-medium text-subcard-text text-base md:text-lg [font-family:'Manrope',Helvetica] ">
                Количество приглашенных пользователей:
              </span>
              </div>
              <div
                className={clsx(
                  styles.users,
                  "font-medium text-subcard-text/60 text-xs md:text-sm [font-family:'Manrope',Helvetica]"
                )}
              >
                <div className="divUsers1">
                  <p>Сегодня:</p>
                  <p>0</p>
                </div>
                <div className="divUsers2">
                  <p>Неделя:</p>
                  <p>0</p>
                </div>
                <div className="divUsers3">
                  <p>Месяц:</p>
                  <p>0</p>
                </div>
                <div className="divUsers4">
                  <p>Всего:</p>
                  <p>0</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card
            className={clsx(styles.div4, "bg-subcard rounded-[15px] col-span-2")}
          >
            <CardContent className="p-3 md:p-5 h-[80px] md:h-[104px] relative">
              <div className="flex w-full items-center justify-between ">
              <span
                className="font-medium mb-8 text-subcard-text text-base md:text-lg [font-family:'Manrope',Helvetica] ">
                Доход
              </span>
              </div>
              <div className="flex w-full items-center justify-between ">
              <span className="font-medium text-subcard-text text-base md:text-lg [font-family:'Manrope',Helvetica] ">
                Токены
              </span>
              </div>
              <div
                className={clsx(
                  styles.users,
                  "font-medium text-subcard-text/60 text-xs md:text-sm [font-family:'Manrope',Helvetica]"
                )}
              >
                <div className="divUsers1">
                  <p>Сегодня:</p>
                  <p>0</p>
                </div>
                <div className="divUsers2">
                  <p>Неделя:</p>
                  <p>0</p>
                </div>
                <div className="divUsers3">
                  <p>Месяц:</p>
                  <p>0</p>
                </div>
                <div className="divUsers4">
                  <p>Всего:</p>
                  <p>0</p>
                </div>
              </div>

              <div className="flex w-full items-center justify-between ">
              <span
                className="font-medium mt-6 text-subcard-text text-base md:text-lg [font-family:'Manrope',Helvetica] ">
                USDT
              </span>
              </div>
              <div
                className={clsx(
                  styles.users,
                  "font-medium text-subcard-text/60 text-xs md:text-sm [font-family:'Manrope',Helvetica]"
                )}
              >
                <div className="divUsers1">
                  <p>Сегодня:</p>
                  <p>0</p>
                </div>
                <div className="divUsers2">
                  <p>Неделя:</p>
                  <p>0</p>
                </div>
                <div className="divUsers3">
                  <p>Месяц:</p>
                  <p>0</p>
                </div>
                <div className="divUsers4">
                  <p>Всего:</p>
                  <p>0</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card
            className={clsx(styles.div5, "bg-subcard rounded-[15px] col-span-2")}
          >
            <CardContent className="p-3 md:p-5 h-[80px] md:h-[104px] relative">
              <div className="flex w-full items-center justify-between ">
              <span className="font-medium text-subcard-text text-base md:text-lg [font-family:'Manrope',Helvetica] ">
                Процент дохода с рефералов
              </span>
              </div>
              <div className="flex w-full items-center justify-center mt-8">
                <p className="font-semibold text-subcard-text text-base md:text-3xl [font-family:'Manrope',Helvetica]">
                  50%
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        <h2 className="mt-[100px] text-violet-600 text-3xl font-normal mb-8 [font-family:'Manrope',Helvetica]">
          Таблица рефералов
        </h2>

        <div className={styles.content}>
          <Card
            className="flex gap-4 w-full p-5 mb-[160px] text-subcard-text shadow-[0px_0px_20px_#0000004c] rounded-[15px] md:rounded-[25px] ">
            <CardContent className="w-full p-0 md:p-0">
              <div className="w-full max-w-full bg-card rounded-lg overflow-hidden">
                {/* Заголовки */}
                <div
                  className="grid"
                  style={{
                    gridTemplateColumns:
                      "minmax(50px, 0.6fr) minmax(100px, 1.5fr) minmax(120px, 1.5fr) minmax(150px, 1.5fr) minmax(100px, 1.5fr)",
                    width: "100%",
                  }}
                >
                  <div
                    className="px-4 py-3 bg-subcard text-left font-medium text-subcard-text text-base md:text-lg  tracking-wider border-b border-subcard">
                    Номер
                  </div>
                  <div
                    className="px-4 py-3 bg-subcard text-left font-medium text-subcard-text text-base md:text-lg  tracking-wider border-b border-subcard">
                    Дата регистрации
                  </div>
                  <div
                    className="px-4 py-3 bg-subcard text-left font-medium text-subcard-text text-base md:text-lg  tracking-wider border-b border-subcard">
                    Количество рефералов
                  </div>
                  <div
                    className="px-4 py-3 bg-subcard text-left font-medium text-subcard-text text-base md:text-lg  tracking-wider border-b border-subcard">
                    Почта
                  </div>
                  <div
                    className="px-4 py-3 bg-subcard text-left font-medium text-subcard-text text-base md:text-lg  tracking-wider border-b border-subcard">
                    Прибыль
                  </div>
                </div>

                {/* Строки данных */}
                <div className="w-full">
                  {referralsData.map((item) => (
                    <div
                      key={item.number}
                      className="grid hover:bg-card-hover/50 transition-colors"
                      style={{
                        gridTemplateColumns:
                          "minmax(50px, 0.6fr) minmax(100px, 1.5fr) minmax(120px, 1.5fr) minmax(150px, 1.5fr) minmax(100px, 1.5fr)",
                        width: "100%",
                      }}
                    >
                      <div className="px-4 py-4 text-sm font-medium text-subcard-text/70">
                        {item.number}
                      </div>
                      <div className="px-4 py-4 text-sm text-subcard-text/70 ">
                        {item.registrationDate}
                      </div>
                      <div className="px-4 py-4 text-sm text-subcard-text/70">
                      <span
                        className={`inline-flex px-2 py-1 text-xs font-semibold ${
                          item.referralCount > 0
                            ? "text-subcard-text/80"
                            : "text-subcard-text/80"
                        }`}
                      >
                        {item.referralCount}
                      </span>
                      </div>
                      <div className="px-4 py-4 text-sm text-subcard-text/80 truncate">
                        {item.email}
                      </div>
                      <div className="px-4 py-4 text-sm text-left font-medium">
                      <span
                        className={
                          item.profit === "0.0 USDT"
                            ? "text-subcard-text/80"
                            : "text-subcard-text/80"
                        }
                      >
                        {item.profit}
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
      <Modal isOpen={modalOpen} onClose={() => setModalOpen(false)} title="Реферальная программа">
        <ReferralsModal/>
      </Modal>
    </>
  );
};
