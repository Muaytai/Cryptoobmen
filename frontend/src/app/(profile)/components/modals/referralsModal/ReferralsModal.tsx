"use client";
import styles from "./referralsModal.module.css";
import Image from "next/image";
import {clsx} from "clsx";

export const ReferralsModal = () => {
  const referralProgramData = [
  {
    id: 1,
    icon: "/images/profile/referal1.svg",
    title: "Приглашай друзей по твоей реферальной ссылке"
  },
  {
    id: 2,
    icon: "/images/profile/gift3.svg",
    title: "Получай за каждого друга по 100 токенов"
  },
  {
    id: 3,
    icon: "/images/profile/referal2.svg",
    title: "Получай % с комиссии твоих друзей в размере 50%"
  },
  {
    id: 4,
    icon: "/images/profile/referal3.svg",
    title: "Инвестируй полученные деньги"
  },
  {
    id: 5,
    icon: "/images/profile/gift5.svg",
    title: "Выводи прибыль"
  }
];

  return (
    <div>
      <div className={styles.container}>
        {referralProgramData.map((item) => (
          <div key={item.id} className={clsx(styles.item, "bg-subcard text-subcard-text")}>
            <Image src={item.icon}  alt="icon" width={18} height={18}/>
            <h3>{item.title}</h3>
          </div>
        ))}
      </div>
    </div>
  );
};
