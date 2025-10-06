import React from "react";
import Modal from "@/components/modal/Modal";
import ModalWrapper from "@/components/modalWindows/ModalWrapper";  // TODO temporary
import ModalWindowButton from "../forms/auth-forms/ModalWindowButton";
import ModalCloseButton from "./components/ModalCloseButton";
import styles from './SendLinkFromVisitor.module.css'
import Button from "@/components/button/Button"
import InputCheckbox from "@/components/modalWindows/components/InputCheckbox";
import TextInput from "@/components/forms/auth-forms/TextInput";

const SendLinkFromVisitor = (props) => {

    /**
     *  Отправляет данные модального окна
     * */
    const sendMessage = () => {
        alert("Message должен куда-то отправляться ;)");
        props.closeModalSendLinkVisitor();
        props.openModalConfirm();
    }
    return (
            <Modal handleClose={props.closeModalSendLinkVisitor}>
                <ModalWrapper>
                    <div className={styles.modalWrapper}>
                        <h1 className={styles.title}>Не нашли, что искали?</h1>
                        <span className={styles.helptext}>Оставьте ссылку на товар, услугу или организацию</span>
                        <div className={styles.inputWrapper}>
                            <InputCheckbox
                                idInput={"service"}
                                nameInput={"group"}
                                valueInput={"service"}
                                label={"Услуга"}
                                typeInput={"radio"}
                            />

                            <InputCheckbox
                                idInput={"organization"}
                                nameInput={"group"}
                                valueInput={"organization"}
                                label={"Организация"}
                                typeInput={"radio"}
                            />
                            <InputCheckbox
                                idInput={"product"}
                                nameInput={"group"}
                                valueInput={"product"}
                                label={"Товар"}
                                typeInput={"radio"}
                            />
                        </div>
                        <TextInput
                            label={true}
                            isStar={true}
                            labelText={"Ссылка"}
                            placeholder={"Вставьте ссылку"}
                        />
                        <Button
                            type="primary centering"
                            size="middle"
                            placeholder="Вставьте ссылку"
                            onClick={sendMessage}
                        >
                            <span>Отправить</span>
                        </Button>
                    </div>
                </ModalWrapper>
            </Modal>
    );
};

export default SendLinkFromVisitor;