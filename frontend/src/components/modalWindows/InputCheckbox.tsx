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

<<<<<<< HEAD:frontend/src/components/modalWindows/InputCheckbox.js
const InputCheckbox = ({idInput, nameInput, valueInput, label = "", typeInput = "checkbox", onChange}) => {
=======
const InputCheckbox: React.FC<InputCheckboxProps> = ({
    idInput, 
    nameInput, 
    valueInput, 
    label = "", 
    typeInput = "checkbox", 
    checked = false, 
    onChange = () => {}
}) => {
>>>>>>> 63a7ddfc7c6785d7e614d516eed767386405399d:frontend/src/components/modalWindows/InputCheckbox.tsx
    return (
        <div className={styles.checkBoxWrapper}>
            <input
                type={typeInput}
                id={idInput}
                name={nameInput}
                value={valueInput}
                className={styles.checkbox}
<<<<<<< HEAD:frontend/src/components/modalWindows/InputCheckbox.js
=======
                checked={checked}
>>>>>>> 63a7ddfc7c6785d7e614d516eed767386405399d:frontend/src/components/modalWindows/InputCheckbox.tsx
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