'use client';

import { useState, useEffect, Suspense, useCallback } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuthStore } from '@/store/useAuthStore';
import { Input } from '@/components/ui/Input';
import styles from './Login.module.css';
import { FaEye, FaEyeSlash, FaGoogle, FaSpinner } from 'react-icons/fa';
import { TbBrandYandex } from 'react-icons/tb';
import { useModal } from "@/utils/modalWindows/generalFunctions";
import WriteAboutError from "@/components/modalWindows/WriteAboutError";

// Компонент, использующий useSearchParams
const LoginFormWithSearchParams = () => {
    const router = useRouter();
    const searchParams = useSearchParams();
    const { login, isLoading, error, setDisableAutoLogin, checkAuthStatus, isAuthenticated, user, socialLogin } = useAuthStore();
    const [credentials, setCredentials] = useState({ email: '', password: '' });
    const [showPassword, setShowPassword] = useState(false);
    const [verificationSuccess, setVerificationSuccess] = useState(false);
    const modalManagerChangePassword = useModal(false);

    // Функция для очистки всех данных аутентификации
    // Обернули в useCallback, чтобы избежать проблем с зависимостями в useEffect
    const clearAllAuthData = useCallback(() => {
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
    }, [setDisableAutoLogin]);

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
        // Попытка подтянуть сессию после социальной авторизации: куки уже выставлены бэкендом
        // Запрашиваем профиль без очистки данных, чтобы сразу показать пользователя
        // Обязательно указываем isLoginProcess=true, чтобы обойти disableAutoLogin
        checkAuthStatus(true).catch(() => {});
    }, [searchParams, setDisableAutoLogin, clearAllAuthData, checkAuthStatus]); // Добавлены корректные зависимости

    // Если пользователь уже аутентифицирован (например, вернулись с соц-логина), уводим со страницы логина
    useEffect(() => {
        console.log('[LoginForm] useEffect для редиректа:', { isAuthenticated, user: !!user, isLoading });
        if (isAuthenticated && user && !isLoading) {
            const redirectParam = searchParams.get('redirect');
            let target = '/';
            if (redirectParam) {
                const decoded = decodeURIComponent(redirectParam);
                target = decoded.startsWith('/') ? decoded : `/${decoded}`;
            }
            console.log('[LoginForm] Редирект после авторизации на:', target);
            
            const timeoutId = setTimeout(() => {
                router.replace(target);
            }, 100);
            return () => clearTimeout(timeoutId);
        }
    }, [isAuthenticated, user, isLoading, router, searchParams]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        
        try {
            await login({
                ...credentials,
                recaptcha_token: undefined
            });
            console.log('[LoginForm] Вход выполнен успешно, данные пользователя загружены');
            
            // Добавляем дополнительную проверку через небольшую задержку для надежности
            setTimeout(() => {
                const currentState = useAuthStore.getState();
                if (currentState.isAuthenticated && currentState.user && !currentState.isLoading) {
                    const redirectParam = searchParams.get('redirect');
                    let target = '/';
                    if (redirectParam) {
                        const decoded = decodeURIComponent(redirectParam);
                        target = decoded.startsWith('/') ? decoded : `/${decoded}`;
                    }
                    console.log('[LoginForm] Дополнительная проверка редиректа после логина на:', target);
                    router.replace(target);
                }
            }, 300);
        } catch (err) {
            console.error('Ошибка входа:', err);
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
        const finalNext = `${frontendUrl}/login`;
        const callback = `${backendUrl}/auth/callback/?next=${encodeURIComponent(finalNext)}`;

        socialLogin();

        window.location.href = `${backendUrl}/accounts/google/login/?process=login&next=${encodeURIComponent(callback)}`;
    };

    const handleYandexLogin = () => {
        const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
        const frontendUrl = process.env.NEXT_PUBLIC_FRONTEND_URL || 'http://localhost:3000';
        const finalNext = `${frontendUrl}/login`;
        const callback = `${backendUrl}/auth/callback/?next=${encodeURIComponent(finalNext)}`;

        socialLogin();

        window.location.href = `${backendUrl}/accounts/yandex/login/?process=login&next=${encodeURIComponent(callback)}`;
    };

    // Проверяем наличие ошибок в URL при загрузке страницы
    useEffect(() => {
        const error = searchParams.get('error');
        if (error === 'auth_failed') {
            console.error('Ошибка авторизации через соцсеть');
        } else if (error === 'server_error') {
            console.error('Ошибка сервера при авторизации');
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
                    <img className={styles.image} src={"/images/chess_mirror.webp"} alt="Chess Mirror" />
                </div>
                <div className={styles.formBox}>
                    <div className={styles.logoWrapper}>
                        <img className={styles.logo} src={"/images/logo.webp"} alt="Logo" />
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
                        {isLoading && (
                            <div className={styles.loadingOverlay}>
                                <div className={styles.loadingMessage}>
                                    <FaSpinner className={styles.spinner} />
                                    <span>Выполняется вход в систему...</span>
                                </div>
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
                            
                            <div className="mb-4" />
                            
                            <div className={styles.linkForgotPassword}>
                                <a 
                                    href="/forgot-password"
                                    onClick={(e) => {
                                        e.preventDefault();
                                        router.push('/forgot-password');
                                    }}
                                    className="text-sm hover:underline cursor-pointer"
                                >
                                    Забыли пароль?
                                </a>
                            </div>
                            <button
                                type="submit"
                                className={styles.submitBtn}
                                disabled={isLoading}
                            >
                                {isLoading ? (
                                    <span className={styles.loadingContent}>
                                        <FaSpinner className={styles.spinner} />
                                        <span>Выполняется вход...</span>
                                    </span>
                                ) : (
                                    'Войти'
                                )}
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
                                        disabled={isLoading}
                                    >
                                        <FaGoogle/> Google
                                    </button>
                                    <button 
                                        type="button" 
                                        className={styles.socialBtn} 
                                        onClick={handleYandexLogin}
                                        disabled={isLoading}
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