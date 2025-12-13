'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { Input } from '@/components/ui/Input';
import api from '@/lib/api/fetch';
import styles from './ResetPasswordConfirm.module.css';
import { FaEye, FaEyeSlash } from 'react-icons/fa';

export default function ResetPasswordConfirmPageClient() {
    const router = useRouter();
    const params = useParams();
    const uidb64 = params?.uidb64 as string;
    const token = params?.token as string;
    
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [successMessage, setSuccessMessage] = useState('');

    useEffect(() => {
        if (!uidb64 || !token) {
            setError('Некорректная ссылка для восстановления пароля');
        }
    }, [uidb64, token]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setSuccessMessage('');

        if (!password || !confirmPassword) {
            setError('Заполните все поля');
            return;
        }

        if (password !== confirmPassword) {
            setError('Пароли не совпадают');
            return;
        }

        if (password.length < 8) {
            setError('Пароль должен содержать не менее 8 символов');
            return;
        }

        setIsLoading(true);
        try {
            await api.post(`/auth/password/reset/confirm/${uidb64}/${token}/`, {
                new_password1: password,
                new_password2: confirmPassword,
            });
            
            setSuccessMessage('Пароль успешно изменен! Вы будете перенаправлены на страницу входа...');
            
            setTimeout(() => {
                router.push('/login');
            }, 2000);
        } catch (err: any) {
            console.error('Ошибка сброса пароля:', err);
            if (err instanceof Error) {
                setError(err.message || 'Произошла ошибка при сбросе пароля. Возможно, ссылка устарела или недействительна.');
            } else {
                setError('Произошла ошибка при сбросе пароля. Возможно, ссылка устарела или недействительна.');
            }
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex min-h-screen items-center justify-center">
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
                            <h2 className={styles.title}>Введите новый пароль</h2>
                        </div>
                        
                        {successMessage && (
                            <div className={styles.successMessage}>
                                {successMessage}
                            </div>
                        )}
                        
                        <form className={styles.formStyle} onSubmit={handleSubmit}>
                            <p className={styles.description}>
                                Введите новый пароль для вашего аккаунта.
                            </p>
                            
                            <div className={styles.inputWrapper}>
                                <Input
                                    type={showPassword ? 'text' : 'password'}
                                    placeholder="Новый пароль"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    required
                                    disabled={isLoading}
                                />
                                <button 
                                    type="button" 
                                    onClick={() => setShowPassword(v => !v)}
                                    className={styles.eyeButton}
                                >
                                    {showPassword ? <FaEyeSlash/> : <FaEye/>}
                                </button>
                            </div>
                            
                            <div className={styles.inputWrapper}>
                                <Input
                                    type={showConfirmPassword ? 'text' : 'password'}
                                    placeholder="Подтвердите новый пароль"
                                    value={confirmPassword}
                                    onChange={(e) => setConfirmPassword(e.target.value)}
                                    required
                                    disabled={isLoading}
                                />
                                <button 
                                    type="button" 
                                    onClick={() => setShowConfirmPassword(v => !v)}
                                    className={styles.eyeButton}
                                >
                                    {showConfirmPassword ? <FaEyeSlash/> : <FaEye/>}
                                </button>
                            </div>
                            
                            {error && (
                                <div className={styles.error}>{error}</div>
                            )}
                            
                            <button
                                type="submit"
                                className={styles.submitBtn}
                                disabled={isLoading || !uidb64 || !token}
                            >
                                {isLoading ? 'Сохранение...' : 'Изменить пароль'}
                            </button>
                            
                            <div className={styles.backLink}>
                                <a 
                                    href="#" 
                                    onClick={(e) => {
                                        e.preventDefault();
                                        router.push('/login');
                                    }}
                                    className={styles.link}
                                >
                                    ← Вернуться к входу
                                </a>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    );
}

