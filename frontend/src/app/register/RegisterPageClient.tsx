"use client";

import {useState} from 'react';
import Link from 'next/link';
import {useRouter} from 'next/navigation';
import {useAuthStore} from '@/store/useAuthStore';
import {FaEye, FaEyeSlash, FaGoogle, FaApple} from 'react-icons/fa';
import styles from './Register.module.css';
import {Input} from "@/components/ui/Input";
import InputCheckbox from "@/components/modalWindows/InputCheckbox";
import ReCaptcha from '@/components/ReCaptcha';

export default function RegisterPageClient() {
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
    const [recaptchaToken, setRecaptchaToken] = useState('');

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
        
        // Проверяем наличие токена reCAPTCHA
        if (!recaptchaToken) {
            setPasswordError('Пожалуйста, дождитесь проверки reCAPTCHA');
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
                recaptcha_token: recaptchaToken,
            });

            setRegistrationMessage('Регистрация успешно завершена! Пожалуйста, проверьте вашу почту для подтверждения email. После подтверждения вы сможете войти в систему.');

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
                else if (err.message.includes('')) {
                    setNetworkError('Пользователь с таким email уже существует.');
                }
            }
            // Другие ошибки обрабатываются в useAuthStore и отображаются через error
        }
    };

    // Функция для очистки всех данных аутентификации
    const clearAllAuthData = () => {
        // Очищаем НЕ HttpOnly куки, если они есть и управляются фронтом
        const clientSideCookies = [
            // 'access_token',
            // 'refresh_token',
            // 'sessionid',
            // 'dj_session_id',
            // 'csrftoken',
            // 'auth_token',
            'next_hmr_refresh_hash' // Пример клиентской куки
        ];

        clientSideCookies.forEach(cookie => {
            document.cookie = `${cookie}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=localhost; samesite=lax`;
            document.cookie = `${cookie}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; samesite=lax`;
            document.cookie = `${cookie}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`; // Добавлено для большей надежности
        });

        // Очищаем localStorage и sessionStorage
        localStorage.removeItem('user');
        localStorage.removeItem('auth-storage');
        // localStorage.removeItem('access_token');
        // localStorage.removeItem('refresh_token');
        // sessionStorage.clear(); // Если используется

        // Устанавливаем флаг блокировки автовхода
        localStorage.setItem('disableAutoLogin', 'true');
    };

    const handleLinkToLogin = () => {
        // Очищаем все данные перед переходом
        clearAllAuthData();
        
        // Добавляем force_login=true для предотвращения автоматического входа
        router.push('/login?force_login=true');
    };

    return (
        <div className="flex min-h-screen items-center justify-center">
            <div className={styles.mainFormWrapper}>
                <div className={styles.imageWrapper}>
                    <img className={styles.image} src={"/images/chess_mirror.webp"}/>
                </div>
                <div className={styles.formBox}>
                    <div className={styles.logoWrapper}>
                        <img className={styles.logo} src={"/images/logo.webp"}/>

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
                            
                            {/* Компонент reCAPTCHA */}
                            <div className="mb-4">
                                <ReCaptcha
                                    siteKey={process.env.NEXT_PUBLIC_RECAPTCHA_SITE_KEY || ''}
                                    onVerify={setRecaptchaToken}
                                    action="register"
                                />
                            </div>
                            
                            <div className={styles.checkboxRow}>
                                <InputCheckbox
                                    idInput="agree"
                                    nameInput="agree"
                                    valueInput="agree"
                                    checked={formData.agree}
                                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                                        setFormData((prev) => ({
                                            ...prev,
                                            agree: e.target.checked
                                        }));
                                    }}
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
                                disabled={isLoading || !recaptchaToken}
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

