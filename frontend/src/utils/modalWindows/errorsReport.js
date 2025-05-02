/**
 * Функция для получения выделенного текста
 * @returns {*|string}
 */
export function getSelectedText() {
    if (window.getSelection) {
        return window.getSelection().toString();
    } else if (document.selection && document.selection.type !== "Control") {
        return document.selection.createRange().text;
    }
    return "";
}

/**
 * Отображение модального окна с выделенным текстом
 * @param selectedText
 */
export function showReportModal(selectedText) {
    // const modal = document.getElementById("error-report-modal");
    // const selectedTextElement = document.getElementById("selected-text");
    if (selectedText.trim() === "") {
        alert("Пожалуйста, выделите текст перед тем, как сообщить об ошибке.");
        return;
    }

    // Показываем модальное окно
    // modal.style.display = "block";
    // selectedTextElement.textContent = selectedText;

    // // Обработка кнопок модального окна
    // document.getElementById("send-error-btn").addEventListener("click", () => {
    //     alert(`Ошибка отправлена! Выделенный текст: "${selectedText}"`);
    //     // modal.style.display = "none"; // Скрываем модальное окно
    // });
    //
    // document.getElementById("cancel-error-btn").addEventListener("click", () => {
    //     // modal.style.display = "none"; // Скрываем модальное окно
    // });
}