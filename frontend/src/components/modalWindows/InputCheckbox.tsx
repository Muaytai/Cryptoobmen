import React from "react";
import styles from "./modalCSS/InputCheckbox.module.css"

interface InputCheckboxProps {
    idInput: string;
    nameInput: string;
    valueInput: string;
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
                className={styles.checkbox}
                checked={checked}
                onChange={onChange}
            />
            <label
                className={styles.label}
                htmlFor={idInput}>
                {label}
            </label>
        </div>
    );
};

export default InputCheckbox;