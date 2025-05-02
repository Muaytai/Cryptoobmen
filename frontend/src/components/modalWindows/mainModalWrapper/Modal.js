import React from "react";
import styles from "./Modal.module.css";
import Button from "@/components/button/Button";
import ModalCloseButton from "@/components/modalWindows/components/ModalCloseButton";
import AnimatedWrapper from "@/components/AnimatedWrapper/AnimatedWrapper";

const Modal = ({children, handleClose}) => {
    return (
            <div className={styles.modalWrapper} onClick={handleClose}>
                <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
                    {children}
                    <div className={styles.btnWrapper}>
                        {/*<Button size="small" onClick={handleClose}>X</Button>*/}
                        <ModalCloseButton onHideModule={handleClose}/>
                    </div>
                </div>
            </div>
    );
};

export default Modal;