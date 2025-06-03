"use client";

import styles from "./topUpBill.module.css";
import {FormInput} from "../forms/FormInput";
import Image from "next/image";
import {clsx} from "clsx";

import { useTheme } from 'next-themes'

export const TopUpBill = () => {
  const { theme } = useTheme()

  return (
    <div>
      <FormInput
        label="Счёт пополнения:"
        disabled
        defaultValue={"Лицевой (170.43 USDT)"}
      />
      <div className={styles.divider}></div>
      <div className={styles.qrCodeWrapper}>
        <Image src={theme === 'dark'
      ? '/images/profile/QR_code.jpg'
      : '/images/profile/QR_code_light.jpg'} alt="QR code" width={300}
               height={300}/>
      </div>
      <div className={styles.divider}></div>
      <p className={clsx(styles.walletTitle, "text-subcard-text/80")}>Адрес крипто кошелька:</p>
      <div className={styles.walletWrapper}>
        <span className={clsx(styles.wallet, "text-subcard-text/80")}>TJr9B3rF4vDsHHfgr5G5XxzrCuKhN3Zwa5</span>
        <Image className={styles.copy} src="/images/profile/copy.svg" alt="copy" width={18} height={18}/>
      </div>


    </div>
  );
};
