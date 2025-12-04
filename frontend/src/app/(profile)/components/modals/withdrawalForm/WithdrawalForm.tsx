"use client";

import {Controller, useForm} from "react-hook-form";
import {z} from "zod";
import {zodResolver} from "@hookform/resolvers/zod";
import {Button} from "@/components/ui/Button";
import styles from "./withdrawalForm.module.css";
import {FormInput} from "../forms/FormInput";
import FormSelect from "../forms/FormSelect";
import {OptionType} from "../types/types";

const schema = z.object({
  bill: z.string().min(1, "Выберите лицевой счет"),
  amount: z
    .string()
    .refine((val) => {
      const num = parseFloat(val);
      return !isNaN(num) && num >= 5 && num <= 100000;
    }, {
      message: "Введите сумму от 5 до 100 000",
    }),
  wallet: z.string().min(1, "Введите название"),
});

type FormData = z.infer<typeof schema>;

export const WithdrawalForm = () => {
  const {
    register,
    handleSubmit,
    formState: {errors},
    control,
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      bill: "Лицевой ( 170.43 USDT)",
      amount: "",
      wallet: "",
    },
  });

  const onSubmit = (data: FormData) => {
    console.log("Submitted:", data);
  };

  const options: OptionType[] = [
    {value: "BinanceWallet", label: "Binance Wallet", icon: "/images/profile/BinanceWallet.svg"},
    {value: "Coinbase Wallet.svg", label: "Coinbase Wallet", icon: "/images/profile/CoinbaseWallet.svg"},
    {value: "MetaMask", label: "Meta Mask", icon: "/images/profile/MetaMask.svg"},
    {value: "OKXWallet", label: "OKX Wallet", icon: "/images/profile/OKXWallet.svg"},
    {value: "Tonkeeper", label: "Tonkeeper", icon: "/images/profile/Tonkeeper.svg"},
    {
      value: "TrustWallet",
      label: "Trust Wallet",
      icon: "/images/profile/TrustWallet.svg",
    },
  ];

  return (
    <form onSubmit={handleSubmit(onSubmit)} className={styles.form}>
      <FormInput
        label="Счёт списания:"
        required
        disabled
        error={errors.bill?.message}
        {...register("bill")}
      />

      <div className={styles.divider}></div>

      <Controller
        control={control}
        name="wallet"
        render={({field}) => (
          <FormSelect
            label="Крипто-кошелек:"
            required
            options={options}
            error={errors.wallet?.message}
            value={field.value}
            onChange={field.onChange}
            onBlur={field.onBlur}
            name={field.name}
          />
        )}
      />

      <div className={styles.divider}></div>

      <FormInput
        label="Сумма, USDT"
        required
        error={errors.amount?.message}
        {...register("amount")}
      />
      <p className="text-subcard-text/70">Минимальная сумма вывода — 5 USDT</p>
      <p className="text-subcard-text/70">Максимальная сумма вывода — 100.000 USDT</p>

      <Button type="submit" className={styles.save}>
        Вывести
      </Button>
      <p className="text-subcard-text/70">Вывод производиться в течении 5 дней</p>
      <p className="text-subcard-text/70">Комиссия сервиса на вывод — 5%</p>
    </form>
  );
};
