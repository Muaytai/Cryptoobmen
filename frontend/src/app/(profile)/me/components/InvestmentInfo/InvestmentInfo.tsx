import React from "react";
import styles from "./InvestmentInfo.module.css";

export const InvestmentInfo: React.FC = () => {
  return (
    <div className={styles.container}>
      <div className={styles.infoItem}>
        <span>Дата инвестирования:</span>
        <span>00.00.0000</span>
      </div>
      <div className={styles.infoItem}>
        <span>Торгует:</span>
        <span>Дней: 0</span>
      </div>
      <div className={styles.infoItem}>
        <span>Сумма:</span>
        <span>000 USDT</span>
      </div>
    </div>
  );
};