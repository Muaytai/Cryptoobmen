'use client';

import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { useAuthStore } from '@/store/useAuthStore';
import Image from '@/components/SafeImage';
import { clsx } from 'clsx';
import styles from './PersonalSection.module.css';

export const PersonalSection: React.FC = () => {
  const { user } = useAuthStore();

  return (
    <>
      <div className={styles.container}>
        {/* Cards Grid */}
        <div className={styles.cardsGrid}>
          {/* Баланс */}
          <Card className={clsx(styles.div1, "bg-subcard rounded-[15px]")}>
            <CardContent className="p-3 md:p-5 h-[80px] md:h-[104px] relative">
              <span className="font-medium text-subcard-text/60 text-xs md:text-sm [font-family:'Manrope',Helvetica]">
                Баланс
              </span>
              <div className="flex w-full items-center justify-between mt-4">
                <span className="font-medium text-subcard-text text-base md:text-lg [font-family:'Manrope',Helvetica]">
                  0.00 USDT
                </span>
              </div>
            </CardContent>
          </Card>





          {/* Профиль пользователя */}
          <Card className={clsx(styles.div3, "bg-subcard rounded-[15px]")}>
            <CardContent className="p-3 md:p-5 min-h-[120px] md:min-h-[140px]">
              <span className="font-medium text-subcard-text/60 text-xs md:text-sm [font-family:'Manrope',Helvetica]">
                Профиль
              </span>
              <div className="mt-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="text-subcard-text/60 text-xs font-medium mb-1">Имя профиля</div>
                    <span className="font-medium text-subcard-text text-base md:text-lg [font-family:'Manrope',Helvetica]">
                      {user?.username || 'Пользователь'}
                    </span>
                  </div>
                  <div className="w-16 h-16 md:w-20 md:h-20 lg:w-24 lg:h-24 xl:w-32 xl:h-32 rounded-full bg-primary flex items-center justify-center ml-4">
                    {user?.avatar ? (
                      <Image 
                        src={user.avatar} 
                        alt="Avatar" 
                        width={150} 
                        height={150} 
                        className="rounded-full w-full h-full object-cover"
                      />
                    ) : (
                      <span className="text-white text-lg md:text-xl lg:text-2xl xl:text-3xl font-medium">
                        {user?.first_name?.[0] || user?.username?.[0] || 'U'}
                      </span>
                    )}
                  </div>
                </div>
                <div className="pt-2 border-t border-white/10">
                  <div className="text-subcard-text/60 text-xs font-medium mb-1">Статус верификации</div>
                  <div className="text-subcard-text text-sm">
                    {user?.is_verified ? 'Верифицирован' : 'Не верифицирован'}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>







          {/* Карточка с личными данными */}
          <Card className={clsx(styles.div10, "bg-subcard rounded-[15px]")}>
            <CardContent className={styles.cardContent}>
              <span className="font-medium text-subcard-text/60 text-xs md:text-sm [font-family:'Manrope',Helvetica]">
                Личные данные
              </span>
              <div className={styles.dataGrid}>
                <div className={styles.dataRow}>
                  <div className="text-subcard-text/60 text-xs font-medium mb-1">Имя</div>
                  <div className="font-medium text-subcard-text text-base md:text-lg [font-family:'Manrope',Helvetica]">{user?.first_name || 'Не указано'}</div>
                </div>
                <div className={styles.dataRow}>
                  <div className="text-subcard-text/60 text-xs font-medium mb-1">Фамилия</div>
                  <div className="font-medium text-subcard-text text-base md:text-lg [font-family:'Manrope',Helvetica]">{user?.last_name || 'Не указано'}</div>
                </div>
                <div className={styles.dataRow}>
                  <div className="text-subcard-text/60 text-xs font-medium mb-1">Полное имя</div>
                  <div className="font-medium text-subcard-text text-base md:text-lg [font-family:'Manrope',Helvetica]">{user?.full_name || 'Не указано'}</div>
                </div>
                <div className={styles.dataRow}>
                  <div className="text-subcard-text/60 text-xs font-medium mb-1">Телефон</div>
                  <div className="font-medium text-subcard-text text-base md:text-lg [font-family:'Manrope',Helvetica]">{user?.phone_number || 'Не указано'}</div>
                </div>
                <div className={styles.dataRow}>
                  <div className="text-subcard-text/60 text-xs font-medium mb-1">Адрес</div>
                  <div className="font-medium text-subcard-text text-base md:text-lg [font-family:'Manrope',Helvetica]">{user?.address || 'Не указано'}</div>
                </div>
                <div className={styles.dataRow}>
                  <div className="text-subcard-text/60 text-xs font-medium mb-1">Email</div>
                  <div className="font-medium text-subcard-text text-base md:text-lg [font-family:'Manrope',Helvetica]">{user?.email || 'Не указано'}</div>
                </div>
                <div className={styles.dataRow}>
                  <div className="text-subcard-text/60 text-xs font-medium mb-1">Веб-сайт</div>
                  <div className="font-medium text-subcard-text text-base md:text-lg [font-family:'Manrope',Helvetica]">{user?.profile?.website || 'Не указано'}</div>
                </div>
                <div className={styles.dataRow}>
                  <div className="text-subcard-text/60 text-xs font-medium mb-1">Дата рождения</div>
                  <div className="font-medium text-subcard-text text-base md:text-lg [font-family:'Manrope',Helvetica]">
                    {user?.date_of_birth ? new Date(user.date_of_birth).toLocaleDateString('ru-RU') : 'Не указано'}
                  </div>
                </div>

              </div>
            </CardContent>
          </Card>




        </div>
      </div>


    </>
  );
};
