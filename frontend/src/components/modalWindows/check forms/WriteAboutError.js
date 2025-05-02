"use client";

import React from "react";
import Modal from "@/components/modal/Modal";
import ModalWrapper from "@/components/modalWindows/ModalWrapper";
import styles from './WriteUs.module.css'
import Button from "@/components/button/Button"
import TextInput from "@/components/forms/auth-forms/TextInput";
import {useRouter} from "next/navigation";
import Title from "@/components/title/title"

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
                        <Title>
                            <h2 className={styles.title}>{props.title}</h2>
                        </Title>

                        <span className={styles.helptext}><strong>На странице:</strong><p>{props.errorURLPage}</p></span>
                        <span className={styles.helptext}><strong>Найдена ошибка:</strong><p>{props.errorMessage}</p></span>

                        <TextInput
                            label={true}
                            isStar={true}
                            labelText={"Описание ошибки:"}
                            placeholder={"..."}
                        />
                        <TextInput
                            label={true}
                            labelText={"E-mail [по желанию]"}
                            placeholder={"Ваш рабочий e-mail"}
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