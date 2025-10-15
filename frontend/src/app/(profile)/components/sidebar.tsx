"use client";

import React, {JSX, useState, useEffect} from "react";
import {motion, AnimatePresence} from "framer-motion";
import Link from "next/link";
import {usePathname} from "next/navigation";
import styles from "./sidebar.module.css";
import {clsx} from "clsx";
import Image from "next/image";

import {useTheme} from 'next-themes';
import {useAuthStore} from '@/store/useAuthStore';
import ImageDependTheme from "@/components/imageDependTheme/imageDependTheme";

const navItems = [
  {
    icon: "/images/profile/vector-5.svg",
    alt: "Profile",
    title: "Главня",
    path: "/me",
  },
  {
    icon: "/images/profile/vector-9.svg",
    alt: "Referrals",
    title: "Реферальная программа",
    path: "/referrals",
  },
  {
    icon: "/images/profile/vector-4.svg",
    alt: "Details",
    title: "Реквезиты",
    path: "/details",
  },
  {
    icon: "/images/profile/settings.svg",
    alt: "Admin",
    title: "Админ-панель",
    path: "/admin",
  },
];

export const SideBar = (): JSX.Element => {
  const pathname = usePathname();
  const [isMobile, setIsMobile] = useState(false);
  const [isOpen, setIsOpen] = useState(false);

  const {theme} = useTheme();
  const user = useAuthStore(state => state.user);

  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < 768);
      if (window.innerWidth >= 768) {
        setIsOpen(false);
      }
    };

    handleResize();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  // Закрываем меню при смене страницы
  useEffect(() => {
    if (isMobile) {
      setIsOpen(false);
    }
  }, [pathname, isMobile]);

  const toggleMenu = () => {
    setIsOpen(!isOpen);
  };

  return (
    <>
      {/* Кнопка гамбургер для мобильных */}
      {isMobile && (
        <motion.div
          className={clsx(styles.hamburgerButton, "bg-card")}
          onClick={toggleMenu}
          whileTap={{scale: 0.9}}
        >
          {[1, 2, 3].map((line) => (
            <motion.img
              key={line}
              className={styles.iconSidebar}
              alt={`Menu line ${line}`}
              src="/images/profile/line-153.svg"
              initial={{opacity: 0, y: -10}}
              animate={{opacity: 1, y: 0}}
              transition={{duration: 0.3, delay: line * 0.1}}
            />
          ))}
        </motion.div>
      )}

      {/* Бэкдроп для мобильных */}
      {isMobile && isOpen && (
        <motion.div
          className={styles.backdrop}
          initial={{opacity: 0}}
          animate={{opacity: 1}}
          exit={{opacity: 0}}
          onClick={toggleMenu}
        />
      )}

      {/* Основной сайдбар */}
      <AnimatePresence>
        {(!isMobile || isOpen) && (
          <motion.div
            className={clsx(styles.sidebar, "!bg-card md:!bg-transparent !text-subcard-text/80")}
            initial={isMobile ? {x: -300} : {}}
            animate={isMobile ? {x: isOpen ? 0 : -300} : {}}
            exit={isMobile ? {x: -300} : {}}
            transition={{type: "spring", stiffness: 300, damping: 30}}
          >
            <Link className={styles.mobileLogo} href="/">
              <ImageDependTheme  srcDark={'/images/logo.png'} srcLight={'/images/logo_light.png'} />

            </Link>
            {/* {!isMobile && (
              <div className={styles.hamburger}>
                {[1, 2, 3].map((line) => (
                  <motion.img
                    key={line}
                    className={styles.iconSidebar}
                    alt={`Menu line ${line}`}
                    src="/images/profile/line-153.svg"
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3, delay: line * 0.1 }}
                  />
                ))}
              </div>
            )} */}

            <div className={styles.navItems}>
              {navItems
                .filter(item => {
                  // Скрываем пункт "Админ-панель" для пользователей без прав администратора сайта
                  if (item.path === '/admin') {
                    return !!user?.is_site_admin;
                  }
                  return true;
                })
                .map((item, index) => {
                const isActive = pathname?.startsWith(item.path);

                return (
                  <Link href={item.path} key={index}>
                    <motion.div
                      className={`${styles.navItem} ${
                        isActive ? styles.navItemActive : ""
                      }`}
                      whileHover={{scale: 1.05}}
                      whileTap={{scale: 0.95}}
                    >
                      {isActive && (
                        <motion.div
                          className={styles.activeIndicator}
                          layoutId="activeIndicator"
                          transition={{
                            type: "spring",
                            stiffness: 300,
                            damping: 30,
                          }}
                        />
                      )}
                      <motion.img
                        className={styles.iconSidebar}
                        alt={item.alt}
                        src={item.icon}
                        initial={{opacity: isActive ? 1 : 0.6}}
                        animate={{opacity: isActive ? 1 : 0.6}}
                        transition={{duration: 0.2}}
                      />
                      {(!isMobile || isOpen) && (
                        <motion.span
                          className={styles.navTitle}
                          initial={{opacity: 0, x: -10}}
                          animate={{opacity: 1, x: 0}}
                          transition={{delay: 0.1}}
                        >
                          {item.title}
                        </motion.span>
                      )}
                    </motion.div>
                  </Link>
                );
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};
