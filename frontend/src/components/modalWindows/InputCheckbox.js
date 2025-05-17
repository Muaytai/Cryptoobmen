import React from "react";
import styles from "./modalCSS/InputCheckbox.module.css"


const InputCheckbox = ({idInput, nameInput, valueInput, label = "", typeInput = "checkbox", onChange}) => {
    return (
        <div className={styles.checkBoxWrapper}>
            <input
                type={typeInput}
                id={idInput}
                name={nameInput}
                value={valueInput}
                className={styles.checkbox}
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