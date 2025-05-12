# Cryptoobmen Frontend

## Локальная разработка

### Запуск проекта локально

```powershell
# Установка зависимостей
cd frontend
npm install

# Запуск в режиме разработки
npm run dev
```

### Запуск через Docker

```powershell
# Запуск всех контейнеров (frontend, backend, postgres, redis)
cd C:\путь\к\проекту\Cryptoobmen
.\docker\local\start-local.ps1

# Остановка контейнеров
docker-compose -f .\docker\local\docker-compose.local.yml down
```

## Проблемы гидратации

В проекте реализованы несколько решений для борьбы с проблемами гидратации в Next.js, особенно связанными с атрибутами `bls_skin_checked="1"`, добавляемыми браузерными расширениями.

### Проверка проблем гидратации

```powershell
# Просмотр консоли в браузере на наличие предупреждений гидратации
# Пример сообщения: "Warning: Prop `className` did not match..."
# Открыть консоль разработчика в браузере (F12) и посмотреть предупреждения
```

### Решение проблем с кириллическими именами файлов

Если изображения с кириллическими именами не загружаются:

```powershell
# Проверка наличия файла
dir .\frontend\public\images\Логотип.png

# Если файл существует, но не загружается, это может быть проблема с кодировкой имен файлов
# Используйте компонент SafeImageMulti вместо SafeImage
```

## Компоненты для решения проблем гидратации

### HydrationFix

Компонент, который удаляет проблемные атрибуты, добавляемые браузерными расширениями.

### ClientOnly

Рендерит содержимое только на клиентской стороне после монтирования компонента.

### withHydrationFix

HOC (компонент высшего порядка), который оборачивает компоненты в ClientOnly.

### SafeImage

Безопасный компонент для изображений, который загружает изображения только на клиенте.

### SafeImageMulti

Улучшенный компонент для изображений, который пытается загрузить изображение из разных источников, полезен для работы с файлами, имеющими разные варианты написания (латиница/кириллица).

## Отладка

```powershell
# Очистка кэша Next.js
cd frontend
npm run clean

# Полная пересборка проекта
npm run build

# Запуск в производственном режиме (для проверки гидратации в production)
npm run start
```

## Пример использования SafeImageMulti

```tsx
<SafeImageMulti
  src="/images/Логотип.png"
  altSrc={["/images/logotip.png", "/images/logo.png"]}
  alt="GX Exchange"
  width={50}
  height={50}
/>
```

## Стандартизация имен файлов

Рекомендуется придерживаться одной конвенции именования файлов:

```powershell
# Проверка всех имен файлов в директории изображений
dir .\frontend\public\images\
```

This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
