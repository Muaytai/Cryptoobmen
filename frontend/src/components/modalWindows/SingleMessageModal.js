import Modal from "./Modal";
import React from "react";

const SingleMessageWindow = (props) => {


    return (
        <Modal onHideModule={props.onHideModule}>
            <p>{props.text}</p>
            <button onClick={props.onHideModule}>Close</button>
        </Modal>
    );
};

export default SingleMessageWindow;