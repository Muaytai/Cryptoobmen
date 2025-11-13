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
        {/* Main gift box card */}
        <Card className={styles.mainCard}>
          <CardContent className={styles.cardContent}>
            <div className={styles.cardContentWrapper}>
              <div className={styles.descriptionWrapper}>
                <p className={styles.description}>
                  Открывай наши уникальные подарочные боксы <br/>и получай ценные
                  награды – токены, USDT и другие бонусы! Каждый бокс содержит
                  случайный приз, <br/>а его стоимость фиксированная и доступна
                  для покупки как за USDT, так и за токены платформы.
                </p>
              </div>

              <h3 className={styles.chanceTitle}>Шансы выпадения призов:</h3>

              <div className={styles.chanceList}>
                {prizeChances.map((chance, index) => (
                  <p key={index}>{chance}</p>
                ))}
              </div>

              <Button className={styles.detailsButton}>Подробнее</Button>
            </div>

            {/* Nested gift box card */}
            <Card className={styles.giftBoxCard}>
              <CardContent className={styles.giftBoxContent}>
                <img
                  className={styles.giftBoxImage}
                  alt="Gift Box"
                  src="/profile/vector-1.svg"
                />

                <div className={styles.giftBoxInfo}>
                  <p className={styles.availableBoxes}>
                    Доступно боксов: <span className={styles.fontMedium}>5</span>
                  </p>

                  <p className={styles.boxPrice}>
                    Стоимость: 5 USDT или 55 токенов
                  </p>

                  <div className={styles.boxActions}>
                    <Button className={styles.boxButton}>Купить</Button>
                    <Button className={styles.boxButtonPrimary}>Открыть</Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </CardContent>
        </Card>

        {/* User winnings card */}
        <Card className={styles.winningsCard}>
          <CardContent className={styles.cardContent}>
            <div><h3 className={styles.winningsTitle}>Выигрыши пользователей</h3>

              <div className={styles.winningsList}>
                {userWinnings.map((user) => (
                  <div key={user.id} className={styles.winningItem}>
                    <div className={styles.userIcon}>
                      <img
                        className={styles.userIconImage}
                        alt="User Icon"
                        src="/profile/vector.svg"
                      />
                    </div>
                    <div className={styles.winningInfo}>
                      {user.email} <br/>
                      {user.prize}
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
