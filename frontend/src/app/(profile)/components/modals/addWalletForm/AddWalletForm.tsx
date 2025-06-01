"use client";

import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect } from "react";
import { Button } from "@/components/ui/Button";
import styles from "./addWalletForm.module.css";
import { FormInput } from "../forms/FormInput";
import  FormSelect  from "../forms/FormSelect";

const schema = z.object({
  system: z.string().min(1, "Выберите способ"),
  address: z.string().min(1, "Введите адрес"),
  name: z.string().min(1, "Введите название"),
});

type FormData = z.infer<typeof schema>;

export const AddWalletForm = () => {
  const {
    register,
    handleSubmit,
    formState: { errors },
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

  return (
    <form onSubmit={handleSubmit(onSubmit)} className={styles.form}>
      <FormSelect
        label="Способ вывода:"
        error={errors.system?.message}
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
