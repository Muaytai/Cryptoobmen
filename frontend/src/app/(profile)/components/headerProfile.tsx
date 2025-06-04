"use client";

import React, { JSX } from "react";
import styles from "./headerProfile.module.css";
import { Button } from "../profile2/components/ui/button";
import { Avatar, AvatarImage, AvatarFallback } from "../profile2/components/ui/avatar";

export const HeaderProfile = (): JSX.Element => {
  return (
    <>
      <div className={styles.header}>
        <Button className={styles.actionButton}>
          <img
            className={styles.iconMedium}
            alt="Messages"
            src="/images/profile/vector-7.svg"
          />
        </Button>

        <div className={styles.userProfile}>
          <Avatar className={styles.avatar}>
            <AvatarImage src="/images/profile/rectangle-12960.png" alt="User" />
            <AvatarFallback className={styles.avatarFallback}>
              КР
            </AvatarFallback>
          </Avatar>
          <span className={styles.userName}>Кристина</span>
        </div>

        <Button className={styles.actionButton}>
          <img
            className={styles.iconMedium}
            alt="Settings"
            src="/images/profile/vector-3.svg"
          />
        </Button>
      </div>
    </>
  );
};
