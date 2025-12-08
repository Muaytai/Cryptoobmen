import {useState, useEffect, useRef, useCallback} from "react";
import {useProfileContext} from "@/app/(profile)/context/ProfileContext";
import {useAuthStore} from "@/store/useAuthStore";
import {useToast} from "@/components/ui/Toast";

type ProfileFormData = {
  first_name: string;
  last_name: string;
  phone_number: string;
  full_name: string;
  date_of_birth: string;
  address: string;
  profile: {
    bio: string;
    website: string;
  };
};

type ProfileUpdatePayload = Partial<Omit<ProfileFormData, "profile">> & {
  profile?: Partial<ProfileFormData["profile"]>;
};

const isValidDate = (dateString: string): boolean => {
  if (!dateString) return false;
  const date = new Date(dateString);
  return !Number.isNaN(date.getTime());
};

const isNonEmpty = (value: string): boolean => value.trim().length > 0;

const filterEmptyFields = (formState: ProfileFormData): ProfileUpdatePayload => {
  const {profile, date_of_birth, ...plainFields} = formState;
  const filtered: ProfileUpdatePayload = {};

  (Object.entries(plainFields) as Array<
    [Exclude<keyof ProfileFormData, "profile" | "date_of_birth">, string]
  >).forEach(([key, value]) => {
    if (isNonEmpty(value)) {
      filtered[key] = value;
    }
  });

  if (isNonEmpty(date_of_birth) && isValidDate(date_of_birth)) {
    filtered.date_of_birth = date_of_birth;
  }

  const profilePayload = Object.entries(profile).reduce<
    Partial<ProfileFormData["profile"]>
  >((acc, [key, value]) => {
    if (isNonEmpty(value)) {
      acc[key as keyof ProfileFormData["profile"]] = value;
    }
    return acc;
  }, {});

  if (Object.keys(profilePayload).length > 0) {
    filtered.profile = profilePayload;
  }

  return filtered;
};

const BASE_FIELD_KEYS: Array<Exclude<keyof ProfileFormData, "profile">> = [
  "first_name",
  "last_name",
  "phone_number",
  "full_name",
  "date_of_birth",
  "address",
];

export const useEditProfile = () => {
  const {user} = useProfileContext();
  const {
    updateProfile,
    updateAvatar,
    isLoading,
    clearError,
    checkAuthStatus,
    shouldPlayAnimation,
    setShouldPlayAnimation,
  } = useAuthStore();
  const {showSuccess, showError} = useToast();

  const reloadAvatarFromServer = useCallback(async () => {
    if (user?.avatar && user.avatar.startsWith("blob:")) {
      try {
        await checkAuthStatus();
      } catch {
        updateProfile({avatar: undefined}, true);
      }
    }
  }, [user?.avatar, checkAuthStatus, updateProfile]);

  const [localLoading, setLocalLoading] = useState(false);

  const formatDateToYYYYMMDD = (dateString: string): string => {
    if (!dateString) return "";
    const date = new Date(dateString);
    if (Number.isNaN(date.getTime())) return "";
    return date.toISOString().split("T")[0];
  };

  const [formData, setFormData] = useState<ProfileFormData>({
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
  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
      const {name, value} = e.target;

      if (name.startsWith("profile.")) {
        const [, nestedKey] = name.split(".");
        setFormData((prev) => ({
          ...prev,
          profile: {
            ...prev.profile,
            [nestedKey as keyof ProfileFormData["profile"]]: value,
          },
        }));
        return;
      }

      if (
        (BASE_FIELD_KEYS as string[]).includes(name)
      ) {
        setFormData((prev) => ({
          ...prev,
          [name as Exclude<keyof ProfileFormData, "profile">]: value,
        }));
      }
    },
    []
  );

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
  }, [
    formData,
    localLoading,
    updateProfile,
    showSuccess,
    showError,
    setShouldPlayAnimation,
  ]);

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
  }, [
    localLoading,
    updateAvatar,
    showSuccess,
    showError,
    setShouldPlayAnimation,
  ]);

  // Обработчик для кнопки "Убрать фото" - устанавливает дефолтную PNG
  const handleRemoveAvatar = useCallback(async () => {
    if (localLoading) return;
    
    setLocalLoading(true);
    
    try {
      // Создаем File объект из PNG
      const pngPath = '/empty_photo.webp';
      const response = await fetch(pngPath);
      const pngBlob = await response.blob();
      const pngFile = new File([pngBlob], 'empty-avatar.webp', { type: 'image/webp' });
      
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
  }, [
    localLoading,
    updateAvatar,
    showSuccess,
    showError,
    setShouldPlayAnimation,
  ]);

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
    user,
    formData,
    showSuccessAnimation,
    localLoading,
    isLoading,
    handleInputChange,
    handleSubmit,
    handleAvatarChange,
    handleRemoveAvatar,
    handleAvatarError,
    formatDateToYYYYMMDD,
  };
};
