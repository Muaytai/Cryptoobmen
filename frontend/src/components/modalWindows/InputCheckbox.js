import React from "react";
import styles from "./modalCSS/InputCheckbox.module.css"


const InputCheckbox = ({idInput, nameInput, valueInput, label = "", typeInput = "checkbox"}) => {
    return (
        <div className={styles.checkBoxWrapper}>
            <input
                type={typeInput}
                id={idInput}
                name={nameInput}
                value={valueInput}
                className={styles.checkbox}
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