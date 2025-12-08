import { Metadata } from 'next';
import RegisterForm from './RegisterForm';

export const metadata: Metadata = {
  title: 'Регистрация - CTokenX | Создайте аккаунт для обмена криптовалют',
  description: 'Зарегистрируйтесь на CTokenX и получите доступ к безопасному обмену криптовалют, выгодным курсам и удобному управлению цифровыми активами. Быстрая регистрация с подтверждением email.',
};

export default function RegisterPage() {
  return <RegisterForm />;
}
