"use client";

import React, {useState} from "react";
import Modal from "./mainModalWrapper/Modal";
import ModalWrapper from "./mainModalWrapper/ModalWrapper";
import styles from './modalCSS/WriteAboutError.module.css'
import Button from "./modalComponents/Button"
import {Input} from '@/components/ui/Input';
import {useRouter} from "next/navigation";
import Title from "./modalComponents/title"

const WriteUs = (props) => {

    /**
     * Отправка данных модального окна
     * **/
    const sendMessage = () => {
        alert("Message должен куда-то отправляться ;)");
        props.closeSendData();
        props.openConfirm();
    }
    const [credentials, setCredentials] = useState({username: '', password: ''});
    const route = useRouter();
    const toUserAgreement = () => {
        route.push("/politic")
    }
    return (
        <Modal onHideModalWindow={props.onHideModalWindow}>
            {/*<ModalWrapper>*/}
            <div className={styles.modalWrapper}>
                <Title>
                    <h2 className={styles.title}>{props.title}</h2>
                </Title>

                <Input
                    type="text"
                    label="Счёт списания:"
                    placeholder="Партнерский (0.0 USDT)"
                    value={credentials.username}
                    onChange={(e) => setCredentials({...credentials, username: e.target.value})}
                    required
                />
                <Input
                    type="text"
                    label="Реквизит(переделать на select):"
                    placeholder="Выберите ваш реквизит"
                    value={credentials.username}
                    onChange={(e) => setCredentials({...credentials, username: e.target.value})}
                    required
                />
                <Input
                    type="text"
                    label="Сумма:"
                    placeholder="USDT"
                    value={credentials.username}
                    onChange={(e) => setCredentials({...credentials, username: e.target.value})}
                    required
                />
                <span className={styles.helptext}><strong>Минимальная сумма вывода - 5 USDT:</strong><p>{props.errorURLPage}</p></span>

                <span className={styles.helptext}><strong>Максимальная сумма вывода - 100.000 USDT</strong><p>{props.errorURLPage}</p></span>

                <Button
                    type="primary centering"
                    size="small"
                    placeholder="Отправить"
                    onClick={sendMessage}
                >
                    <span>Отправить</span>
                </Button>
                <span className={styles.helptext}><strong>Вывод производится в течении 5 дней</strong><p>{props.errorURLPage}</p></span>

                <span className={styles.helptext}><strong>Комиссия сервиса на вывод - 5%</strong><p>{props.errorURLPage}</p></span>


            </div>
            {/*</ModalWrapper>*/}
        </Modal>
    );
};

export default WriteUs;