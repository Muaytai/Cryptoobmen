import React from "react";
import { Button } from "@/components/ui/Button";
import { Card, CardContent } from "@/components/ui/card";
import { clsx } from "clsx";
import { Toast, useToast } from "@/components/ui/Toast";
import styles from "./EditProfile.module.css";
import { useEditProfile } from "./useEditProfile";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/useAuthStore";

export const EditProfileView: React.FC = () => {
  const router = useRouter();
  
  const {
    user,
    formData,
    showSuccessAnimation,
    localLoading,
    isLoading,
    error,
    handleInputChange,
    handleSubmit,
    handleAvatarChange,
    handleRemoveAvatar,
    handleAvatarError,
    clearError,
    formatDateToYYYYMMDD,
    showAnimation,
    hideAnimation,
  } = useEditProfile();
  
  const { shouldPlayAnimation } = useAuthStore();

  const { toasts, removeToast } = useToast();
  


  return (
    <>
      <div className={styles.pageBackground}>
        <div className={styles.container}>
          <div className={styles.header}>
            <h1 className={styles.title}>Редактирование профиля</h1>
            <p className={styles.subtitle}>
              Обновите информацию о себе
            </p>
          </div>

          <form onSubmit={handleSubmit} className={styles.form}>
            {/* Аватар */}
            <Card className={clsx(styles.avatarCard, { [styles.success]: shouldPlayAnimation })}>
              <CardContent className={styles.avatarContent}>
                <div className={styles.avatarSection}>
                  <div className={styles.avatarContainer}>
                    {user?.avatar ? (
                      <img
                        src={user.avatar}
                        alt="Avatar"
                        className={styles.avatarImage}
                        onError={handleAvatarError}
                      />
                    ) : (
                      <div className={styles.avatarPlaceholder}>
                        <span className={styles.avatarInitial}>
                          {formData.first_name?.[0] || formData.last_name?.[0] || 'U'}
                        </span>
                      </div>
                    )}
                  </div>
                  
                  <div className={styles.avatarControls}>
                    <label htmlFor="avatar-upload" className={styles.avatarUploadButton}>
                      <span>Изменить фото</span>
                      <input
                        id="avatar-upload"
                        type="file"
                        accept="image/*"
                        onChange={handleAvatarChange}
                        className={styles.hiddenInput}
                        disabled={localLoading}
                      />
                    </label>
                    
                    {user?.avatar && (
                      <Button
                        type="button"
                        onClick={handleRemoveAvatar}
                        disabled={localLoading}
                        className={styles.removeAvatarButton}
                      >
                        Убрать фото
                      </Button>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Основная форма */}
            <Card className={clsx(styles.mainFormCard, { [styles.success]: shouldPlayAnimation })}>
              <CardContent className={styles.mainFormContent}>
                <div className={styles.formGrid}>
                  {/* Имя */}
                  <div className={styles.formField}>
                    <label htmlFor="first_name" className={styles.label}>
                      Имя *
                    </label>
                    <input
                      type="text"
                      id="first_name"
                      name="first_name"
                      value={formData.first_name}
                      onChange={handleInputChange}
                      disabled={localLoading}
                      className={styles.input}
                      placeholder="Введите имя"
                      required
                    />
                  </div>

                  {/* Фамилия */}
                  <div className={styles.formField}>
                    <label htmlFor="last_name" className={styles.label}>
                      Фамилия *
                    </label>
                    <input
                      type="text"
                      id="last_name"
                      name="last_name"
                      value={formData.last_name}
                      onChange={handleInputChange}
                      disabled={localLoading}
                      className={styles.input}
                      placeholder="Введите фамилию"
                      required
                    />
                  </div>

                  {/* Телефон */}
                  <div className={styles.formField}>
                    <label htmlFor="phone_number" className={styles.label}>
                      Телефон
                    </label>
                    <input
                      type="tel"
                      id="phone_number"
                      name="phone_number"
                      value={formData.phone_number}
                      onChange={handleInputChange}
                      disabled={localLoading}
                      className={styles.input}
                      placeholder="+7 (999) 123-45-67"
                    />
                  </div>

                  {/* Полное имя */}
                  <div className={styles.formField}>
                    <label htmlFor="full_name" className={styles.label}>
                      Полное имя
                    </label>
                    <input
                      type="text"
                      id="full_name"
                      name="full_name"
                      value={formData.full_name}
                      onChange={handleInputChange}
                      disabled={localLoading}
                      className={styles.input}
                      placeholder="Иванов Иван Иванович"
                    />
                  </div>

                  {/* Дата рождения */}
                  <div className={styles.formField}>
                    <label htmlFor="date_of_birth" className={styles.label}>
                      Дата рождения
                    </label>
                    <input
                      type="date"
                      id="date_of_birth"
                      name="date_of_birth"
                      value={formatDateToYYYYMMDD(formData.date_of_birth)}
                      onChange={handleInputChange}
                      disabled={localLoading}
                      className={styles.input}
                    />
                  </div>

                  {/* Адрес */}
                  <div className={styles.formField}>
                    <label htmlFor="address" className={styles.label}>
                      Адрес проживания
                    </label>
                    <input
                      type="text"
                      id="address"
                      name="address"
                      value={formData.address}
                      onChange={handleInputChange}
                      disabled={localLoading}
                      className={styles.input}
                      placeholder="Введите адрес"
                    />
                  </div>

                  {/* Биография */}
                  <div className={clsx(styles.formField, styles.fullWidth)}>
                    <label htmlFor="bio" className={styles.label}>
                      О себе
                    </label>
                    <textarea
                      id="bio"
                      name="profile.bio"
                      value={formData.profile.bio}
                      onChange={handleInputChange}
                      disabled={localLoading}
                      className={styles.textarea}
                      placeholder="Расскажите о себе..."
                      rows={4}
                    />
                  </div>

                  {/* Веб-сайт */}
                  <div className={styles.formField}>
                    <label htmlFor="website" className={styles.label}>
                      Веб-сайт
                    </label>
                    <input
                      type="url"
                      id="website"
                      name="profile.website"
                      value={formData.profile.website}
                      onChange={handleInputChange}
                      disabled={localLoading}
                      className={styles.input}
                      placeholder="https://example.com"
                    />
                  </div>
                </div>

                {/* Кнопки */}
                <div className={styles.formActions}>
                  <Button
                    type="submit"
                    disabled={localLoading || isLoading}
                    className={styles.submitButton}
                  >
                    {localLoading || isLoading ? "Сохранение..." : "Сохранить изменения"}
                  </Button>
                  
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => {
                      console.log('Кнопка "Вернуться к профилю" нажата');
                      console.log('router:', router);
                      console.log('Путь:', '/me');
                      try {
                        // Сначала пробуем router.replace
                        router.replace('/me');
                        console.log('router.replace выполнен');
                        
                        // Если не сработало, используем router.back()
                        setTimeout(() => {
                          if (window.location.pathname === '/me/edit') {
                            console.log('router.replace не сработал, используем router.back()');
                            router.back();
                          }
                        }, 100);
                      } catch (error) {
                        console.error('Ошибка при переходе:', error);
                        router.back();
                      }
                    }}
                    disabled={localLoading || isLoading}
                    className={styles.backButton}
                  >
                    Вернуться к профилю
                  </Button>
                </div>
              </CardContent>
            </Card>
          </form>

          {/* Анимация успеха */}
          {showSuccessAnimation && (
            <div className={styles.successAnimation}>
              <div className={styles.successContent}>
                <div className={styles.successIcon}>✓</div>
                <div className={styles.successText}>Профиль успешно обновлен!</div>
              </div>
            </div>
          )}
          

          

          

          


          {/* Уведомления */}
          {toasts.map((toast) => (
            <Toast
              key={toast.id}
              {...toast}
              onClose={() => removeToast(toast.id)}
            />
          ))}
        </div>
      </div>
    </>
  );
};
