import styles from "./layout.module.css";

import React from "react";

export default function Layout({children}: {
  children: React.ReactNode
}) {

  return (
    <>
      {children}
    </>
  );
}
