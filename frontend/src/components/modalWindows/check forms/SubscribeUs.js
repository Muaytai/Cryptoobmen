"use client";

import React from "react";
import Modal from "@/components/modal/Modal";
// import Modal from "@/components/modalWindows/Modal"
import ModalWrapper from "@/components/modalWindows/ModalWrapper";  // TODO temporary
import ModalCloseButton from "./components/ModalCloseButton";
import styles from './WriteUs.module.css'
import Button from "@/components/button/Button"
import TextInput from "@/components/forms/auth-forms/TextInput";
import {useRouter} from "next/navigation";

const WriteUs = (props) => {

    /**
     * Отправка данных модального окна
     * **/
    const sendMessage = () => {
        alert("Message должен куда-то отправляться ;)");
        props.closeSendData();
        props.openConfirm();
    }
    const route = useRouter();
    const toUserAgreement = () => {
        route.push("/politic")
    }
    return (
        <Modal handleClose={props.closeSendData}>
            <ModalWrapper>
                <div className={styles.modalWrapper}>
                    <h3 className={styles.title}>{props.title}</h3>
                    <span className={styles.helptext}>Мы не занимаемся рассылкой рекламных сообщений, а так же не передаём контактные данные третьим лицам</span>
                    <TextInput
                        label={true}
                        isStar={true}
                        labelText={"E-mail"}
                        placeholder={"Ваш e-mail"}
                    />
                    <Button
                        type="primary centering"
                        size="middle"
                        placeholder="Отправить"
                        onClick={sendMessage}
                    >
                        <span>Отправить</span>
                    </Button>

                </div>
            </ModalWrapper>
        </Modal>
    );
};

export default WriteUs;