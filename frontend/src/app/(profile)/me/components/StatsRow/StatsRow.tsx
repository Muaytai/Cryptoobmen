import React from "react";
import styles from "./StatsRow.module.css";

export const StatsRow: React.FC = () => {
  return (
    <div className={styles.statsRow}>
      <div className={styles.statItem}>
        <span>День:</span>
        <span>0.00%</span>
      </div>
      <div className={styles.statItem}>
        <span>Месяц:</span>
        <span>00.00%</span>
      </div>
      <div className={styles.statItem}>
        <span>Общий:</span>
        <span>000.00%</span>
      </div>
    </div>
  );
};