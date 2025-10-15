"use client";

import React, {useEffect, useRef} from "react";
import styles from "./modal.module.css";
import Image from "next/image";
import {clsx} from "clsx";

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
}

export const Modal = ({isOpen, onClose, title, children}: ModalProps) => {
  const modalRef = useRef<HTMLDivElement>(null);

  // Закрытие при клике вне модалки
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (modalRef.current && !modalRef.current.contains(e.target as Node)) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen, onClose]);

  // Блокировка скролла
  useEffect(() => {
    document.body.style.overflow = isOpen ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className={styles.overlay}>
      <div className={clsx(styles.modal, "bg-card")} ref={modalRef}>
        <div className={styles.header}>
          <div className={styles.closeWrap}>
          <button
            onClick={onClose}
            className={styles.close}
            aria-label="Закрыть модальное окно"
            title="Закрыть"
          >
            <Image src="/images/profile/close.svg" alt="close" width={40} height={40}/>
          </button>
          </div>
          {title && <h2>{title}</h2>}
        </div>
        <div className={styles.content}>{children}</div>
      </div>
    </div>
  );
};
