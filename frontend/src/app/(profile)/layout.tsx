"use client";

import styles from "./layout.module.css";
import React, { useEffect } from "react";
import { useAuthStore } from "@/store/useAuthStore";
import { useWalletStore } from "@/store/useWalletStore";
import { useRouter } from "next/navigation";

import { HeaderProfile } from "./components/headerProfile";
import { SideBar } from "./components/sidebar";
import { ProfileProvider } from "./context/ProfileContext";

export default function Layout({ children }: { children: React.ReactNode }) {
  const { user, isAuthenticated, isLoading: authLoading } = useAuthStore();
  const { wallets, isLoading: walletLoading, totalUsdBalance } = useWalletStore();
  const router = useRouter();

  useEffect(() => {
    console.log(`[Layout useEffect] Running. authLoading: ${authLoading}, isAuthenticated: ${isAuthenticated}`);
    if (!authLoading) {
      if (!isAuthenticated) {
        console.log(`[Layout useEffect] Condition met: !authLoading (${!authLoading}) && !isAuthenticated (${!isAuthenticated}). Redirecting to /login.`);
        router.push('/login?from=profile');
      } else {
        console.log(`[Layout useEffect] Condition met: !authLoading (${!authLoading}) && isAuthenticated (${!isAuthenticated}). User is authenticated. No redirect.`);
      }
    } else {
      console.log(`[Layout useEffect] authLoading is true. Waiting for auth check to complete.`);
    }
    if (!walletLoading) {
      if (!wallets) {
        console.log(`[Layout useEffect] кошельки загружены но экземпляров нет (${!walletLoading}) && !wallets (${!wallets}). Redirecting to /login.`);
      } else {
        console.log(`[Layout useEffect] кошельки загружены и экземпляры есть (${!walletLoading}) && wallets (${wallets}). User is authenticated. No redirect.`);
      }
    } else {
      console.log(`[Layout useEffect] ожидание загрузки кошельков.`);
    }
  }, [isAuthenticated, authLoading, router, wallets, walletLoading, totalUsdBalance]);

  console.log(`[Layout Render] authLoading: ${authLoading}, isAuthenticated: ${isAuthenticated}, user: ${user ? user.email : 'null'}`);

  if (authLoading) {
    console.log("[Layout Render] Displaying loading state because authLoading is true.");
    return (
      <div className="flex w-full min-h-screen bg-card text-white items-center justify-center">
        <div>Загрузка данных профиля...</div>
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    console.log(`[Layout Render] authLoading is false. Condition !isAuthenticated (${!isAuthenticated}) || !user (${!user}) is true. Redirecting to login.`);
    router.push('/login?from=profile');
    return (
      <div className="flex w-full min-h-screen bg-card text-white items-center justify-center">
        <div>Перенаправление на страницу входа...</div>
      </div>
    );
  }

  console.log("[Layout Render] Proceeding to render profile layout.");

  return (
    <ProfileProvider user={user} totalUsdBalance={totalUsdBalance}>
      <div className={styles.container}>
        <SideBar />
        <div className={styles.wrapper}>
          <div className={styles.wrapperMain}>
            <HeaderProfile user={user} />
            {children}
          </div>
        </div>
      </div>
    </ProfileProvider>
  );
}
