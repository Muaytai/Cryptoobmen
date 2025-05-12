import React, {JSX} from "react";
import {Button} from "../../components/ui/button";
import {Card, CardContent} from "../../components/ui/card";
import styles from "./ViewByAnima.module.css";

export const ViewByAnima = (): JSX.Element => {
  const userWinnings = [
    {
      id: 1,
      email: "d************f@mail.ru",
      prize: "выйграл 55 токенов",
    },
    {
      id: 2,
      email: "z********k@gmail.com",
      prize: "выйграл бонус в размере 50% от суммы пополнения депозита",
    },
    {
      id: 3,
      email: "2******8@yandex.ru",
      prize: "выйграл 110 токенов",
    },
    {
      id: 4,
      email: "h********7@gmail.com",
      prize: "выйграл 10 USDT",
    },
  ];

  const prizeChances = [
    "80% - 5 USDT или 55 токенов",
    "15% - 10–25 USDT или 110–275 токенов",
    "5% - 50 USDT,  700 токенов или эксклюзивные бонусы",
  ];

  return (
    <section className={styles.container}>
      <h2 className={styles.title}>Подарочные боксы</h2>

      <div className={styles.content}>
        {/* Left card - Gift box information */}
        <Card className="w-full md:w-2/3 shadow-[0px_0px_20px_#0000004c] rounded-[15px] md:rounded-[25px] relative">
          <CardContent className="p-4 md:p-5">
            <div className="text-gray-500 text-base md:text-lg font-medium">
              Открывай наши уникальные подарочные боксы и получай ценные
              награды – токены, USDT и другие бонусы! Каждый бокс содержит
              случайный приз, а его стоимость фиксированная и доступна для
              покупки как за USDT, так и за токены платформы.
            </div>

            <h3 className="font-medium text-lg md:text-xl text-[#1a1a1a] mt-8 md:mt-16">
              Шансы выпадения призов:
            </h3>

            <div className="font-medium text-gray-500 text-base md:text-lg mt-2">
              {prizeChances.map((chance, index) => (
                <div key={index}>{chance}</div>
              ))}
            </div>

            <Button
              variant="outline"
              className="mt-8 md:mt-16 rounded-[15px] border-2 border-violet-600 px-4 md:px-[30px] py-2 md:py-[15px] h-auto"
            >
              <span className="font-medium text-base md:text-lg text-[#1a1a1a]">
                Подробнее
              </span>
            </Button>

            {/* Right section with gift box */}
            <div className="relative md:absolute w-full md:w-[520px] h-auto md:h-[363px] mt-8 md:mt-0 md:top-5 md:right-5 bg-gray-100 rounded-[15px] p-4 md:p-0">
              <img
                className="w-[100px] md:w-[156px] h-[108px] md:h-[169px] mx-auto mt-4 md:mt-6"
                alt="Gift Box"
                src="/profile/vector-1.svg"
              />

              <div className="px-2 md:px-5 mt-4 md:mt-8">
                <div className="text-center font-normal text-base md:text-xl">
                  <span>Доступно боксов: </span>
                  <span className="font-medium">5</span>
                </div>

                <div className="text-center font-medium text-gray-500 text-base md:text-lg mt-2 md:mt-3">
                  Стоимость: 5 USDT или 55 токенов
                </div>

                <div className="flex flex-col md:flex-row justify-between gap-3 md:gap-4 mt-4 md:mt-5">
                  <Button className="w-full md:w-[220px] rounded-[15px] bg-violet-600 px-4 md:px-[30px] py-2 md:py-[15px] h-auto">
                    <span className="font-medium text-base md:text-lg text-white">
                      Купить
                    </span>
                  </Button>

                  <Button
                    variant="outline"
                    className="w-full md:w-[220px] rounded-[15px] border-2 border-violet-600 px-4 md:px-[30px] py-2 md:py-[15px] h-auto"
                  >
                    <span className="font-medium text-base md:text-lg text-[#1a1a1a]">
                      Открыть
                    </span>
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* User winnings card */}
        {/* Right card - User winnings */}
        <Card className="w-full md:w-1/3 shadow-[0px_0px_20px_#0000004c] rounded-[15px] md:rounded-[25px]">
          <CardContent className="p-4 md:p-5">
            <h3 className="font-medium text-[#1a1a1a] text-lg md:text-xl mb-4 md:mb-5">
              Выигрыши пользователей
            </h3>

            {userWinnings.map((user, index) => (
              <div key={index} className="flex items-start mb-4 md:mb-5">
                <div className="w-10 h-10 md:w-12 md:h-12 bg-white rounded-3xl flex items-center justify-center mr-3 md:mr-4">
                  <img
                    className="w-[20px] h-[20px] md:w-[30px] md:h-[30px]"
                    alt="User Icon"
                    src="/profile/vector.svg"
                  />
                </div>
                <div className="font-medium text-gray-500 text-base md:text-lg">
                  {user.email} <br />
                  {user.prize}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </section>
  );
};
