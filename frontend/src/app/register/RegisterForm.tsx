'use client';

import {useState} from 'react';
import Link from 'next/link';
import {useRouter} from 'next/navigation';
import {useAuthStore} from '@/store/useAuthStore';
import {FaEye, FaEyeSlash, FaGoogle, FaApple} from 'react-icons/fa';
import styles from './Register.module.css';
import {Input} from "@/components/ui/Input";
import InputCheckbox from "@/components/modalWindows/InputCheckbox";

export default function RegisterForm() {
    const router = useRouter();
    const {register, error, clearError, isLoading} = useAuthStore();
    const [formData, setFormData] = useState({
        username: '',
        email: '',
        password: '',
        confirmPassword: '',
        agree: false,
    });
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirm, setShowConfirm] = useState(false);
    const [passwordError, setPasswordError] = useState('');
    const [networkError, setNetworkError] = useState('');
    const [registrationMessage, setRegistrationMessage] = useState('');

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const {name, value, type, checked} = e.target;
        setFormData((prev) => ({
            ...prev,
            [name]: type === 'checkbox' ? checked : value,
        }));
        if (name === 'confirmPassword' || name === 'password') {
            if (
                (name === 'confirmPassword' && value !== formData.password) ||
                (name === 'password' && value !== formData.confirmPassword && formData.confirmPassword !== '')
            ) {
                setPasswordError('Пароли не совпадают');
            } else {
                setPasswordError('');
            }
        }
        if (error) clearError();
        if (networkError) setNetworkError('');
        setRegistrationMessage('');
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (formData.password !== formData.confirmPassword) {
            setPasswordError('Пароли не совпадают');
            return;
        }
        if (!formData.agree) {
            setPasswordError('Необходимо согласиться с условиями');
            return;
        }

        // Сбрасываем все ошибки перед отправкой
        setPasswordError('');
        setNetworkError('');
        setRegistrationMessage('');

        try {
            console.log('Отправка запроса на регистрацию...');
            await register({
                email: formData.email,
                username: formData.username,
                password1: formData.password,
                password2: formData.confirmPassword,
            });

            // console.log('Регистрация успешна, перенаправление на дашборд');
            // router.push('/dashboard'); // Убираем автоматический редирект
            setRegistrationMessage('Регистрация почти завершена! Пожалуйста, проверьте вашу почту и перейдите по ссылке для подтверждения email.');

        } catch (err) {
            console.error('Ошибка регистрации:', err);
            // Проверяем, является ли ошибка сетевой
            if (err instanceof Error) {
                if (err.message.includes('Failed to fetch')) {
                    setNetworkError('Ошибка связи с сервером. Убедитесь, что сервер Django запущен и доступен.');
                } else if (err.message.includes('Unexpected end of JSON input')) {
                    setNetworkError('Сервер вернул некорректный ответ. Возможно, проблема с настройками Django или Next.js');
                } else if (err.message.includes('сервер вернул пустой ответ')) {
                    setNetworkError('Сервер вернул пустой ответ. Проверьте настройки Django и логи сервера.');
                }
            }
            // Другие ошибки обрабатываются в useAuthStore и отображаются через error
        }
    };


    const handleLinkToLogin = () => {
        router.push("/login");
    }
    return (
        <div className="flex min-h-screen items-center justify-center">
            <div className={styles.mainFormWrapper}>
                <div className={styles.imageWrapper}>
                    <img className={styles.image} src={"/images/chess_mirror.png"}/>
                </div>
                <div className={styles.formBox}>
                    <div className={styles.logoWrapper}>
                        <img className={styles.logo} src={"/images/logo.png"}/>

                    </div>

                    <div className={styles.formBoxWrapper}>
                        <div className={styles.titleWrapper}>
                            <div className={styles.titleLogin} onClick={handleLinkToLogin}>Вход</div>
                            <div className={styles.titleRegister}>Зарегистрироваться
                            </div>

                        </div>
                        <form className={styles.formStyle} onSubmit={handleSubmit}>
                            <input
                                type="text"
                                name="username"
                                placeholder="Придумайте ваш ник"
                                value={formData.username}
                                onChange={handleChange}
                                required
                                className={styles.input}
                            />
                            <input
                                type="email"
                                name="email"
                                placeholder="Введите ваш электронный адрес или телефон"
                                value={formData.email}
                                onChange={handleChange}
                                required
                                className={styles.input}
                            />
                            <div className={styles.inputWrapper}>
                                <input
                                    type={showPassword ? 'text' : 'password'}
                                    name="password"
                                    placeholder="Придумайте пароль"
                                    value={formData.password}
                                    onChange={handleChange}
                                    required
                                    className={styles.input}
                                />
                                <button
                                    type="button"
                                    className={styles.eyeButton}
                                    onClick={() => setShowPassword((v) => !v)}
                                    tabIndex={-1}
                                >
                                    {showPassword ? <FaEyeSlash/> : <FaEye/>}
                                </button>
                            </div>
                            <div className={styles.inputWrapper}>
                                <input
                                    type={showConfirm ? 'text' : 'password'}
                                    name="confirmPassword"
                                    placeholder="Повторите пароль"
                                    value={formData.confirmPassword}
                                    onChange={handleChange}
                                    required
                                    className={styles.input}
                                />
                                <button
                                    type="button"
                                    className={styles.eyeButton}
                                    onClick={() => setShowConfirm((v) => !v)}
                                    tabIndex={-1}
                                >
                                    {showConfirm ? <FaEyeSlash/> : <FaEye/>}
                                </button>
                            </div>
                            <div className={styles.checkboxRow}>
                                <InputCheckbox
                                    idInput={"agree"}
                                    nameInput={"agree"}
<<<<<<< HEAD
                                    valueInput={"true"}
                                    onChange={handleChange}
=======
                                    valueInput={"agree"}
                                    checked={formData.agree}
                                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                                        setFormData((prev) => ({
                                            ...prev,
                                            agree: e.target.checked
                                        }));
                                    }}
>>>>>>> 63a7ddfc7c6785d7e614d516eed767386405399d
                                />
                                <span className={styles.agreeText}>
              Я соглашаюсь с <Link href="/terms" className={styles.link}>Условиями использования</Link> и <Link
                                    href="/privacy" className={styles.link}>Политикой конфиденциальности</Link>
            </span>
                            </div>
                            {(error || passwordError || networkError) && (
                                <p className={styles.error}>{error || passwordError || networkError}</p>
                            )}
                            {registrationMessage && (
                                <p className={styles.successMessage}>{registrationMessage}</p>
                            )}
                            <button
                                type="submit"
                                className={styles.submitBtn}
                                disabled={isLoading}
                            >
                                {isLoading ? 'Загрузка...' : 'Зарегистрироваться'}
                            </button>

                        </form>
                    </div>
                </div>
            </div>
        </div>
    );
}
