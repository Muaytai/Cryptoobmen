"use client";

import React, {JSX} from "react";
import styles from "./referalls.module.css";
import {Button} from "@/components/ui/Button";
import {Card, CardContent} from "@/components/ui/card";
import {clsx} from "clsx";

export const Referrals = (): JSX.Element => {
  return (
    <section className={styles.container}>
      <h2 className="text-violet-600 text-3xl font-normal mb-8 [font-family:'Manrope',Helvetica]">
        Твоя реферальная программа
      </h2>

      <div
        className={clsx(styles.gridGroup, "flex gap-4 w-full bg-card p-5 text-subcard-text shadow-[0px_0px_20px_#0000004c] rounded-[15px] md:rounded-[25px] ")}>
        <Card
          className={clsx(styles.div1, "flex gap-1 w-full text-subcard-text ")}>
          <CardContent className="p-0 w-full flex gap-2 items-center justify-between">
            <h2 className="text-lg">Приглашай друзей и зарабатывай!</h2>
            <Button
              className="w-[160px] h-[36px] md:h-[48px] bg-violet-600 rounded-[15px] ">
                <span
                  className="font-medium text-white text-sm md:text-lg text-center [font-family:'Manrope',Helvetica]">
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
                src="/profile/vector-7_2.svg"
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
              className={clsx(styles.users, "font-medium text-subcard-text/60 text-xs md:text-sm [font-family:'Manrope',Helvetica]")}>

              <div className="divUsers1"><p>Сегодня:</p><p>0</p></div>
              <div className="divUsers2"><p>Неделя:</p><p>0</p></div>
              <div className="divUsers3"><p>Месяц:</p><p>0</p></div>
              <div className="divUsers4"><p>Всего:</p><p>0</p></div>

            </div>
          </CardContent>
        </Card>

        <Card
          className={clsx(styles.div4, "bg-subcard rounded-[15px] col-span-2")}
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
                src="/profile/vector-7_2.svg"
              />
            </div>
          </CardContent>
        </Card>

        <Card
          className={clsx(styles.div5, "bg-subcard rounded-[15px] col-span-2")}
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
                src="/profile/vector-7_2.svg"
              />
            </div>
          </CardContent>
        </Card>
      </div>

      <h2 className="mt-[100px] text-violet-600 text-3xl font-normal mb-8 [font-family:'Manrope',Helvetica]">
        Твоя реферальная программа
      </h2>

      <div className={styles.content}>
        <Card
          className="flex gap-4 w-full p-5 mb-[160px] text-subcard-text shadow-[0px_0px_20px_#0000004c] rounded-[15px] md:rounded-[25px] ">
          <CardContent className="p-0 md:p-0">34r34r34</CardContent>
        </Card>
      </div>

    </section>
  );
};
