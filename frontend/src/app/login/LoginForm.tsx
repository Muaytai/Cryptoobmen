'use client';

import {useState, useEffect, Suspense} from 'react';
import {useRouter, useSearchParams} from 'next/navigation';
import Link from 'next/link';
import {useAuthStore} from '@/store/useAuthStore';
import {Input} from '@/components/ui/Input';
import styles from './Login.module.css';
import {FaEye, FaEyeSlash, FaGoogle} from 'react-icons/fa';
import {TbBrandYandex} from 'react-icons/tb';
import {useModal} from "@/utils/modalWindows/generalFunctions";
import WriteAboutError from "@/components/modalWindows/WriteAboutError";

// Компонент, использующий useSearchParams
const LoginFormWithSearchParams = () => {
    const router = useRouter();
    const searchParams = useSearchParams();
    const {login, isLoading, error, setDisableAutoLogin, setTokens} = useAuthStore();
    const [credentials, setCredentials] = useState({email: '', password: ''});
    const [showPassword, setShowPassword] = useState(false);
    const [loginAttempted, setLoginAttempted] = useState(false);
    const [verificationSuccess, setVerificationSuccess] = useState(false);
    const modalManagerChangePassword = useModal(false);

    // Функция для очистки всех данных аутентификации
    const clearAllAuthData = () => {
        // Очищаем НЕ HttpOnly куки, если они есть и управляются фронтом
        const clientSideCookies = [
            // 'access_token', // HttpOnly, управляется бэкендом
            // 'refresh_token', // HttpOnly, управляется бэкендом
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
        setDisableAutoLogin(true);
    };

    // При монтировании компонента проверяем force_login, verified и токены
    useEffect(() => {
        const forceLogin = searchParams.get('force_login');
        const verified = searchParams.get('verified');
        
        if (forceLogin === 'true') {
            clearAllAuthData();
        } else {
            // Если нет force_login, просто сбрасываем флаг автовхода
            localStorage.removeItem('disableAutoLogin');
            setDisableAutoLogin(false);
        }
        
        // Проверяем, пришли ли мы после успешной верификации email
        if (verified === 'true') {
            setVerificationSuccess(true);
            // Скрываем сообщение через 5 секунд
            setTimeout(() => {
                setVerificationSuccess(false);
            }, 5000);
        }
    }, [searchParams, setDisableAutoLogin]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            setLoginAttempted(true);
            await login(credentials);
            console.log('Вход выполнен успешно');
            // Определяем куда редиректить после успешного входа
            const redirectParam = searchParams.get('redirect');
            const target = redirectParam ? decodeURIComponent(redirectParam) : '/';
            // Используем replace, чтобы не оставлять страницу логина в истории
            router.replace(target);
        } catch (err) {
            console.error('Ошибка входа:', err);
            setLoginAttempted(false);
        }
    };

    const handleLinkToRegister = () => {
        // Очищаем все данные перед переходом
        clearAllAuthData();
        
        // Добавляем force_login=true для предотвращения автоматического входа
        router.push('/register?force_login=true');
    };

    const handleGoogleLogin = () => {
        const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
        const frontendUrl = process.env.NEXT_PUBLIC_FRONTEND_URL || 'http://localhost:3000';
        const next = `${frontendUrl}/login`;
        
        // Очищаем все данные перед авторизацией
        clearAllAuthData();
        
        window.location.href = `${backendUrl}/accounts/google/login/?process=login&next=${encodeURIComponent(next)}`;
    };

    const handleYandexLogin = () => {
        const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
        const frontendUrl = process.env.NEXT_PUBLIC_FRONTEND_URL || 'http://localhost:3000';
        const next = `${frontendUrl}/login`;
        
        // Очищаем все данные перед авторизацией
        clearAllAuthData();
        
        window.location.href = `${backendUrl}/accounts/yandex/login/?process=login&next=${encodeURIComponent(next)}`;
    };

    // Проверяем наличие ошибок в URL при загрузке страницы
    useEffect(() => {
        const error = searchParams.get('error');
        if (error === 'auth_failed') {
            console.error('Ошибка авторизации через соцсеть');
            // Можно показать сообщение пользователю
        } else if (error === 'server_error') {
            console.error('Ошибка сервера при авторизации');
            // Можно показать сообщение пользователю
        }
    }, [searchParams]);

    return (
        <div className="flex min-h-screen items-center justify-center">
            {
                modalManagerChangePassword.isVisible ?
                    <WriteAboutError
                        title={"Вывод средств"}
                        onHideModalWindow={modalManagerChangePassword.close}
                    /> :
                    ""
            }
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
                            <div className={styles.titleLogin}>Вход</div>
                            <div className={styles.titleRegister} onClick={handleLinkToRegister}>Зарегистрироваться
                            </div>
                        </div>
                        
                        {verificationSuccess && (
                            <div className="bg-green-500 text-white p-3 rounded-lg mb-4 text-center">
                                Email успешно подтвержден! Теперь вы можете войти в систему.
                            </div>
                        )}
                        <form className={styles.formStyle} onSubmit={handleSubmit}>
                            <Input
                                type="email"
                                placeholder="Введите ваш электронный адрес"
                                value={credentials.email}
                                onChange={(e) => setCredentials({...credentials, email: e.target.value})}
                                required
                            />
                            <div className="relative">
                                <Input
                                    type={showPassword ? 'text' : 'password'}
                                    placeholder="Введите пароль"
                                    value={credentials.password}
                                    onChange={(e) => setCredentials({...credentials, password: e.target.value})}
                                    required
                                />
                                <button type="button" onClick={() => setShowPassword(v => !v)}
                                        className={styles.eyeButton}>
                                    {showPassword ? <FaEyeSlash/> : <FaEye/>}
                                </button>
                            </div>
                            <div className={styles.linkForgotPassword}>
                                <a className="text-sm  hover:underline">Забыли
                                    пароль?</a>
                            </div>
                            <button
                                type="button"
                                onClick={handleSubmit}
                                className={styles.submitBtn}
                                disabled={isLoading}
                            >
                                {isLoading ? 'Загрузка...' : 'Войти'}
                            </button>
                            {error && <div className="text-red-500 text-sm mt-2">{error}</div>}
                            <div className="flex items-center my-6">
                                <div className="flex-1 h-px bg-[#23233a]"/>
                                <span className="mx-4 text-gray-400 text-sm">или</span>
                                <div className="flex-1 h-px bg-[#23233a]"/>
                            </div>
                            <div className={styles.socialButtonWrapper}>
                                <div className={styles.socialBtns}>
                                    <button 
                                        type="button" 
                                        className={styles.socialBtn} 
                                        onClick={handleGoogleLogin}
                                    >
                                        <FaGoogle/> Google
                                    </button>
                                    <button 
                                        type="button" 
                                        className={styles.socialBtn} 
                                        onClick={handleYandexLogin}
                                    >
                                        <TbBrandYandex/> Яндекс 
                                    </button>
                                </div>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    );
};

// Основной компонент, который оборачивает содержимое в Suspense
export default function LoginForm() {
    return (
        <Suspense fallback={<div className="flex min-h-screen items-center justify-center">Загрузка...</div>}>
            <LoginFormWithSearchParams />
        </Suspense>
    );
}