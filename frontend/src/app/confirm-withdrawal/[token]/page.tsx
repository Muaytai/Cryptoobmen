'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';

// Простой компонент для отображения состояния загрузки
const LoadingSpinner = () => (
    <div className="spinner">
        <style jsx>{`
            .spinner {
                border: 4px solid rgba(0, 0, 0, 0.1);
                width: 36px;
                height: 36px;
                border-radius: 50%;
                border-left-color: #09f;
                animation: spin 1s ease infinite;
                margin: 20px auto;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        `}</style>
    </div>
);

export default function ConfirmWithdrawalPage() {
    const params = useParams();
    const token = params.token as string;

    const [isLoading, setIsLoading] = useState(true);
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');

    useEffect(() => {
        if (!token) {
            setError('Токен подтверждения не найден.');
            setIsLoading(false);
            return;
        }

        const confirmWithdrawal = async () => {
            setIsLoading(true);
            setError('');
            setMessage('');

            try {
                // URL вашего бэкенда
                const apiUrl = `${process.env.NEXT_PUBLIC_API_URL}/transactions/withdrawals/confirm/${token}/`;
                const response = await fetch(apiUrl, {
                    method: 'GET',
                });

                if (!response.ok) {
                    // Попытаемся прочитать тело ответа как текст, если это не JSON
                    const errorText = await response.text();
                    try {
                        // Может быть, это все-таки JSON с ошибкой
                        const errorJson = JSON.parse(errorText) as { error?: string; detail?: string };
                        throw new Error(errorJson.error || errorJson.detail || 'Произошла неизвестная ошибка.');
                    } catch {
                        // Если это не JSON, показываем как текст (может быть HTML)
                        // В реальном приложении здесь лучше показать общую ошибку, а не HTML
                        throw new Error('Ошибка сервера. Пожалуйста, попробуйте позже.');
                    }
                }

                const data = await response.json();
                setMessage(data.message || 'Вывод успешно подтвержден.');

            } catch (err: unknown) {
                const message = err instanceof Error ? err.message : String(err);
                setError(message);
            } finally {
                setIsLoading(false);
            }
        };

        confirmWithdrawal();
    }, [token]);

    return (
        <div className="container mx-auto mt-10 p-4 text-center max-w-md">
            <div className="bg-white shadow-md rounded-lg p-8">
                <h1 className="text-2xl font-bold mb-4">Подтверждение вывода средств</h1>
                
                {isLoading && (
                    <div>
                        <p>Пожалуйста, подождите, мы обрабатываем ваш запрос...</p>
                        <LoadingSpinner />
                    </div>
                )}

                {error && (
                    <div className="text-red-500 bg-red-100 border border-red-400 rounded p-4">
                        <h2 className="font-bold">Ошибка!</h2>
                        <p>{error}</p>
                    </div>
                )}

                {message && (
                    <div className="text-green-700 bg-green-100 border border-green-400 rounded p-4">
                        <h2 className="font-bold">Успешно!</h2>
                        <p>{message}</p>
                    </div>
                )}

                <div className="mt-6">
                    <Link href="/" className="text-blue-500 hover:underline">
                        Вернуться на главную страницу
                    </Link>
                </div>
            </div>
        </div>
    );
}
