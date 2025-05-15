"use client";

import React, { JSX } from "react";
import styles from "./details.module.css";
import { Button } from "@/components/ui/Button";
import { Card, CardContent } from "@/components/ui/card";
import { clsx } from "clsx";

export const Details = (): JSX.Element => {
  return (
    <section className={styles.container}>
      <h2 className="text-violet-600 text-3xl font-normal mb-8 [font-family:'Manrope',Helvetica]">
        Твоя реферальная программа
      </h2>

      <div className={styles.content}>
        <Card className="flex gap-4 w-full p-5 md:w-2/3 shadow-[0px_0px_20px_#0000004c] rounded-[15px] md:rounded-[25px] ">
          <CardContent className="p-0 md:p-0">34r34r34</CardContent>
        </Card>
      </div>
    </section>
  );
};
