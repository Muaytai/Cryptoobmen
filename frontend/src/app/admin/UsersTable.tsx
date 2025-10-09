"use client";

import React, { useEffect, useState } from "react";
import api from "@/lib/api/fetch";
import { useAuthStore } from "@/store/useAuthStore";

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
};

export default function UsersTable() {
  const [users, setUsers] = useState<UserRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterRole, setFilterRole] = useState("all");
  const [filterStatus, setFilterStatus] = useState("all");
  const getAuthHeaders = useAuthStore((s) => s.getAuthHeaders);

  const fetchUsers = async () => {
    setLoading(true);
    setError(null);
    try {
      const headers = getAuthHeaders();
      const res: any = await api.get("/accounts/users/", { headers });
      const data = res?.data ?? res;
      setUsers(Array.isArray(data) ? data : []);
    } catch (e: any) {
      setError(e?.message || "Не удалось загрузить пользователей");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, [getAuthHeaders]);

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
      (filterStatus === "inactive" && !user.is_active) ||
      (filterStatus === "verified" && user.is_verified) ||
      (filterStatus === "kyc_verified" && user.kyc_verified);

    return matchesSearch && matchesRole && matchesStatus;
  });

  const toggleSiteAdmin = async (userId: string | number, currentStatus: boolean) => {
    try {
      const headers = getAuthHeaders();
      await api.patch(`/accounts/users/${userId}/`, 
        { is_site_admin: !currentStatus }, 
        { headers }
      );
      await fetchUsers(); // Обновляем список
    } catch (e: any) {
      setError(e?.message || "Не удалось обновить права администратора");
    }
  };

  const toggleActive = async (userId: string | number, currentStatus: boolean) => {
    try {
      const headers = getAuthHeaders();
      await api.patch(`/accounts/users/${userId}/`, 
        { is_active: !currentStatus }, 
        { headers }
      );
      await fetchUsers(); // Обновляем список
    } catch (e: any) {
      setError(e?.message || "Не удалось обновить статус пользователя");
    }
  };

  if (loading) return <div className="py-4">Загрузка пользователей…</div>;
  if (error) return <div className="py-4 text-red-500">{error}</div>;

  return (
    <div className="space-y-4">
      {/* Фильтры и поиск */}
      <div className="flex flex-wrap gap-4 p-4 bg-muted/20 rounded-lg">
        <div className="flex-1 min-w-[200px]">
          <input
            type="text"
            placeholder="Поиск по email, username, имени..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full px-3 py-2 border rounded-md text-sm"
          />
        </div>
        <select
          value={filterRole}
          onChange={(e) => setFilterRole(e.target.value)}
          className="px-3 py-2 border rounded-md text-sm"
        >
          <option value="all">Все роли</option>
          <option value="site_admin">Администраторы сайта</option>
          <option value="staff">Персонал</option>
          <option value="superuser">Суперпользователи</option>
          <option value="regular">Обычные пользователи</option>
        </select>
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="px-3 py-2 border rounded-md text-sm"
        >
          <option value="all">Все статусы</option>
          <option value="active">Активные</option>
          <option value="inactive">Неактивные</option>
          <option value="verified">Верифицированные</option>
          <option value="kyc_verified">KYC верифицированные</option>
        </select>
        <button
          onClick={fetchUsers}
          className="px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm hover:bg-primary/90"
        >
          Обновить
        </button>
      </div>

      {/* Таблица */}
      <div className="w-full overflow-x-auto border rounded-md">
        <table className="min-w-[1000px] w-full text-sm">
          <thead className="bg-muted/40">
            <tr>
              <th className="text-left p-3">Email</th>
              <th className="text-left p-3">Username</th>
              <th className="text-left p-3">Имя</th>
              <th className="text-left p-3">Статус</th>
              <th className="text-left p-3">Роли</th>
              <th className="text-left p-3">KYC</th>
              <th className="text-left p-3">Дата регистрации</th>
              <th className="text-left p-3">Действия</th>
            </tr>
          </thead>
          <tbody>
            {filteredUsers.map((u) => (
              <tr key={u.id} className="border-t hover:bg-muted/40">
                <td className="p-3">
                  <div className="flex items-center gap-2">
                    <span>{u.email}</span>
                    {u.is_verified && <span className="text-green-500">✓</span>}
                  </div>
                </td>
                <td className="p-3">{u.username}</td>
                <td className="p-3">
                  {u.first_name && u.last_name 
                    ? `${u.first_name} ${u.last_name}`
                    : u.first_name || u.last_name || "—"
                  }
                </td>
                <td className="p-3">
                  <span className={`px-2 py-1 rounded-full text-xs ${
                    u.is_active ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
                  }`}>
                    {u.is_active ? "Активен" : "Заблокирован"}
                  </span>
                </td>
                <td className="p-3">
                  <div className="flex gap-1 flex-wrap">
                    {u.is_superuser && <span className="px-2 py-1 bg-red-100 text-red-800 rounded text-xs">Super</span>}
                    {u.is_staff && <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">Staff</span>}
                    {u.is_site_admin && <span className="px-2 py-1 bg-purple-100 text-purple-800 rounded text-xs">Site Admin</span>}
                    {!u.is_superuser && !u.is_staff && !u.is_site_admin && (
                      <span className="px-2 py-1 bg-gray-100 text-gray-800 rounded text-xs">User</span>
                    )}
                  </div>
                </td>
                <td className="p-3">
                  <span className={`px-2 py-1 rounded-full text-xs ${
                    u.kyc_verified ? "bg-green-100 text-green-800" : "bg-yellow-100 text-yellow-800"
                  }`}>
                    {u.kyc_verified ? "✓" : "—"}
                  </span>
                </td>
                <td className="p-3">{u.date_joined?.slice(0, 10) || "—"}</td>
                <td className="p-3">
                  <div className="flex gap-2">
                    <button
                      onClick={() => window.location.href = `/admin/users/${u.id}`}
                      className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs hover:bg-blue-200"
                    >
                      Просмотр
                    </button>
                    <button
                      onClick={() => toggleSiteAdmin(u.id, u.is_site_admin || false)}
                      className={`px-2 py-1 rounded text-xs ${
                        u.is_site_admin 
                          ? "bg-red-100 text-red-800 hover:bg-red-200" 
                          : "bg-green-100 text-green-800 hover:bg-green-200"
                      }`}
                    >
                      {u.is_site_admin ? "Убрать админ" : "Сделать админ"}
                    </button>
                    <button
                      onClick={() => toggleActive(u.id, u.is_active || false)}
                      className={`px-2 py-1 rounded text-xs ${
                        u.is_active 
                          ? "bg-red-100 text-red-800 hover:bg-red-200" 
                          : "bg-green-100 text-green-800 hover:bg-green-200"
                      }`}
                    >
                      {u.is_active ? "Заблокировать" : "Разблокировать"}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {filteredUsers.length === 0 && (
              <tr>
                <td className="p-4 text-center text-muted-foreground" colSpan={8}>
                  Пользователи не найдены
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="text-sm text-muted-foreground">
        Показано {filteredUsers.length} из {users.length} пользователей
      </div>
    </div>
  );
}


