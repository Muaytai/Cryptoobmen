import React from "react";
import styles from "./Modal.module.css";
import Button from "@/components/modalWindows/modalComponents/Button";
import ModalCloseButton from "./ModalCloseButton";
// import AnimatedWrapper from "@/components/AnimatedWrapper/AnimatedWrapper";

const Modal = ({children, onHideModalWindow}) => {
    return (
            <div className={styles.modalWrapper} onClick={onHideModalWindow}>
                <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
                    {children}
                    <div className={styles.btnWrapper}>
                        {/*<Button size="small" onClick={handleClose}>X</Button>*/}
                        <ModalCloseButton onHideModule={onHideModalWindow}/>
                    </div>
                </div>
            </div>
    );
};

export default Modal;