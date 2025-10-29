"use client";

import styles from "./topUpBill.module.css";
import {FormInput} from "../forms/FormInput";
import Image from "next/image";
import {clsx} from "clsx";

import {useTheme} from 'next-themes'
import ImageDependTheme from "@/components/imageDependTheme/imageDependTheme";

export const TopUpBill = () => {
  const {theme} = useTheme()

  return (
    <div>
      <FormInput
        label="Счёт пополнения:"
        disabled
        defaultValue={"Лицевой (170.43 USDT)"}
      />
      <div className={styles.divider}></div>
      <div className={styles.qrCodeWrapper}>
        <ImageDependTheme srcDark={'/images/profile/QR_code.jpg'} srcLight={'/images/profile/QR_code_light.jpg'}
                          width={300} height={300} alt={"QR code"}/>
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
