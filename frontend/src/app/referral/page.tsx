'use client';

import { Sidebar } from "@/components/layout/Sidebar";

export default function ReferralPage() {
  return (
    <div className="flex">
      {/* Sidebar */}
      <Sidebar />
      
      {/* Основной контент */}
      <div className="flex-1 p-6">
        <h1 className="text-2xl font-bold mb-6">Реф. программа</h1>
        
        {/* Реферальная ссылка */}
        <div className="bg-[#181828] rounded-lg p-4 mb-6 border border-[#23233a]">
          <h2 className="text-sm text-gray-400 mb-2">Реферальная ссылка</h2>
          <div className="flex">
            <input 
              type="text" 
              value="https://cryptx.com/referral/USERNAME" 
              readOnly 
              className="bg-[#23233a] text-white px-3 py-2 rounded-l border-r border-[#23233a] flex-1"
            />
            <button className="bg-[#7c3aed] text-white px-4 py-2 rounded-r">
              Копировать
            </button>
          </div>
        </div>
        
        {/* Статистика */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div className="bg-[#181828] rounded-lg p-4 border border-[#23233a]">
            <h3 className="text-sm text-gray-400 mb-2">Количество приглашенных</h3>
            <div className="text-2xl font-bold">5</div>
          </div>
          <div className="bg-[#181828] rounded-lg p-4 border border-[#23233a]">
            <h3 className="text-sm text-gray-400 mb-2">Процент дохода с рефералов</h3>
            <div className="text-2xl font-bold text-[#a855f7]">50%</div>
          </div>
        </div>
        
        {/* Таблица рефералов */}
        <div className="bg-[#181828] rounded-lg p-4 border border-[#23233a]">
          <h2 className="text-xl font-bold mb-4">Таблица рефералов</h2>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-[#23233a]">
                  <th className="text-left p-2">Уровень</th>
                  <th className="text-left p-2">Дата регистрации</th>
                  <th className="text-left p-2">Количество рефералов</th>
                  <th className="text-left p-2">Почта</th>
                  <th className="text-left p-2">Прибыль</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-[#23233a]">
                  <td className="p-2">1</td>
                  <td className="p-2">26.01.2025</td>
                  <td className="p-2">3</td>
                  <td className="p-2">u*****@gmail.com</td>
                  <td className="p-2 text-[#a855f7]">4.71 USDT</td>
                </tr>
                <tr className="border-b border-[#23233a]">
                  <td className="p-2">1</td>
                  <td className="p-2">07.02.2025</td>
                  <td className="p-2">0</td>
                  <td className="p-2">k*****@mail.ru</td>
                  <td className="p-2">0.0 USDT</td>
                </tr>
                <tr>
                  <td className="p-2">1</td>
                  <td className="p-2">18.03.2025</td>
                  <td className="p-2">2</td>
                  <td className="p-2">a*****@yandex.ru</td>
                  <td className="p-2 text-[#a855f7]">1.25 USDT</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
} 