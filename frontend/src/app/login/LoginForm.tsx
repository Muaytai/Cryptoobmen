'use client';

import {useState} from 'react';
import {useRouter} from 'next/navigation';
import Link from 'next/link';
import {useAuthStore} from '@/store/useAuthStore';
import {Input} from '@/components/ui/Input';
import {authConfig} from '@/config/auth';
import styles from './Login.module.css';
import {FaEye, FaEyeSlash, FaGoogle, FaApple} from 'react-icons/fa';

export default function LoginForm() {
    const router = useRouter();
    const {login, isLoading, error} = useAuthStore();
    const [credentials, setCredentials] = useState({username: '', password: ''});
    const [showPassword, setShowPassword] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await login(credentials);
            router.push('/dashboard');
        } catch (err) {
            console.error('Ошибка входа:', err);
        }
    };

    const handleLinkToRegister = () => {
        router.push("/register");
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
                            <div className={styles.titleLogin}>Вход</div>
                            <div className={styles.titleRegister} onClick={handleLinkToRegister}>Зарегистрироваться
                            </div>

                        </div>
                        <form className={styles.formStyle} onSubmit={handleSubmit}>
                            <Input
                                type="text"
                                placeholder="Введите ваш электронный адрес или телефон"
                                value={credentials.username}
                                onChange={(e) => setCredentials({...credentials, username: e.target.value})}
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
                                <Link href="/forgot-password" className="text-sm  hover:underline">Забыли
                                    пароль?</Link>
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
                                    <button type="button" className={styles.socialBtn}>
                                        <FaGoogle/> Google
                                    </button>
                                    <button type="button" className={styles.socialBtn}>
                                        <FaApple/> Apple
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