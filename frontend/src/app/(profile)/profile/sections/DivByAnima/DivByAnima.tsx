import {CheckCircleIcon, CopyIcon} from "lucide-react";
import React, {JSX} from "react";
import styles from "./DivByAnima.module.css";
import {Button} from "@/components/ui/Button";
import {Card, CardContent} from "@/components/ui/card";
import {clsx} from "clsx";

export const DivByAnima = (): JSX.Element => {
  const userData = {
    name: "Кристина Соколова",
    welcomeMessage: "С возвращением!",
    profileImage: "/profile/rectangle-12960.png",
    uid: "9999999999",
    verificationType: "Верифицирован",
    userType: "Личный",
    vipLevel: "Нету",
    email: "kristina_sokolova@mail.ru",
    referralLink: "https://сrypto.com/referral/USERNAME",
  };

  // Account data
  const accountData = {
    personal: {
      title: "Лицевой счет",
      balance: "170.43 USDT",
    },
    partner: {
      title: "Партнерский счет",
      balance: "**** USDT",
    },
  };

  return (
    <div className={styles.container}>

      {/* Cards Grid */}
      <div className={styles.cardsGrid}>
        {/* Profile Section */}
        <div className={clsx(styles.profileSection, styles.div1)}>
          <div className={styles.profilePicture}>
            <img
              className={styles.profileImage}
              alt="Profile"
              src={userData.profileImage}
            />
          </div>

          <div className={styles.userInfo}>
            <p className={styles.welcomeMessage}>{userData.welcomeMessage}</p>
            <div className={styles.nameContainer}>
              <h2 className={styles.userName}>{userData.name}</h2>
              <img className={styles.editIcon} alt="Edit" src="/profile/edit-2.png"/>
            </div>
          </div>
        </div>

        {/* User Info Cards */}
        <Card className={clsx(styles.div2, "bg-gray-100 rounded-[15px]")}>
          <CardContent className="p-3 md:p-5 h-[80px] md:h-[104px] relative">
            <span className="font-medium text-gray-500 text-xs md:text-sm [font-family:'Manrope',Helvetica]">
              UID
            </span>
            <div className="flex items-center justify-between mt-4 ">
              <span className="font-medium text-[#1a1a1a] text-base md:text-lg [font-family:'Manrope',Helvetica]">
                {userData.uid}
              </span>
              <img
                className="w-[14px] h-[14px] md:w-[18px] md:h-[18px]"
                alt="Copy"
                src="/profile/vector-7_1.svg"
              />
            </div>
          </CardContent>
        </Card>

        <Card className={clsx(styles.div4, "bg-subcard rounded-[15px]")}>
          <CardContent className="p-3 md:p-5 h-[80px] md:h-[104px]">
            <span className="font-medium text-subcard-text/60 text-xs md:text-sm [font-family:'Manrope',Helvetica]">
              Тип пользователя
            </span>
            <div className="mt-4 ">
              <span className="font-medium text-subcard-text text-base md:text-lg [font-family:'Manrope',Helvetica]">
                {userData.userType}
              </span>
            </div>
          </CardContent>
        </Card>


        {/* Verification & VIP */}
        <Card className={clsx(styles.div3, "bg-gray-100 rounded-[15px]")}>
          <CardContent className="p-3 md:p-5 h-[80px] md:h-[104px] relative">
            <span className="font-medium text-gray-500 text-xs md:text-sm [font-family:'Manrope',Helvetica]">
              Проверка&nbsp;&nbsp;личности
            </span>
            <div className="flex items-center justify-between mt-4 ">
              <span className="font-medium text-[#1a1a1a] text-base md:text-lg [font-family:'Manrope',Helvetica]">
                {userData.verificationType}
              </span>
              <img
                className="w-[18px] h-[18px] md:w-[22px] md:h-[22px]"
                alt="Verified"
                src="/profile/vector-6_1.svg"
              />
            </div>
          </CardContent>
        </Card>

        <Card className={clsx(styles.div5, "bg-gray-100 rounded-[15px]")}>
          <CardContent className="p-3 md:p-5 h-[80px] md:h-[104px]">
            <span className="font-medium text-gray-500 text-xs md:text-sm [font-family:'Manrope',Helvetica]">
              VIP уровень
            </span>
            <div className="mt-4 ">
              <span className="font-medium text-[#1a1a1a] text-base md:text-lg [font-family:'Manrope',Helvetica]">
                {userData.vipLevel}
              </span>
            </div>
          </CardContent>
        </Card>

        {/* Personal Account Card */}
        <Card className={clsx(styles.div6, "bg-gray-100 rounded-[15px] col-span-2")}>
          <CardContent className="p-3 md:p-5 h-[180px] md:h-[214px] relative">
            <div className="flex items-center">
              <span className="font-normal text-violet-600 text-base md:text-xl [font-family:'Manrope',Helvetica]">
                {accountData.personal.title}
              </span>
              <img
                className="w-[24px] h-4 md:w-[34px] md:h-5 ml-2"
                alt="Vector"
                src="/profile/vector-12.svg"
              />
            </div>

            <div
              className="mt-6 md:mt-[38px] font-normal text-[#1a1a1a] text-2xl md:text-[32px] [font-family:'Manrope',Helvetica]">
              {accountData.personal.balance}
            </div>

            <div className="flex flex-col gap-2 md:gap-3 absolute top-3 md:top-5 right-3 md:right-5">
              <Button
                className="w-[160px] h-[36px] md:h-[48px] bg-violet-600 rounded-[15px] ">
                <span
                  className="font-medium text-white text-sm md:text-lg text-center [font-family:'Manrope',Helvetica]">
                  Пополнить
                </span>
              </Button>

              <Button
                variant="outline"
                className="w-[160px]  h-[36px] md:h-[48px] rounded-[15px] border-2 border-solid border-violet-600"
              >
                <span
                  className="font-medium text-[#1a1a1a] text-sm md:text-lg text-center [font-family:'Manrope',Helvetica]">
                  Вывести
                </span>
              </Button>

              <Button
                className="w-[160px] h-[36px] md:h-[48px] bg-violet-600 rounded-[15px]">
                <span
                  className="font-medium text-white text-sm md:text-lg text-center [font-family:'Manrope',Helvetica]">
                  Инвестировать
                </span>
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Email Card */}
        <Card className={clsx(styles.div7, "bg-gray-100 rounded-[15px] col-span-2")}>
          <CardContent className="p-3 md:p-5 h-[80px] md:h-[104px] relative">
            <span className="font-medium text-gray-500 text-xs md:text-sm [font-family:'Manrope',Helvetica]">
              Почта
            </span>
            <div className="flex items-center mt-2 md:mt-[14px]">
              <span className="font-medium text-[#1a1a1a] text-base md:text-lg [font-family:'Manrope',Helvetica]">
                {userData.email}
              </span>
              <img
                className="w-4 h-2 md:w-5 md:h-3 ml-2"
                alt="Email"
                src="/profile/vector-8_1.svg"
              />
            </div>
          </CardContent>
        </Card>


        {/* Partner Account Card */}
        <Card className={clsx(styles.div8, "bg-gray-100 rounded-[15px] col-span-2")}>
          <CardContent className="p-3 md:p-5 h-[180px] md:h-[214px] relative">
            <div className="flex items-center">
              <span className="font-medium text-violet-600 text-base md:text-xl [font-family:'Manrope',Helvetica]">
                {accountData.partner.title}
              </span>
              <img
                className="w-[24px] h-3 md:w-[34px] md:h-4 ml-2"
                alt="Vector"
                src="/profile/vector-10.svg"
              />
            </div>

            <div
              className="mt-6 md:mt-[38px] font-normal text-[#1a1a1a] text-2xl md:text-[32px] [font-family:'Manrope',Helvetica]">
              {accountData.partner.balance}
            </div>

            <div className="flex flex-col gap-2 md:gap-3 absolute top-3 md:top-5 right-3 md:right-5">
              <Button
                className="w-[160px] h-[36px] md:h-[48px] bg-violet-600 rounded-[15px]">
                <span
                  className="font-medium text-white text-sm md:text-lg text-center [font-family:'Manrope',Helvetica]">
                  Пополнить
                </span>
              </Button>

              <Button
                variant="outline"
                className="w-[160px] h-[36px] md:h-[48px] rounded-[15px] border-2 border-solid border-violet-600"
              >
                <span
                  className="font-medium text-[#1a1a1a] text-sm md:text-lg text-center [font-family:'Manrope',Helvetica]">
                  Вывести
                </span>
              </Button>
            </div>
          </CardContent>
        </Card>


        {/* Referral Link Card */}
        <Card className={clsx(styles.div9, "bg-gray-100 rounded-[15px] col-span-2")}>
          <CardContent className="p-3 md:p-5 h-[80px] md:h-[104px] relative">
            <span className="font-medium text-gray-500 text-xs md:text-sm [font-family:'Manrope',Helvetica]">
              Реферальная ссылка
            </span>
            <div className="flex w-full items-center justify-between mt-4 ">
              <span className="font-medium text-[#1a1a1a] text-base md:text-lg [font-family:'Manrope',Helvetica] ">
                {userData.referralLink}
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


    </div>
  );
};