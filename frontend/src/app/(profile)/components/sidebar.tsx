"use client";

import React, { JSX, useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { usePathname } from "next/navigation";
import styles from "./sidebar.module.css";

const navItems = [
  {
    icon: "/images/profile/vector-5.svg",
    alt: "Profile",
    path: "/profile2",
  },
  {
    icon: "/images/profile/vector-9.svg",
    alt: "Referrals",
    path: "/referrals",
  },
  {
    icon: "/images/profile/vector-4.svg",
    alt: "Details",
    path: "/details",
  },
];

export const SideBar = (): JSX.Element => {
  const pathname = usePathname();
  const [activeItem, setActiveItem] = useState(0);

  // При клике на элемент сайдбара
  const handleItemClick = (index: number) => {
    setActiveItem(index);
    // Здесь может быть логика перехода на другую страницу
  };

  return (
    <div className={styles.sidebar}>
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

      <div className={styles.navItems}>
        {navItems.map((item, index) => {
          const isActive = pathname === item.path;

          return (
            <Link href={item.path} key={index} passHref>
              <motion.div
                className={`${styles.navItem} ${
                  isActive ? styles.navItemActive : ""
                }`}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                {isActive && (
                  <motion.div
                    className={styles.activeIndicator}
                    layoutId="activeIndicator"
                    transition={{ type: "spring", stiffness: 300, damping: 30 }}
                  />
                )}
                <motion.img
                  className={styles.iconSidebar}
                  alt={item.alt}
                  src={item.icon}
                  initial={{ opacity: isActive ? 1 : 0.6 }}
                  animate={{ opacity: isActive ? 1 : 0.6 }}
                  transition={{ duration: 0.2 }}
                />
              </motion.div>
            </Link>
          );
        })}
      </div>
    </div>
  );
};
