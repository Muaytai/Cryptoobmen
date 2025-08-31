"use client";

import React, { createContext, useContext, ReactNode } from 'react';
import { User } from '@/store/useAuthStore';
import { useAuthStore } from '@/store/useAuthStore';
import { useWalletStore } from '@/store/useWalletStore';

interface ProfileContextType {
  user: User;
  totalUsdBalance?: number;
}

const ProfileContext = createContext<ProfileContextType | undefined>(undefined);

interface ProfileProviderProps {
  children: ReactNode;
  user: User;
  totalUsdBalance?: number;
}

export const ProfileProvider: React.FC<ProfileProviderProps> = ({ 
  children, 
  user, 
  totalUsdBalance 
}) => {
  // Получаем актуальные данные из store
  const storeUser = useAuthStore(state => state.user);
  const storeTotalUsdBalance = useWalletStore(state => state.totalUsdBalance);

  // Используем данные из store если они есть, иначе используем пропсы
  const contextValue = {
    user: storeUser || user,
    totalUsdBalance: storeTotalUsdBalance ?? totalUsdBalance,
  };

  return (
    <ProfileContext.Provider value={contextValue}>
      {children}
    </ProfileContext.Provider>
  );
};

export const useProfileContext = () => {
  const context = useContext(ProfileContext);
  if (context === undefined) {
    throw new Error('useProfileContext must be used within a ProfileProvider');
  }
  return context;
};
