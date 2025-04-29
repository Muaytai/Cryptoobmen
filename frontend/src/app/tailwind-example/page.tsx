import React from 'react';
import { Button } from '@/components/ui/Button';
import { 
  Card, 
  CardHeader, 
  CardTitle, 
  CardDescription, 
  CardContent, 
  CardFooter 
} from '@/components/ui/card';
import { FigmaImage } from '@/components/ui/image';
import { IconHome, IconUser, IconSettings } from '@/components/ui/icon';

export default function TailwindExample() {
  return (
    <div className="container mx-auto py-12 px-4">
      <h1 className="text-4xl font-bold mb-8">Пример использования Tailwind CSS</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <IconHome size="sm" className="text-primary" />
              Карточка 1
            </CardTitle>
            <CardDescription>Описание карточки с примером Tailwind CSS</CardDescription>
          </CardHeader>
          <CardContent>
            <FigmaImage 
              src="https://images.unsplash.com/photo-1519681393784-d120267933ba"
              alt="Горы"
              width={400}
              height={300}
              aspectRatio="video"
              className="mb-4"
            />
            <p className="text-base text-gray-700 dark:text-gray-300">
              Это пример контента в карточке с использованием утилит Tailwind CSS.
            </p>
          </CardContent>
          <CardFooter>
            <Button>Подробнее</Button>
          </CardFooter>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <IconUser size="sm" className="text-primary" />
              Карточка 2
            </CardTitle>
            <CardDescription>Еще один пример с Tailwind CSS</CardDescription>
          </CardHeader>
          <CardContent>
            <FigmaImage 
              src="https://images.unsplash.com/photo-1542202229-7d93c33f5d07"
              alt="Океан"
              width={400}
              height={300}
              aspectRatio="video"
              rounded="lg"
              className="mb-4"
            />
            <p className="text-base text-gray-700 dark:text-gray-300">
              Tailwind позволяет быстро верстать компоненты без написания CSS.
            </p>
          </CardContent>
          <CardFooter>
            <Button variant="outline">Подробнее</Button>
          </CardFooter>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <IconSettings size="sm" className="text-primary" />
              Карточка 3
            </CardTitle>
            <CardDescription>Демонстрация стилей и компонентов</CardDescription>
          </CardHeader>
          <CardContent>
            <FigmaImage 
              src="https://images.unsplash.com/photo-1490604001847-b712b0c2f967"
              alt="Природа"
              width={400}
              height={300}
              aspectRatio="video"
              rounded="sm"
              className="mb-4"
            />
            <p className="text-base text-gray-700 dark:text-gray-300">
              Использование утилитарных классов делает верстку гибкой и удобной.
            </p>
          </CardContent>
          <CardFooter>
            <Button variant="secondary">Подробнее</Button>
          </CardFooter>
        </Card>
      </div>
      
      <div className="bg-slate-100 dark:bg-slate-800 p-6 rounded-lg mb-12">
        <h2 className="text-2xl font-semibold mb-4">Различные варианты кнопок</h2>
        <div className="flex flex-wrap gap-4">
          <Button>Обычная</Button>
          <Button variant="secondary">Второстепенная</Button>
          <Button variant="outline">Контурная</Button>
          <Button variant="ghost">Призрачная</Button>
          <Button variant="destructive">Опасная</Button>
          <Button variant="link">Ссылка</Button>
        </div>
      </div>
      
      <div className="bg-slate-100 dark:bg-slate-800 p-6 rounded-lg mb-12">
        <h2 className="text-2xl font-semibold mb-4">Различные варианты изображений</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <h3 className="text-lg font-medium mb-2">Стандартное</h3>
            <FigmaImage 
              src="https://images.unsplash.com/photo-1570295999919-56ceb5ecca61"
              alt="Портрет"
              width={200}
              height={200}
              aspectRatio="auto"
            />
          </div>
          
          <div>
            <h3 className="text-lg font-medium mb-2">Квадратное</h3>
            <FigmaImage 
              src="https://images.unsplash.com/photo-1570295999919-56ceb5ecca61"
              alt="Портрет"
              width={200}
              height={200}
              aspectRatio="square"
            />
          </div>
          
          <div>
            <h3 className="text-lg font-medium mb-2">Видео (16:9)</h3>
            <FigmaImage 
              src="https://images.unsplash.com/photo-1570295999919-56ceb5ecca61"
              alt="Портрет"
              width={200}
              height={200}
              aspectRatio="video"
            />
          </div>
          
          <div>
            <h3 className="text-lg font-medium mb-2">Круглое</h3>
            <FigmaImage 
              src="https://images.unsplash.com/photo-1570295999919-56ceb5ecca61"
              alt="Портрет"
              width={200}
              height={200}
              aspectRatio="square"
              rounded="full"
            />
          </div>
        </div>
      </div>
      
      <div className="bg-slate-100 dark:bg-slate-800 p-6 rounded-lg">
        <h2 className="text-2xl font-semibold mb-4">Различные варианты иконок</h2>
        <div className="flex flex-wrap gap-8">
          <div className="flex flex-col items-center">
            <IconHome size="sm" className="text-primary mb-2" />
            <span className="text-sm">Маленькая</span>
          </div>
          <div className="flex flex-col items-center">
            <IconHome size="md" className="text-primary mb-2" />
            <span className="text-sm">Средняя</span>
          </div>
          <div className="flex flex-col items-center">
            <IconHome size="lg" className="text-primary mb-2" />
            <span className="text-sm">Большая</span>
          </div>
          <div className="flex flex-col items-center">
            <IconHome size="xl" className="text-primary mb-2" />
            <span className="text-sm">Очень большая</span>
          </div>
          
          <div className="flex flex-col items-center">
            <IconUser size="lg" className="text-primary mb-2" />
            <span className="text-sm">Пользователь</span>
          </div>
          <div className="flex flex-col items-center">
            <IconSettings size="lg" className="text-primary mb-2" />
            <span className="text-sm">Настройки</span>
          </div>
        </div>
      </div>
    </div>
  );
} 