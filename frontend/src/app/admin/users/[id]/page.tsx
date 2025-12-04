"use client";

import React, { useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import api from "@/lib/api/fetch";
import { useAuthStore } from "@/store/useAuthStore";

type AdminUserDetails = {
  id: number | string;
  email: string;
  username: string;
  is_site_admin?: boolean;
};

type AdminUserDocument = {
  id: number | string;
  document_type: string;
  status: string;
  uploaded_at?: string;
};

export default function AdminUserDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const id = useMemo(() => String(params?.id || ""), [params]);
  const user = useAuthStore((s) => s.user);
  const isLoading = useAuthStore((s) => s.isLoading);
  const checkAuthStatus = useAuthStore((s) => s.checkAuthStatus);
  const getAuthHeaders = useAuthStore((s) => s.getAuthHeaders);

  const [details, setDetails] = useState<AdminUserDetails | null>(null);
  const [documents, setDocuments] = useState<AdminUserDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user && !isLoading) {
      checkAuthStatus().catch(() => {});
    }
  }, [user, isLoading, checkAuthStatus]);

  useEffect(() => {
    if (!isLoading && user && !user.is_site_admin) {
      router.replace("/me");
    }
  }, [user, isLoading, router]);

  useEffect(() => {
    const load = async () => {
      if (!id) return;
      setLoading(true);
      setError(null);
      try {
        const headers = getAuthHeaders();
        const userRes = await api.get<AdminUserDetails>(`/accounts/users/${id}/`, { headers });
        const docsRes = await api.get<AdminUserDocument[]>(`/accounts/documents/?user=${id}`, { headers });
        const userData =
          (userRes as { data?: AdminUserDetails }).data ?? (userRes as AdminUserDetails);
        const docsDataRaw =
          (docsRes as { data?: AdminUserDocument[] }).data ?? (docsRes as AdminUserDocument[]);
        setDetails(userData);
        setDocuments(Array.isArray(docsDataRaw) ? docsDataRaw : []);
      } catch (e: unknown) {
        const message = e instanceof Error ? e.message : null;
        setError(message || "Не удалось загрузить данные пользователя");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [id, getAuthHeaders]);

  if (isLoading || !user) return <div className="p-6">Загрузка…</div>;
  if (!user.is_site_admin) return null;
  if (loading) return <div className="p-6">Загрузка данных пользователя…</div>;
  if (error) return <div className="p-6 text-red-500">{error}</div>;

  return (
    <div className="p-6 space-y-6">
      <div>
        <button className="text-sm text-primary" onClick={() => router.back()}>
          ← Назад
        </button>
      </div>

      <div>
        <h1 className="text-2xl font-semibold mb-2">Пользователь: {details?.email}</h1>
        <div className="text-sm text-muted-foreground">
          ID: {details?.id} · Username: {details?.username} · Site Admin: {details?.is_site_admin ? "Да" : "Нет"}
        </div>
      </div>

      <section>
        <h2 className="text-lg font-medium mb-3">Документы</h2>
        <div className="w-full overflow-x-auto border rounded-md">
          <table className="min-w-[680px] w-full text-sm">
            <thead className="bg-muted/40">
              <tr>
                <th className="text-left p-3">Тип</th>
                <th className="text-left p-3">Статус</th>
                <th className="text-left p-3">Загружен</th>
              </tr>
            </thead>
            <tbody>
              {documents.map((d) => (
                <tr key={d.id} className="border-t">
                  <td className="p-3">{d.document_type}</td>
                  <td className="p-3">{d.status}</td>
                  <td className="p-3">{d.uploaded_at?.slice(0, 19).replace("T", " ") || "—"}</td>
                </tr>
              ))}
              {documents.length === 0 && (
                <tr>
                  <td className="p-4 text-center text-muted-foreground" colSpan={3}>
                    Документы не найдены
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}


