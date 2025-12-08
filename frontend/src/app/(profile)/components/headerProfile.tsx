"use client";

import React, { JSX } from "react";
import Image from "next/image";
import styles from "./headerProfile.module.css";
import { Button } from "../me/components/ui/button";
import { Avatar, AvatarImage, AvatarFallback } from "../me/components/ui/avatar";
import { User } from "@/store/useAuthStore";
import { useRouter } from "next/navigation";

interface HeaderProfileProps {
  user: User;
}

export const HeaderProfile = ({ user }: HeaderProfileProps): JSX.Element => {
  const userName = user?.first_name || user?.username || "Пользователь";
  const userInitials = userName.substring(0, 2).toUpperCase();
  const userAvatar = user?.avatar || "/images/profile/rectangle-12960.webp";
  const router = useRouter();

  return (
    <>
      <div className={styles.header}>
        <Button className={styles.actionButton}>
          <Image
            width={24}
            height={24}
            className={styles.iconMedium}
            alt="Messages"
            src="/images/profile/vector-7.svg"
          />
        </Button>

        <div className={styles.userProfile}>
          <Avatar className={styles.avatar}>
            <AvatarImage src={userAvatar} alt="User" />
            <AvatarFallback className={styles.avatarFallback}>
              {userInitials}
            </AvatarFallback>
          </Avatar>
          <span className={styles.userName}>{userName}</span>
        </div>

        <Button className={styles.actionButton} onClick={() => router.push("/me/edit")}>
          <Image
            width={24}
            height={24}
            className={styles.iconSmall}
            alt="Edit"
            src="/images/profile/settings.svg"
          />
        </Button>
      </div>
    </>
  );
};
