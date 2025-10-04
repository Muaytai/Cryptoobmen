"use client";

import { InputHTMLAttributes, forwardRef } from "react";
import { clsx } from "clsx";
import styles from "./formField.module.css";

interface Props extends InputHTMLAttributes<HTMLInputElement> {
  error?: string;
  label: string;
  required?: boolean;
  disabled?: boolean;
}

export const FormInput = forwardRef<HTMLInputElement, Props>(
  ({ label, error, required, disabled, ...rest }, ref) => (
    <label className={styles.label}>
      <span className="text-subcard-text/70">
        {required && "*"}
        {label}
      </span>
      <input
        disabled={disabled}
        {...rest}
        ref={ref}
        className={clsx(styles.input, error && styles.error, disabled && styles.disabled, disabled && "bg-subcard text-subcard-text/70")}
      />
      {error && <div className={styles.helper}>{error}</div>}
    </label>
  )
);

FormInput.displayName = "FormInput";
