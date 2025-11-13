import styles from "./ModalCloseButton.module.css";

const ModalCloseButton = (props) => {
    return (
        <div>
            <span className={styles.closeButton} onClick={props.onHideModule}>
                &times;
            </span>
        </div>
    );
};

export default ModalCloseButton;
