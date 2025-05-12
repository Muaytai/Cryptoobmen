"use client";

import React, {JSX} from "react";

import {
  Avatar,
  AvatarFallback,
  AvatarImage,
} from "./components/ui/avatar";
import {Button} from "./components/ui/button";
import {DivByAnima} from "./sections/DivByAnima";
import {DivWrapperByAnima} from "./sections/DivWrapperByAnima/DivWrapperByAnima";
import {ViewByAnima} from "./sections/ViewByAnima";
import {ViewWrapperByAnima} from "./sections/ViewWrapperByAnima";

import styles from "./Profile.module.css";

export const Profile = (): JSX.Element => {
  const navItems = [
    {icon: "/profile/vector-5.svg", isActive: true, alt: "Dashboard"},
    {icon: "/profile/vector-9.svg", isActive: false, alt: "Analytics"},
    {icon: "/profile/vector-4.svg", isActive: false, alt: "Reports"},
  ];

  const actionButtons = [
    {icon: "/profile/vector-16.svg", alt: "Search"},
    {icon: "/profile/vector-17.svg", alt: "Notifications", hasBg: true},
    {icon: "/profile/vector-7.svg", alt: "Messages"},
    {icon: "/profile/vector-3.svg", alt: "Settings"},
  ];

  return (
    <div className={styles.container}>
      <div className={styles.wrapper}>
        <div className={styles.wrapperMain}>
          <div className={styles.header}>
            <div className={styles.searchContainer}>
              <div className={styles.searchBox}>
                <div className={styles.searchInput}>
                  <img
                    className={styles.icon}
                    alt="Search"
                    src="/profile/vector-16.svg"
                  />
                </div>
                <Button className={styles.actionButton}>
                  <img
                    className={styles.iconLarge}
                    alt="Notifications"
                    src="/profile/vector-17.svg"
                  />
                </Button>
              </div>
            </div>

            <Button className={styles.actionButton}>
              <img
                className={styles.iconMedium}
                alt="Messages"
                src="/profile/vector-7.svg"
              />
            </Button>

            <div className={styles.userProfile}>
              <Avatar className={styles.avatar}>
                <AvatarImage src="/profile/rectangle-12960.png" alt="User"/>
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
                src="/profile/vector-3.svg"
              />
            </Button>
          </div>

          <DivByAnima/>
          <DivWrapperByAnima/>
          <ViewWrapperByAnima/>
          <ViewByAnima/>

          <div className={styles.sidebar}>
            <div className={styles.hamburger}>
              {[1, 2, 3].map((line) => (
                <img
                  key={line}
                  className={styles.iconSidebar}
                  alt={`Menu line ${line}`}
                  src="/profile/line-153.svg"
                />
              ))}
            </div>

            <div className={styles.navItems}>
              {navItems.map((item, index) => (
                <div
                  key={index}
                  className={`${styles.navItem} ${item.isActive ? styles.navItemActive : ""}`}
                >
                  {item.isActive && (
                    <img
                      className={styles.activeIndicator}
                      alt="Active indicator"
                      src="/profile/rectangle-21.svg"
                    />
                  )}
                  <img
                    className={styles.iconSidebar}
                    alt={item.alt}
                    src={item.icon}
                  />
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
