"use client";

import React, { useState } from "react";
// Используем простые иконки вместо heroicons

interface GuideSection {
  id: string;
  title: string;
  content: React.ReactNode;
  icon: string;
}

const AdminGuide: React.FC = () => {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set());

  const toggleSection = (sectionId: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(sectionId)) {
      newExpanded.delete(sectionId);
    } else {
      newExpanded.add(sectionId);
    }
    setExpandedSections(newExpanded);
  };

  const sections: GuideSection[] = [
    {
      id: "overview",
      title: "Обзор возможностей администратора",
      icon: "📋",
      content: (
        <div className="space-y-4">
          <div className="bg-blue-50 p-4 rounded-lg border-l-4 border-blue-400">
            <h4 className="font-semibold text-blue-900 mb-2">Ваши права как администратора сайта:</h4>
            <ul className="space-y-2 text-blue-800">
              <li>• Управление пользователями и их профилями</li>
              <li>• Мониторинг и управление транзакциями</li>
              <li>• Управление кошельками и балансами</li>
              <li>• Проверка KYC документов</li>
              <li>• Управление криптовалютами и курсами обмена</li>
              <li>• Доступ к аналитике и отчетам</li>
            </ul>
          </div>
          <div className="bg-yellow-50 p-4 rounded-lg border-l-4 border-yellow-400">
            <h4 className="font-semibold text-yellow-900 mb-2">⚠️ Важные ограничения:</h4>
            <ul className="space-y-1 text-yellow-800">
              <li>• Вы НЕ имеете доступа к Django Admin (только суперпользователи)</li>
              <li>• Не можете удалять системные данные без подтверждения</li>
              <li>• Все действия логируются для аудита</li>
            </ul>
          </div>
        </div>
      ),
    },
    {
      id: "user-management",
      title: "Управление пользователями",
      icon: "👥",
      content: (
        <div className="space-y-4">
          <div className="bg-green-50 p-4 rounded-lg">
            <h4 className="font-semibold text-green-900 mb-2">Что вы можете делать:</h4>
            <ul className="space-y-2 text-green-800">
              <li>• Просматривать список всех пользователей</li>
              <li>• Проверять статус верификации (email, KYC)</li>
              <li>• Просматривать профили пользователей</li>
              <li>• Отслеживать активность пользователей</li>
            </ul>
          </div>
          <div className="bg-orange-50 p-4 rounded-lg">
            <h4 className="font-semibold text-orange-900 mb-2">Как реагировать на проблемы:</h4>
            <div className="space-y-3 text-orange-800">
              <div>
                <strong>Подозрительная активность:</strong>
                <ul className="ml-4 mt-1 space-y-1">
                  <li>• Проверьте историю транзакций пользователя</li>
                  <li>• Обратите внимание на IP-адреса и устройства</li>
                  <li>• При необходимости заблокируйте аккаунт (через Django Admin)</li>
                </ul>
              </div>
              <div>
                <strong>Жалобы пользователей:</strong>
                <ul className="ml-4 mt-1 space-y-1">
                  <li>• Изучите детали проблемы в профиле пользователя</li>
                  <li>• Проверьте связанные транзакции</li>
                  <li>• Свяжитесь с пользователем для уточнения</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      ),
    },
    {
      id: "transactions",
      title: "Управление транзакциями",
      icon: "💳",
      content: (
        <div className="space-y-4">
          <div className="bg-blue-50 p-4 rounded-lg">
            <h4 className="font-semibold text-blue-900 mb-2">Мониторинг транзакций:</h4>
            <ul className="space-y-2 text-blue-800">
              <li>• Отслеживание депозитов, выводов и обменов</li>
              <li>• Проверка статусов транзакций</li>
              <li>• Анализ подозрительных операций</li>
              <li>• Управление застрявшими транзакциями</li>
            </ul>
          </div>
          <div className="bg-red-50 p-4 rounded-lg">
            <h4 className="font-semibold text-red-900 mb-2">🚨 Критические ситуации:</h4>
            <div className="space-y-3 text-red-800">
              <div>
                <strong>Застрявшие транзакции (pending &gt; 24 часов):</strong>
                <ul className="ml-4 mt-1 space-y-1">
                  <li>• Проверьте статус в блокчейне</li>
                  <li>• Свяжитесь с технической поддержкой</li>
                  <li>• При необходимости отмените транзакцию</li>
                </ul>
              </div>
              <div>
                <strong>Неудачные транзакции (failed):</strong>
                <ul className="ml-4 mt-1 space-y-1">
                  <li>• Проверьте причину ошибки</li>
                  <li>• Убедитесь, что средства не списаны</li>
                  <li>• Предложите пользователю повторить операцию</li>
                </ul>
              </div>
              <div>
                <strong>Подозрительные крупные транзакции:</strong>
                <ul className="ml-4 mt-1 space-y-1">
                  <li>• Проверьте KYC статус пользователя</li>
                  <li>• Изучите историю транзакций</li>
                  <li>• При необходимости запросите дополнительную верификацию</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      ),
    },
    {
      id: "wallets",
      title: "Управление кошельками",
      icon: "👛",
      content: (
        <div className="space-y-4">
          <div className="bg-purple-50 p-4 rounded-lg">
            <h4 className="font-semibold text-purple-900 mb-2">Мониторинг кошельков:</h4>
            <ul className="space-y-2 text-purple-800">
              <li>• Отслеживание балансов пользователей</li>
              <li>• Проверка адресов кошельков</li>
              <li>• Мониторинг пополнений и выводов</li>
              <li>• Анализ активности кошельков</li>
            </ul>
          </div>
          <div className="bg-yellow-50 p-4 rounded-lg">
            <h4 className="font-semibold text-yellow-900 mb-2">⚠️ Проблемы с кошельками:</h4>
            <div className="space-y-3 text-yellow-800">
              <div>
                <strong>Нулевые или отрицательные балансы:</strong>
                <ul className="ml-4 mt-1 space-y-1">
                  <li>• Проверьте историю транзакций</li>
                  <li>• Убедитесь в корректности расчетов</li>
                  <li>• При необходимости восстановите баланс</li>
                </ul>
              </div>
              <div>
                <strong>Неактивные кошельки:</strong>
                <ul className="ml-4 mt-1 space-y-1">
                  <li>• Проверьте последнюю активность</li>
                  <li>• Свяжитесь с пользователем</li>
                  <li>• Рассмотрите возможность архивирования</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      ),
    },
    {
      id: "kyc-documents",
      title: "KYC Документы",
      icon: "📄",
      content: (
        <div className="space-y-4">
          <div className="bg-green-50 p-4 rounded-lg">
            <h4 className="font-semibold text-green-900 mb-2">Процесс верификации:</h4>
            <ul className="space-y-2 text-green-800">
              <li>• Проверка документов, удостоверяющих личность</li>
              <li>• Верификация адреса проживания</li>
              <li>• Проверка соответствия данных в профиле</li>
              <li>• Одобрение или отклонение заявок</li>
            </ul>
          </div>
          <div className="bg-blue-50 p-4 rounded-lg">
            <h4 className="font-semibold text-blue-900 mb-2">Критерии одобрения:</h4>
            <ul className="space-y-2 text-blue-800">
              <li>• Документы должны быть четкими и читаемыми</li>
              <li>• Данные в документах должны совпадать с профилем</li>
              <li>• Документы не должны быть просроченными</li>
              <li>• Нет признаков подделки или редактирования</li>
            </ul>
          </div>
          <div className="bg-orange-50 p-4 rounded-lg">
            <h4 className="font-semibold text-orange-900 mb-2">Как реагировать на отклонения:</h4>
            <ul className="space-y-2 text-orange-800">
              <li>• Укажите конкретную причину отклонения</li>
              <li>• Предложите пользователю исправить ошибки</li>
              <li>• Предоставьте инструкции по повторной подаче</li>
              <li>• Ведите историю всех решений по верификации</li>
            </ul>
          </div>
        </div>
      ),
    },
    {
      id: "crypto-management",
      title: "Управление криптовалютами",
      icon: "💰",
      content: (
        <div className="space-y-4">
          <div className="bg-indigo-50 p-4 rounded-lg">
            <h4 className="font-semibold text-indigo-900 mb-2">Управление активами:</h4>
            <ul className="space-y-2 text-indigo-800">
              <li>• Добавление новых криптовалют</li>
              <li>• Обновление курсов обмена</li>
              <li>• Настройка торговых пар</li>
              <li>• Мониторинг ликвидности</li>
            </ul>
          </div>
          <div className="bg-red-50 p-4 rounded-lg">
            <h4 className="font-semibold text-red-900 mb-2">🚨 Критические ситуации:</h4>
            <div className="space-y-3 text-red-800">
              <div>
                <strong>Резкие изменения курсов:</strong>
                <ul className="ml-4 mt-1 space-y-1">
                  <li>• Проверьте источник курса</li>
                  <li>• При необходимости приостановите торговлю</li>
                  <li>• Уведомите пользователей об изменениях</li>
                </ul>
              </div>
              <div>
                <strong>Проблемы с сетью блокчейна:</strong>
                <ul className="ml-4 mt-1 space-y-1">
                  <li>• Приостановите депозиты и выводы</li>
                  <li>• Уведомите пользователей о задержках</li>
                  <li>• Следите за восстановлением сети</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      ),
    },
    {
      id: "security",
      title: "Безопасность и мониторинг",
      icon: "🔒",
      content: (
        <div className="space-y-4">
          <div className="bg-red-50 p-4 rounded-lg border-l-4 border-red-400">
            <h4 className="font-semibold text-red-900 mb-2">🚨 Немедленные действия при подозрительной активности:</h4>
            <ul className="space-y-2 text-red-800">
              <li>• Заблокировать подозрительные аккаунты</li>
              <li>• Приостановить все транзакции пользователя</li>
              <li>• Связаться с технической поддержкой</li>
              <li>• Документировать все действия</li>
            </ul>
          </div>
          <div className="bg-yellow-50 p-4 rounded-lg">
            <h4 className="font-semibold text-yellow-900 mb-2">Регулярный мониторинг:</h4>
            <ul className="space-y-2 text-yellow-800">
              <li>• Проверка необычных паттернов транзакций</li>
              <li>• Мониторинг множественных аккаунтов с одного IP</li>
              <li>• Отслеживание крупных операций</li>
              <li>• Анализ жалоб пользователей</li>
            </ul>
          </div>
          <div className="bg-blue-50 p-4 rounded-lg">
            <h4 className="font-semibold text-blue-900 mb-2">Документирование:</h4>
            <ul className="space-y-2 text-blue-800">
              <li>• Ведите журнал всех административных действий</li>
              <li>• Сохраняйте скриншоты подозрительной активности</li>
              <li>• Записывайте причины принятых решений</li>
              <li>• Регулярно создавайте отчеты о безопасности</li>
            </ul>
          </div>
        </div>
      ),
    },
    {
      id: "support",
      title: "Поддержка пользователей",
      icon: "🆘",
      content: (
        <div className="space-y-4">
          <div className="bg-green-50 p-4 rounded-lg">
            <h4 className="font-semibold text-green-900 mb-2">Типичные запросы поддержки:</h4>
            <ul className="space-y-2 text-green-800">
              <li>• Проблемы с депозитами и выводами</li>
              <li>• Запросы на ускорение верификации</li>
              <li>• Вопросы по курсам обмена</li>
              <li>• Технические проблемы с кошельками</li>
            </ul>
          </div>
          <div className="bg-blue-50 p-4 rounded-lg">
            <h4 className="font-semibold text-blue-900 mb-2">Процесс обработки запросов:</h4>
            <ol className="space-y-2 text-blue-800">
              <li>1. Изучите детали проблемы в профиле пользователя</li>
              <li>2. Проверьте связанные транзакции и кошельки</li>
              <li>3. Свяжитесь с пользователем для уточнения</li>
              <li>4. При необходимости эскалируйте в техническую поддержку</li>
              <li>5. Предоставьте решение и объясните причины</li>
            </ol>
          </div>
          <div className="bg-purple-50 p-4 rounded-lg">
            <h4 className="font-semibold text-purple-900 mb-2">Эскалация проблем:</h4>
            <ul className="space-y-2 text-purple-800">
              <li>• Технические проблемы → Разработчики</li>
              <li>• Финансовые споры → Финансовый отдел</li>
              <li>• Правовые вопросы → Юридический отдел</li>
              <li>• Критические инциденты → Руководство</li>
            </ul>
          </div>
        </div>
      ),
    },
  ];

  return (
    <div className="bg-white rounded-lg shadow-sm border p-6">
      <div className="flex items-center gap-3 mb-6">
        <span className="text-3xl">📚</span>
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Руководство администратора</h2>
          <p className="text-gray-600 mt-1">
            Инструкции по управлению платформой и реагированию на различные ситуации
          </p>
        </div>
      </div>

      <div className="space-y-4">
        {sections.map((section) => {
          const isExpanded = expandedSections.has(section.id);
          
          return (
            <div key={section.id} className="border rounded-lg overflow-hidden">
              <button
                onClick={() => toggleSection(section.id)}
                className="w-full px-6 py-4 text-left bg-gray-50 hover:bg-gray-100 transition-colors flex items-center justify-between"
              >
                <div className="flex items-center gap-3">
                  <span className="text-2xl">{section.icon}</span>
                  <span className="font-semibold text-gray-900">{section.title}</span>
                </div>
                {isExpanded ? (
                  <span className="text-gray-500">▼</span>
                ) : (
                  <span className="text-gray-500">▶</span>
                )}
              </button>
              
              {isExpanded && (
                <div className="px-6 py-4 border-t bg-white">
                  {section.content}
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div className="mt-8 p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border">
        <h3 className="font-semibold text-gray-900 mb-2">💡 Полезные советы:</h3>
        <ul className="space-y-2 text-gray-700">
          <li>• Всегда проверяйте детали перед принятием важных решений</li>
          <li>• Документируйте все административные действия</li>
          <li>• При сомнениях обращайтесь к руководству или технической поддержке</li>
          <li>• Регулярно обновляйте свои знания о новых функциях платформы</li>
          <li>• Следите за обновлениями в области безопасности криптовалют</li>
        </ul>
      </div>
    </div>
  );
};

export default AdminGuide;
