import React, {JSX, useState} from "react";
import {Button} from "../../components/ui/button";
import {Card, CardContent} from "../../components/ui/card";
import styles from "./ViewByAnima.module.css";
import {GiftBoxModal} from "@/app/(profile)/components/modals/giftBoxModal/GiftBoxModal";
import {Modal} from "@/app/(profile)/components/modals/Modal";

export const ViewByAnima = (): JSX.Element => {
  const [modalOpen, setModalOpen] = useState(false);


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
      <h2 className="text-violet-600 text-3xl font-normal mb-8 [font-family:'Manrope',Helvetica]">
        Подарочные боксы
      </h2>

      <div className={styles.content}>
        {/* Left card - Gift box information */}
        <Card
          className="flex flex-col md:flex-row gap-4 w-full p-5 md:w-2/3 shadow-[0px_0px_20px_#0000004c] rounded-[15px] md:rounded-[25px] ">
          <CardContent className="md:w-[50%] w-full p-0 md:p-0">
            <div className="text-subcard-text/60 text-base md:text-lg font-medium">
              Открывай наши уникальные подарочные боксы и получай ценные награды
              – токены, USDT и другие бонусы! Каждый бокс содержит случайный
              приз, а его стоимость фиксированная и доступна для покупки как за
              USDT, так и за токены платформы.
            </div>

            <h3 className="font-medium text-lg md:text-xl text-subcard-text mt-5">
              Шансы выпадения призов:
            </h3>

            <div className="font-medium text-subcard-text/60 text-base md:text-lg mt-2">
              {prizeChances.map((chance, index) => (
                <div key={index}>{chance}</div>
              ))}
            </div>

            <Button
              variant="outline"
              className="w-[160px]  h-[36px] md:h-[48px] rounded-[15px] bg-subcard border-2 border-solid border-violet-600 mt-5"
              onClick={() => setModalOpen(true)}
            >
              <span
                className="font-medium text-subcard-text text-sm md:text-lg text-center [font-family:'Manrope',Helvetica]">
                Подробнее
              </span>
            </Button>
          </CardContent>

          {/* Right section with gift box */}
          <div className="md:w-[50%] w-full mt-8 md:mt-0 md:top-5 md:right-5 bg-subcard rounded-[15px] p-4 md:p-0">
            <img
              className="w-[100px] md:w-[156px] h-[108px] md:h-[169px] mx-auto mt-4 md:mt-6"
              alt="Gift Box"
              src="/images/profile/vector-1.svg"
            />

            <div className="px-2 md:px-5 mt-4 md:mt-8">
              <div className="text-center font-normal text-subcard-text md:text-xl">
                <span>Доступно боксов: </span>
                <span className="font-medium">5</span>
              </div>

              <div className="text-center font-medium text-subcard-text/60 text-base md:text-lg mt-2 md:mt-3">
                Стоимость: 5 USDT или 55 токенов
              </div>

              <div className="flex flex-col lg:flex-row justify-center items-center gap-3 md:gap-4 mt-4 md:mt-5 pb-4">
                <Button className="w-[160px] h-[36px] md:h-[48px] bg-violet-600 rounded-[15px] ">
                  <span
                    className="font-medium text-white text-sm md:text-lg text-center [font-family:'Manrope',Helvetica]">
                    Купить
                  </span>
                </Button>
                <Button
                  variant="outline"
                  className="w-[160px]  h-[36px] md:h-[48px] rounded-[15px] bg-subcard border-2 border-solid border-violet-600"
                >
                  <span
                    className="font-medium text-subcard-text text-sm md:text-lg text-center [font-family:'Manrope',Helvetica]">
                    Открыть
                  </span>
                </Button>
              </div>
            </div>
          </div>
        </Card>

        {/* User winnings card */}
        {/* Right card - User winnings */}
        <Card className="w-full md:w-1/3 shadow-[0px_0px_20px_#0000004c] rounded-[15px] md:rounded-[25px]">
          <CardContent className="p-4 md:p-5">
            <h3 className="font-medium text-subcard-text text-lg md:text-xl mb-4 md:mb-5">
              Выигрыши пользователей
            </h3>

            {userWinnings.map((user, index) => (
              <div key={index} className="flex items-center mb-4 md:mb-5">
                <div className="flex items-center shrink-0 justify-center mr-3 md:mr-4">
                  <img
                    className="w-[30px] h-[30px]"
                    alt="User Icon"
                    src="/images/profile/vector.svg"
                  />
                </div>
                <div className="font-medium text-subcard-text/60 text-base md:text-lg">
                  {user.email} <br/>
                  {user.prize}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <Modal isOpen={modalOpen} onClose={() => setModalOpen(false)} title="Подарочные боксы">
        <GiftBoxModal/>
      </Modal>
    </section>
  );
};
