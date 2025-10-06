import {useState} from "react";


//
// /**
//  * открывает модальное окно. Возвращает функцию, которую нужно вызвать
//  * */
// export const openAnyModal = (setIsVisible) => {
//     // return () => setIsVisible(true);
//     setIsVisible(true);
// };
//
// /**
//  * закрывает модальное окно. Возвращает функцию, которую нужно вызвать
//  * */
// export const closeAnyModal = (setIsVisible) => {
//     // return () => setIsVisible(false);
//     setIsVisible(false);
// };
//

/**
 * Хук управляет открытием и закрытием модальных окон.
 * Возвращает функцию, которую нужно вызвать
 * */
export const useModal = (initialState = false, checkAuth=true) => {
    const [isVisible, setIsVisible] = useState(initialState);

    const open = () => {setIsVisible(true)};
    const close = () => {setIsVisible(false)};

    return {
        isVisible,
        open,
        close
    }
}