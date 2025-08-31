import { useState, useEffect, useRef, useCallback } from "react";
import { useProfileContext } from "@/app/(profile)/context/ProfileContext";
import { useAuthStore } from "@/store/useAuthStore";
import { useToast } from "@/components/ui/Toast";

export const useEditProfile = () => {
  const { user } = useProfileContext();
  const { updateProfile, updateAvatar, isLoading, error, clearError, checkAuthStatus, shouldPlayAnimation, setShouldPlayAnimation } = useAuthStore();
  const { showSuccess, showError } = useToast();
  
  // Функция для загрузки аватара с сервера
  const reloadAvatarFromServer = useCallback(async () => {
    if (user?.avatar && user.avatar.startsWith('blob:')) {
      try {
        // Загружаем профиль пользователя с сервера для получения актуального аватара
        await checkAuthStatus();
      } catch (error) {
        // В случае ошибки просто очищаем недействительный blob URL
        updateProfile({ avatar: undefined }, true);
      }
    }
  }, [user?.avatar, checkAuthStatus, updateProfile]);
  
  const [localLoading, setLocalLoading] = useState(false);

  // Вспомогательные функции для работы с датами
  const formatDateToYYYYMMDD = (dateString: string): string => {
    if (!dateString) return '';
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return '';
    return date.toISOString().split('T')[0];
  };

  const validateDate = (dateString: string): boolean => {
    if (!dateString) return true; // Пустая дата разрешена
    const date = new Date(dateString);
    return !isNaN(date.getTime());
  };

  // Функция для фильтрации данных перед отправкой
  const filterEmptyFields = (formData: any): any => {
    const filteredData: any = {};
    
    // Список полей, которые НЕ должны отправляться в запросе на редактирование профиля
    const excludedFields = ['avatar']; // avatar меняется отдельной формой
    
    Object.entries(formData).forEach(([key, value]) => {
      // Пропускаем исключенные поля
      if (excludedFields.includes(key)) {
        return;
      }
      
      // Специальная обработка для даты рождения
      if (key === 'date_of_birth') {
        if (value && typeof value === 'string' && value.trim() !== '') {
          // Проверяем, что дата не пустая и корректная
          if (validateDate(value)) {
            filteredData[key] = value;
          }
        }
        return; // Пропускаем остальную обработку для даты
      }
      
      // Для вложенного объекта profile
      if (key === 'profile' && value && typeof value === 'object') {
        const profileData: any = {};
        Object.entries(value).forEach(([profileKey, profileValue]) => {
          if (profileValue && typeof profileValue === 'string' && profileValue.trim() !== '') {
            profileData[profileKey] = profileValue;
          }
        });
        // Добавляем profile только если есть заполненные поля
        if (Object.keys(profileData).length > 0) {
          filteredData[key] = value;
        }
      }
      // Для обычных полей (строки)
      else if (value && typeof value === 'string' && value.trim() !== '') {
        filteredData[key] = value;
      }
    });
    
    return filteredData;
  };
  
  // Объединенное состояние формы
  const [formData, setFormData] = useState({
    first_name: user?.first_name || "",
    last_name: user?.last_name || "",
    phone_number: user?.phone_number || "",
    full_name: user?.full_name || "",
    date_of_birth: user?.date_of_birth || "",
    address: user?.address || "",
    profile: {
      bio: user?.profile?.bio || "",
      website: user?.profile?.website || "",
    },
  });

  // Состояние для анимации успеха - используем useRef для сохранения между перерендерами
  const [showSuccessAnimation, setShowSuccessAnimation] = useState(false);
  const animationTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Стабильная функция для показа анимации
  const showAnimation = useCallback(() => {
    console.log('=== АНИМАЦИЯ: showAnimation вызван ===');
    setShowSuccessAnimation(true);
    console.log('=== АНИМАЦИЯ: setShowSuccessAnimation(true) выполнен ===');
  }, []);

  // Стабильная функция для скрытия анимации
  const hideAnimation = useCallback(() => {
    setShowSuccessAnimation(false);
    if (animationTimeoutRef.current) {
      clearTimeout(animationTimeoutRef.current);
      animationTimeoutRef.current = null;
    }
  }, []);





  // Проигрывание анимации после перерендера
  useEffect(() => {
    console.log('=== АНИМАЦИЯ: useEffect сработал ===', { shouldPlayAnimation, pathname: window.location.pathname });
    
    // Анимация должна срабатывать только на странице редактирования
    const isEditPage = typeof window !== 'undefined' && window.location.pathname === '/me/edit/';
    
    if (isEditPage && shouldPlayAnimation && !showSuccessAnimation) {
      console.log('=== АНИМАЦИЯ: Запускаем анимацию ===');
      showAnimation(); // Проигрываем анимацию
      
      // Скрываем анимацию через 3 секунды
      animationTimeoutRef.current = setTimeout(() => {
        console.log('=== АНИМАЦИЯ: Скрываем анимацию ===');
        hideAnimation();
      }, 3000);
      
      // Очищаем флаг
      setShouldPlayAnimation(false);
    }
  }, [shouldPlayAnimation, showSuccessAnimation, showAnimation, hideAnimation, setShouldPlayAnimation]);

  // Очистка флага анимации при переходе на другие страницы
  useEffect(() => {
    const isEditPage = typeof window !== 'undefined' && window.location.pathname === '/me/edit/';
    
    if (!isEditPage && shouldPlayAnimation) {
      // Если мы не на странице редактирования, очищаем флаг
      setShouldPlayAnimation(false);
    }
  }, [shouldPlayAnimation, setShouldPlayAnimation]);

  // Простая защита от бесконечной анимации
  useEffect(() => {
    if (showSuccessAnimation) {
      const forceHideTimeout = setTimeout(() => {
        hideAnimation();
      }, 5000);
      
      return () => clearTimeout(forceHideTimeout);
    }
  }, [showSuccessAnimation, hideAnimation]);

  // Обработчик изменения полей формы
  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    
    if (name.includes('.')) {
      // Для вложенных полей (например, profile.bio)
      const [parentKey, childKey] = name.split('.');
      setFormData(prev => ({
        ...prev,
        [parentKey]: {
          ...(prev as any)[parentKey],
          [childKey]: value
        }
      }));
    } else {
      // Для обычных полей
      setFormData(prev => ({
        ...prev,
        [name]: value
      }));
    }
  }, []);

  // Обработчик отправки формы
  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (localLoading) return;
    
    setLocalLoading(true);
    
    try {
      const filteredData = filterEmptyFields(formData);
      
      if (Object.keys(filteredData).length === 0) {
        showError('Нет данных для обновления');
        return;
      }
      
      await updateProfile(filteredData);
      
      showSuccess('Профиль успешно обновлен!');
      
      console.log('=== АНИМАЦИЯ: Профиль обновлен, устанавливаем флаг ===');
      // Поднимаем флаг для проигрывания анимации после перерендера
      setShouldPlayAnimation(true);
      console.log('=== АНИМАЦИЯ: setShouldPlayAnimation(true) выполнен ===');
      
    } catch (error) {
      console.error('Ошибка при обновлении профиля:', error);
      showError('Ошибка при обновлении профиля');
    } finally {
      setLocalLoading(false);
    }
  }, [formData, localLoading, updateProfile, showSuccess, showError, showAnimation, hideAnimation]);

  // Обработчик загрузки аватара
  const handleAvatarChange = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    if (localLoading) return;
    
    setLocalLoading(true);
    
    try {
      await updateAvatar(file);
      showSuccess('Аватар успешно обновлен!');
      
      // Поднимаем флаг для проигрывания анимации после перерендера
      setShouldPlayAnimation(true);
      
    } catch (error) {
      console.error('Ошибка при обновлении аватара:', error);
      showError('Ошибка при обновлении аватара');
    } finally {
      setLocalLoading(false);
    }
  }, [localLoading, updateAvatar, showSuccess, showError, showAnimation, hideAnimation]);

  // Обработчик для кнопки "Убрать фото" - устанавливает дефолтную PNG
  const handleRemoveAvatar = useCallback(async () => {
    if (localLoading) return;
    
    setLocalLoading(true);
    
    try {
      // Создаем File объект из PNG
      const pngPath = '/empty_photo.png';
      const response = await fetch(pngPath);
      const pngBlob = await response.blob();
      const pngFile = new File([pngBlob], 'empty-avatar.png', { type: 'image/png' });
      
      await updateAvatar(pngFile);
      showSuccess('Установлен дефолтный аватар!');
      
      // Поднимаем флаг для проигрывания анимации после перерендера
      setShouldPlayAnimation(true);
      
    } catch (error) {
      console.error('Ошибка при установке дефолтного аватара:', error);
      showError('Ошибка при установке дефолтного аватара');
    } finally {
      setLocalLoading(false);
    }
  }, [localLoading, updateAvatar, showSuccess, showError, showAnimation, hideAnimation]);

  // Обработчик ошибки загрузки аватара
  const handleAvatarError = useCallback(() => {
    reloadAvatarFromServer();
  }, [reloadAvatarFromServer]);



  // Очищаем ошибки при размонтировании
  useEffect(() => {
    return () => {
      clearError();
    };
  }, [clearError]);



  return {
    // Состояние
    user,
    formData,
    showSuccessAnimation,
    localLoading,
    isLoading,
    error,
    
    // Функции
    handleInputChange,
    handleSubmit,
    handleAvatarChange,
    handleRemoveAvatar,
    handleAvatarError,
    reloadAvatarFromServer,
    clearError,
    showAnimation,
    hideAnimation,
    
    // Утилиты
    formatDateToYYYYMMDD,
  };
};
