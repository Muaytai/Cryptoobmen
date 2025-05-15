'use client';

import {useState, useEffect} from 'react';
import {useRouter, useSearchParams} from 'next/navigation';
import Link from 'next/link';
import {useAuthStore} from '@/store/useAuthStore';
import {Input} from '@/components/ui/Input';
import styles from './Login.module.css';
import {FaEye, FaEyeSlash, FaGoogle, FaApple} from 'react-icons/fa';
import {TbBrandYandex} from 'react-icons/tb';
import {useModal} from "@/utils/modalWindows/generalFunctions";
import WriteAboutError from "@/components/modalWindows/WriteAboutError";


export default function LoginForm() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const {login, isLoading, error, isAuthenticated, setDisableAutoLogin} = useAuthStore();
    const [credentials, setCredentials] = useState({email: '', password: ''});
    const [showPassword, setShowPassword] = useState(false);
    const [redirectPath, setRedirectPath] = useState('/profile');
    const [loginAttempted, setLoginAttempted] = useState(false);

    // При монтировании компонента сбрасываем флаг блокировки автовхода
    useEffect(() => {
        // Очищаем куку disableAutoLogin при загрузке страницы входа
        document.cookie = 'disableAutoLogin=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
        localStorage.removeItem('disableAutoLogin');
        setDisableAutoLogin(false);
    }, [setDisableAutoLogin]);

    // Получаем параметр redirect из URL
    useEffect(() => {
        const redirect = searchParams.get('redirect');
        if (redirect) {
            // Удаляем лишние слэши и проверяем валидность пути
            const sanitizedRedirect = redirect.replace(/^\/+|\/+$/g, '');
            if (sanitizedRedirect) {
                setRedirectPath(`/${sanitizedRedirect}`);
            } else {
                setRedirectPath('/profile');
            }
        } else {
            setRedirectPath('/profile');
        }
    }, [searchParams]);

    // Эффект, который следит за состоянием авторизации и выполняет перенаправление
    useEffect(() => {
        if (isAuthenticated && loginAttempted) {
            console.log('Пользователь авторизован, перенаправление на:', redirectPath);
            
            // Убеждаемся, что флаг disableAutoLogin точно снят
            document.cookie = 'disableAutoLogin=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
            localStorage.removeItem('disableAutoLogin');
            
            // Перенаправляем на нужную страницу
            router.push(redirectPath);
        }
    }, [isAuthenticated, loginAttempted, redirectPath, router]);


    const modalManagerChangePassword = useModal(false);


    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            setLoginAttempted(true);
            
            // Убеждаемся, что флаг disableAutoLogin точно снят перед входом
            document.cookie = 'disableAutoLogin=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
            localStorage.removeItem('disableAutoLogin');
            setDisableAutoLogin(false);
            
            await login(credentials);
            console.log('Вход выполнен успешно, готовимся к перенаправлению в:', redirectPath);
            
            // Перенаправление происходит в useEffect выше, после обновления состояния isAuthenticated
        } catch (err) {
            console.error('Ошибка входа:', err);
            setLoginAttempted(false);
        }
    };

    const handleLinkToRegister = () => {
        // Явно очищаем cookie disableAutoLogin перед переходом
        document.cookie = 'disableAutoLogin=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
        localStorage.removeItem('disableAutoLogin');
        
        // Используем window.location вместо router.push для полного обновления страницы
        window.location.href = '/register';
    }

    const handleGoogleLogin = () => {
        // Убедитесь, что этот URL соответствует вашему backend urls.py для allauth google login
        window.location.href = 'http://localhost:8000/accounts/google/login/';
    };

    const handleYandexLogin = () => {
        // URL для инициации входа через Яндекс на бэкенде
        window.location.href = 'http://localhost:8000/accounts/yandex/login/';
    };

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
                                        // className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-primary">
                                        className={styles.eyeButton}>
                                    {showPassword ? <FaEyeSlash/> : <FaEye/>}
                                </button>
                            </div>
                            <div className={styles.linkForgotPassword}>
                                {/*<Link href="/forgot-password" className="text-sm  hover:underline">Забыли*/}
                                {/*    пароль?</Link>*/}
                                <a className="text-sm  hover:underline">Забыли
                                    пароль?</a>

                            </div>
                            {/*<button type="submit" className="button w-full mt-2" disabled={isLoading}>*/}
                            {/*    {isLoading ? 'Вход...' : 'Войти'}*/}
                            {/*</button>*/}
                            <button
                                type="submit"
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
                                {/*<button type="button"*/}
                                {/*        className="flex-1 button-outline flex items-center justify-center gap-2">*/}
                                {/*    <FaGoogle/> Google*/}
                                {/*</button>*/}
                                {/*<button type="button"*/}
                                {/*        className="flex-1 button-outline flex items-center justify-center gap-2">*/}
                                {/*    <FaApple/> Apple*/}
                                {/*</button>*/}
                                {/* Соцсети */}

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
                            {/*<div className="mt-4 text-center">*/}
                            {/*    Нет аккаунта? <Link href="/register" className={styles.link}>Зарегистрироваться</Link>*/}
                            {/*</div>*/}
                        </form>
                    </div>
                </div>
            </div>
        </div>
    );
}