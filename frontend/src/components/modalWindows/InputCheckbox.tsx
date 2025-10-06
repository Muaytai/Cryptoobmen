import React from "react";
import styles from "./ModalWindows.module.css";

interface InputCheckboxProps {
    idInput: string;
    nameInput: string;
    valueInput?: string;
    label?: string;
    typeInput?: string;
    checked?: boolean;
    onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void;
}

const InputCheckbox: React.FC<InputCheckboxProps> = ({
    idInput,
    nameInput,
    valueInput,
    label = "",
    typeInput = "checkbox",
    checked = false,
    onChange = () => {}
}) => {
    return (
        <div className={styles.checkBoxWrapper}>
            <input
                type={typeInput}
                id={idInput}
                name={nameInput}
                value={valueInput}
                checked={checked}
                onChange={onChange}
                className={styles.checkBox}
            />
            <label htmlFor={idInput} className={styles.checkBoxLabel}>
                {label}
            </label>
        </div>
    );
};

export default InputCheckbox;