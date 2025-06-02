"use client";

import {useForm} from "react-hook-form";
import {z} from "zod";
import {zodResolver} from "@hookform/resolvers/zod";
import {useEffect} from "react";
import {Button} from "@/components/ui/Button";
import styles from "./addWalletForm.module.css";
import {FormInput} from "../forms/FormInput";
import FormSelect from "../forms/FormSelect";

const schema = z.object({
  system: z.string().min(1, "Выберите способ"),
  address: z.string().min(1, "Поле адрес реквизита не может быть пустым"),
  name: z.string().min(1, "Поле имени не может быть пустым"),
});

type FormData = z.infer<typeof schema>;

export const AddWalletForm = () => {
  const {
    register,
    handleSubmit,
    formState: {errors},
    setFocus,
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      system: "USDT (TRC20)",
      address: "",
      name: "",
    },
  });

  // useEffect(() => {
  //   setFocus("address");
  // }, [setFocus]);

  const onSubmit = (data: FormData) => {
    console.log("Submitted:", data);
  };

  const options: OptionType[] = [

    {value: "btc", label: "Bitcoin", icon: "/images/profile/bitcoin.svg"},
    {value: "eth", label: "Ethereum", icon: "/images/profile/ethereum.svg"},
    {value: "lte", label: "Litecoin", icon: "/images/profile/litecoin.svg"},
    {value: "usdt_trc20", label: "USDT (TRC20)", icon: "/images/profile/vector-usdt.svg",},
    {value: "usdt_erc20", label: "USDT (ERC20)", icon: "/images/profile/vector-usdt.svg",},
    {value: "usdt_bep20", label: "USDT (BEP20)", icon: "/images/profile/vector-usdt.svg",},
    {value: "toncoin", label: "Toncoin", icon: "/images/profile/toncoin.svg",},
  ];

  return (
    <form onSubmit={handleSubmit(onSubmit)} className={styles.form}>
      <FormSelect
        label="Способ вывода:"
        error={errors.system?.message}
        options={options}
        {...register("system")}
      >
        <option value="USDT (TRC20)">₮ USDT (TRC20)</option>
      </FormSelect>

      <FormInput
        label="Адрес реквизита"
        required
        error={errors.address?.message}
        {...register("address")}
      />

      <FormInput
        label="Название"
        required
        error={errors.name?.message}
        {...register("name")}
      />

      <Button type="submit" className={styles.save}>
        Сохранить
      </Button>
    </form>
  );
};
