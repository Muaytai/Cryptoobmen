import React from "react";
import Modal from "@/components/modal/Modal";
import ModalWrapper from "@/components/modalWindows/ModalWrapper";  // TODO temporary
import styles from './ThanksForSendData.module.css'
import Button from "@/components/button/Button"
import Title from "@/components/title/title";

const ThanksForSendData = (props) => {

    return (
        <Modal handleClose={props.onHideModule}>
            <ModalWrapper>
                <div className={styles.modalWrapper}>
                    <Title>
                        <h2 className={styles.helptext}>{props.title}</h2>
                    </Title>
                    {/*<h3 className={styles.title}>{props.title}</h3>*/}
                    <span className={styles.helptext}>{props.description}</span>
                    {props.imgGift ? <div className={styles.giftWrapper}><img src="/img/gift/gift.png"  width="250"/></div> : ""}
                    <Button
                        type="primary centering"
                        size="middle"
                        // placeholder="Вставьте ссылку"
                        onClick={props.onHideModule}
                    >
                        <span>{props.buttonText}</span>
                    </Button>
                </div>
            </ModalWrapper>
        </Modal>
    );
};

export default ThanksForSendData;