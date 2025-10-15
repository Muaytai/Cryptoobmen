"use client";

import React, { useEffect, useState } from "react";
import api from "@/lib/api/fetch";
import { useAuthStore } from "@/store/useAuthStore";

type DocumentRow = {
  id: number | string;
  user: {
    id: number | string;
    email: string;
    username: string;
  };
  document_type: string;
  document_file: string;
  uploaded_at: string;
  status: string;
  notes?: string;
};

export default function DocumentsTable() {
  const [documents, setDocuments] = useState<DocumentRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterType, setFilterType] = useState("all");
  const [filterStatus, setFilterStatus] = useState("all");
  const getAuthHeaders = useAuthStore((s) => s.getAuthHeaders);

  const fetchDocuments = async () => {
    setLoading(true);
    setError(null);
    try {
      const headers = getAuthHeaders();
      const res: any = await api.get("/accounts/documents/", { headers });
      const data = res?.data ?? res;
      setDocuments(Array.isArray(data) ? data : []);
    } catch (e: any) {
      setError(e?.message || "Не удалось загрузить документы");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, [getAuthHeaders]);

  const filteredDocuments = documents.filter((doc) => {
    const matchesSearch = 
      doc.user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      doc.user.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
      doc.document_type.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesType = 
      filterType === "all" ||
      doc.document_type === filterType;

    const matchesStatus = 
      filterStatus === "all" ||
      doc.status === filterStatus;

    return matchesSearch && matchesType && matchesStatus;
  });

  const updateStatus = async (docId: string | number, newStatus: string, notes?: string) => {
    try {
      const headers = getAuthHeaders();
      await api.patch(`/accounts/documents/${docId}/`, 
        { status: newStatus, notes }, 
        { headers }
      );
      await fetchDocuments();
    } catch (e: any) {
      setError(e?.message || "Не удалось обновить статус документа");
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved': return "bg-green-100 text-green-800";
      case 'pending': return "bg-yellow-100 text-yellow-800";
      case 'rejected': return "bg-red-100 text-red-800";
      default: return "bg-gray-100 text-gray-800";
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'passport': return "bg-blue-100 text-blue-800";
      case 'driver_license': return "bg-purple-100 text-purple-800";
      case 'id_card': return "bg-orange-100 text-orange-800";
      default: return "bg-gray-100 text-gray-800";
    }
  };

  const downloadDocument = (documentFile: string) => {
    // Создаем ссылку для скачивания документа
    const link = document.createElement('a');
    link.href = documentFile;
    link.download = documentFile.split('/').pop() || 'document';
    link.target = '_blank';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  if (loading) return <div className="py-4">Загрузка документов…</div>;
  if (error) return <div className="py-4 text-red-500">{error}</div>;

  return (
    <div className="space-y-4">
      {/* Фильтры и поиск */}
      <div className="flex flex-wrap gap-4 p-4 bg-muted/20 rounded-lg">
        <div className="flex-1 min-w-[200px]">
          <input
            type="text"
            placeholder="Поиск по email, username, типу документа..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full px-3 py-2 border rounded-md text-sm"
          />
        </div>
        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
          className="px-3 py-2 border rounded-md text-sm"
        >
          <option value="all">Все типы</option>
          <option value="passport">Паспорт</option>
          <option value="driver_license">Водительские права</option>
          <option value="id_card">ID карта</option>
        </select>
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="px-3 py-2 border rounded-md text-sm"
        >
          <option value="all">Все статусы</option>
          <option value="pending">В ожидании</option>
          <option value="approved">Одобрено</option>
          <option value="rejected">Отклонено</option>
        </select>
        <button
          onClick={fetchDocuments}
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
              <th className="text-left p-3">Пользователь</th>
              <th className="text-left p-3">Тип документа</th>
              <th className="text-left p-3">Статус</th>
              <th className="text-left p-3">Файл</th>
              <th className="text-left p-3">Загружен</th>
              <th className="text-left p-3">Примечания</th>
              <th className="text-left p-3">Действия</th>
            </tr>
          </thead>
          <tbody>
            {filteredDocuments.map((doc) => (
              <tr key={doc.id} className="border-t hover:bg-muted/40">
                <td className="p-3">
                  <div>
                    <div className="font-medium">{doc.user.email}</div>
                    <div className="text-xs text-muted-foreground">{doc.user.username}</div>
                  </div>
                </td>
                <td className="p-3">
                  <span className={`px-2 py-1 rounded-full text-xs ${getTypeColor(doc.document_type)}`}>
                    {doc.document_type === 'passport' ? 'Паспорт' :
                     doc.document_type === 'driver_license' ? 'Водительские права' :
                     doc.document_type === 'id_card' ? 'ID карта' : doc.document_type}
                  </span>
                </td>
                <td className="p-3">
                  <span className={`px-2 py-1 rounded-full text-xs ${getStatusColor(doc.status)}`}>
                    {doc.status === 'pending' ? 'В ожидании' :
                     doc.status === 'approved' ? 'Одобрено' :
                     doc.status === 'rejected' ? 'Отклонено' : doc.status}
                  </span>
                </td>
                <td className="p-3">
                  <button
                    onClick={() => downloadDocument(doc.document_file)}
                    className="text-blue-600 hover:text-blue-800 text-xs underline"
                  >
                    Скачать
                  </button>
                </td>
                <td className="p-3">
                  <div className="text-xs">
                    <div>{doc.uploaded_at.slice(0, 10)}</div>
                    <div className="text-muted-foreground">{doc.uploaded_at.slice(11, 19)}</div>
                  </div>
                </td>
                <td className="p-3">
                  <div className="text-xs max-w-[200px] truncate">
                    {doc.notes || "—"}
                  </div>
                </td>
                <td className="p-3">
                  <div className="flex gap-2">
                    {doc.status === 'pending' && (
                      <>
                        <button
                          onClick={() => {
                            const notes = prompt("Примечания (необязательно):");
                            updateStatus(doc.id, 'approved', notes || '');
                          }}
                          className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs hover:bg-green-200"
                        >
                          Одобрить
                        </button>
                        <button
                          onClick={() => {
                            const notes = prompt("Причина отклонения:");
                            if (notes) {
                              updateStatus(doc.id, 'rejected', notes);
                            }
                          }}
                          className="px-2 py-1 bg-red-100 text-red-800 rounded text-xs hover:bg-red-200"
                        >
                          Отклонить
                        </button>
                      </>
                    )}
                    <button
                      onClick={() => window.location.href = `/admin/users/${doc.user.id}`}
                      className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs hover:bg-blue-200"
                    >
                      Пользователь
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {filteredDocuments.length === 0 && (
              <tr>
                <td className="p-4 text-center text-muted-foreground" colSpan={7}>
                  Документы не найдены
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="text-sm text-muted-foreground">
        Показано {filteredDocuments.length} из {documents.length} документов
      </div>
    </div>
  );
}
