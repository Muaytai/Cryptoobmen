"use client";

import React, { useEffect, useState } from "react";
import api from "@/lib/api/fetch";
import { useAuthStore } from "@/store/useAuthStore";
import UserDetailsModal from "@/components/UserDetailsModal";

type UserRow = {
  id: number | string;
  email: string;
  username: string;
  first_name?: string;
  last_name?: string;
  is_site_admin?: boolean;
  is_staff?: boolean;
  is_superuser?: boolean;
  is_active?: boolean;
  is_verified?: boolean;
  kyc_verified?: boolean;
  date_joined?: string;
  last_login?: string;
  total_balance_usd?: number;
};

export default function UsersTable() {
  const [users, setUsers] = useState<UserRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [authLoading, setAuthLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterRole, setFilterRole] = useState("all");
  const [filterStatus, setFilterStatus] = useState("all");
  const [selectedUserId, setSelectedUserId] = useState<number | string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const getAuthHeaders = useAuthStore((s) => s.getAuthHeaders);
  const user = useAuthStore((s) => s.user);
  const checkAuthStatus = useAuthStore((s) => s.checkAuthStatus);

  const fetchUsers = async () => {
    setLoading(true);
    setError(null);
    try {
      const headers = getAuthHeaders();
      const res: any = await api.get("/accounts/users/admin_list/", { headers });
      const data = res?.data ?? res;
      setUsers(Array.isArray(data) ? data : []);
    } catch (e: any) {
      setError(e?.message || "Не удалось загрузить пользователей");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const initData = async () => {
      setAuthLoading(true);
      try {
        // Сначала проверяем аутентификацию
        if (!user) {
          await checkAuthStatus();
        }
      } catch (error) {
        console.error('Auth check failed:', error);
        setError('Ошибка аутентификации');
      } finally {
        setAuthLoading(false);
      }
    };
    
    initData();
  }, [user, checkAuthStatus]);

  // Загружаем данные когда пользователь аутентифицирован
  useEffect(() => {
    if (user && !authLoading) {
      fetchUsers();
    }
  }, [user, authLoading]);

  const filteredUsers = users.filter((user) => {
    const matchesSearch = 
      user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (user.first_name && user.first_name.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (user.last_name && user.last_name.toLowerCase().includes(searchTerm.toLowerCase()));

    const matchesRole = 
      filterRole === "all" ||
      (filterRole === "site_admin" && user.is_site_admin) ||
      (filterRole === "staff" && user.is_staff) ||
      (filterRole === "superuser" && user.is_superuser) ||
      (filterRole === "regular" && !user.is_site_admin && !user.is_staff && !user.is_superuser);

    const matchesStatus = 
      filterStatus === "all" ||
      (filterStatus === "active" && user.is_active) ||
      (filterStatus === "verified" && user.is_verified) ||
      (filterStatus === "kyc_verified" && user.kyc_verified);

    return matchesSearch && matchesRole && matchesStatus;
  });

  // Функции управления правами убраны - только просмотр пользователей
  
  const openUserDetails = (userId: number | string) => {
    setSelectedUserId(userId);
    setIsModalOpen(true);
  };

  const closeUserDetails = () => {
    setSelectedUserId(null);
    setIsModalOpen(false);
  };

  if (authLoading) return <div className="py-4">Проверка аутентификации…</div>;
  if (loading) return <div className="py-4">Загрузка пользователей…</div>;
  if (error) return <div className="py-4 text-red-500">{error}</div>;
  if (!user) return <div className="py-4 text-red-500">Необходима аутентификация</div>;

  return (
    <div className="space-y-6">
      {/* Заголовок как на CryptoTable */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 px-6 py-4">
        <div className="flex items-center gap-3">
          <span className="text-2xl">👥</span>
          <h1 className="text-2xl font-semibold text-gray-900">Управление пользователями</h1>
        </div>
      </div>

      {/* Фильтры и поиск */}
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 p-6 rounded-xl border border-blue-100">
        <div className="flex flex-wrap gap-4">
          <div className="flex-1 min-w-[250px]">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              🔍 Поиск пользователей
            </label>
            <input
              type="text"
              placeholder="Введите имя, email или username..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-4 py-3 border border-gray-200 rounded-lg text-sm text-gray-900 bg-white placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            />
          </div>
          <div className="min-w-[180px]">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              👤 Роль
            </label>
            <select
              value={filterRole}
              onChange={(e) => setFilterRole(e.target.value)}
              className="w-full px-4 py-3 border border-gray-200 rounded-lg text-sm text-gray-900 bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            >
              <option value="all">Все роли</option>
              <option value="site_admin">Администраторы сайта</option>
              <option value="staff">Персонал</option>
              <option value="superuser">Суперпользователи</option>
              <option value="regular">Обычные пользователи</option>
            </select>
          </div>
          <div className="min-w-[180px]">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              ✅ Статус
            </label>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="w-full px-4 py-3 border border-gray-200 rounded-lg text-sm text-gray-900 bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            >
              <option value="all">Все статусы</option>
              <option value="active">Активные</option>
              <option value="verified">Верифицированные</option>
              <option value="kyc_verified">KYC верифицированные</option>
            </select>
          </div>
          <div className="flex items-end gap-2">
            <button
              onClick={fetchUsers}
              className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg text-sm font-medium hover:from-blue-700 hover:to-purple-700 transition-all transform hover:scale-105 shadow-lg"
            >
              🔄 Обновить
            </button>
          </div>
        </div>
      </div>

      {/* Статистика */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Всего пользователей</p>
              <p className="text-2xl font-bold text-gray-900">{users.length}</p>
            </div>
            <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
              <span className="text-2xl">👥</span>
            </div>
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Активные</p>
              <p className="text-2xl font-bold text-green-600">{users.filter(u => u.is_active !== false).length}</p>
            </div>
            <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
              <span className="text-2xl">✅</span>
            </div>
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Администраторы</p>
              <p className="text-2xl font-bold text-purple-600">{users.filter(u => u.is_site_admin).length}</p>
            </div>
            <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center">
              <span className="text-2xl">👑</span>
            </div>
          </div>
        </div>
        <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">KYC</p>
              <p className="text-2xl font-bold text-orange-600">{users.filter(u => u.kyc_verified).length}</p>
            </div>
            <div className="w-12 h-12 bg-orange-100 rounded-full flex items-center justify-center">
              <span className="text-2xl">📋</span>
            </div>
          </div>
        </div>
      </div>

      {/* Таблица */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-left px-4 py-3 text-sm font-medium text-gray-700">Пользователь</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-gray-700">Email</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-gray-700">Роль</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-gray-700">Статус</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-gray-700">Баланс</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-gray-700">Дата</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-gray-700">Действия</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {filteredUsers.map((u) => (
                <tr key={u.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3">
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center text-gray-600 font-medium text-sm">
                        {u.username.charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <div className="text-sm font-medium text-gray-900">{u.username}</div>
                        <div className="text-xs text-gray-500 font-mono">
                          {u.first_name && u.last_name 
                            ? `${u.first_name} ${u.last_name}`
                            : u.first_name || u.last_name || "Без имени"
                          }
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center space-x-2">
                      <span className="text-sm text-gray-900">{u.email}</span>
                      {u.is_verified && (
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          ✓
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {u.is_superuser && (
                        <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-red-100 text-red-800">
                          Super
                        </span>
                      )}
                      {u.is_staff && (
                        <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-800">
                          Staff
                        </span>
                      )}
                      {u.is_site_admin && (
                        <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-purple-100 text-purple-800">
                          Site Admin
                        </span>
                      )}
                      {!u.is_superuser && !u.is_staff && !u.is_site_admin && (
                        <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-800">
                          User
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center space-x-2">
                      {u.kyc_verified ? (
                        <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-green-100 text-green-800">
                          Пройден
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-yellow-100 text-yellow-800">
                          Ожидает
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="text-sm">
                      {u.total_balance_usd !== undefined ? (
                        <span className="font-medium text-green-600">
                          ${u.total_balance_usd.toFixed(2)}
                        </span>
                      ) : (
                        <span className="text-gray-400 text-xs">
                          Нет данных
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="text-sm text-gray-900">
                      {u.date_joined ? new Date(u.date_joined).toLocaleDateString('ru-RU') : "—"}
                    </div>
                    <div className="text-xs text-gray-500">
                      {u.last_login ? `Вход: ${new Date(u.last_login).toLocaleDateString('ru-RU')}` : "Никогда"}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center space-x-1">
                      <button
                        onClick={() => openUserDetails(u.id)}
                        className="px-2 py-1 rounded text-xs font-medium bg-green-100 text-green-700 hover:bg-green-200 transition-colors"
                        title="Просмотреть детали пользователя"
                      >
                        👁️ Детали
                      </button>
                      <button
                        onClick={() => window.location.href = `/admin/users/${u.id}`}
                        className="px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-700 hover:bg-blue-200 transition-colors"
                      >
                        Редактировать
                      </button>
                      <button
                        className="px-2 py-1 rounded text-xs font-medium bg-red-100 text-red-700 hover:bg-red-200 transition-colors"
                      >
                        Заблокировать
                      </button>
                      <button
                        className="px-2 py-1 rounded text-xs font-medium bg-red-100 text-red-700 hover:bg-red-200 transition-colors"
                      >
                        Удалить
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {filteredUsers.length === 0 && (
                <tr>
                  <td className="px-4 py-8 text-center text-gray-500" colSpan={7}>
                    <p className="text-sm">Пользователи не найдены</p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Информация о результатах */}
      <div className="flex items-center justify-between text-sm text-gray-600 bg-gray-50 px-4 py-3 rounded-lg">
        <span>Показано {filteredUsers.length} из {users.length} пользователей</span>
        {filteredUsers.length > 0 && (
          <span className="text-blue-600">Последнее обновление: {new Date().toLocaleTimeString('ru-RU')}</span>
        )}
      </div>

      {/* User Details Modal */}
      {selectedUserId && (
        <UserDetailsModal
          userId={selectedUserId}
          isOpen={isModalOpen}
          onClose={closeUserDetails}
        />
      )}
    </div>
  );
}


