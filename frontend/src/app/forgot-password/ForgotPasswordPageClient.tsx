'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Input } from '@/components/ui/Input';
import api from '@/lib/api/fetch';
import styles from './ForgotPassword.module.css';

export default function ForgotPasswordPageClient() {
    const router = useRouter();
    const [email, setEmail] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [successMessage, setSuccessMessage] = useState('');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setSuccessMessage('');
        
        if (!email) {
            setError('Введите ваш email');
            return;
        }

        setIsLoading(true);
        try {
            await api.post('/auth/password/reset/', { email });
            setSuccessMessage('Инструкции по восстановлению пароля отправлены на ваш email. Проверьте почту.');
            setEmail('');
        } catch (err: any) {
            console.error('Ошибка восстановления пароля:', err);
            if (err instanceof Error) {
                setError(err.message || 'Произошла ошибка при отправке запроса на восстановление пароля');
            } else {
                setError('Произошла ошибка при отправке запроса на восстановление пароля');
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
                            <h2 className={styles.title}>Восстановление пароля</h2>
                        </div>
                        
                        {successMessage && (
                            <div className={styles.successMessage}>
                                {successMessage}
                            </div>
                        )}
                        
                        <form className={styles.formStyle} onSubmit={handleSubmit}>
                            <p className={styles.description}>
                                Введите ваш email, и мы отправим вам инструкции по восстановлению пароля.
                            </p>
                            
                            <Input
                                type="email"
                                placeholder="Введите ваш электронный адрес"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                                disabled={isLoading}
                            />
                            
                            {error && (
                                <div className={styles.error}>{error}</div>
                            )}
                            
                            <button
                                type="submit"
                                className={styles.submitBtn}
                                disabled={isLoading}
                            >
                                {isLoading ? 'Отправка...' : 'Отправить'}
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

