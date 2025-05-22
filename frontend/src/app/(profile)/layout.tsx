import styles from "./layout.module.css";

import React from "react";

import { HeaderProfile } from "./components/headerProfile";
import { SideBar } from "./components/sidebar";

export default function Layout({ children }: { children: React.ReactNode }) {
  
  return (
    <div className={styles.container}>
      <div className={styles.wrapper}>
        <div className={styles.wrapperMain}>
          <HeaderProfile />
          {children}
          <SideBar />
        </div>
      </div>
    </div>
  );
}
