"use client";
import styles from "./giftBoxModal.module.css";
import Image from "next/image";
import {clsx} from "clsx";

export const GiftBoxModal = () => {
  const boxPromoData = [
    {
      id: 1,
      title: "Покупай боксы за USDT или Токены!",
      icon: "/images/profile/gift1.svg"
    },
    {
      id: 2,
      title: "Открывай боксы",
      icon: "/images/profile/gift2.svg"
    },
    {
      id: 3,
      title: "Выигрывай Токены",
      icon: "/images/profile/gift3.svg"
    },
    {
      id: 4,
      title: "Обменивай токены на USDT или инвестируй их!",
      icon: "/images/profile/gift4.svg"
    },
    {
      id: 5,
      title: "Получай прибыль!",
      icon: "/images/profile/gift5.svg"
    }
  ];

  return (
    <div>
      <div className={styles.promoContainer}>
        {boxPromoData.map((item) => (
          <div key={item.id} className={clsx(styles.promoItem, "bg-subcard text-subcard-text")}>
            <Image src={item.icon}  alt="icon" width={18} height={18}/>
            <h3>{item.title}</h3>
          </div>
        ))}
      </div>
    </div>
  );
};
