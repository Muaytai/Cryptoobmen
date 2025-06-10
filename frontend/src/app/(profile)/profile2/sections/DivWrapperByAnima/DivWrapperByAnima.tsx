import React, { JSX } from "react";
import { Button } from "../../components/ui/button";
import { Card, CardContent } from "../../components/ui/card";
import {
  ToggleGroup,
  ToggleGroupItem,
} from "../../components/ui/toggle-group";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import styles from "./DivWrapperByAnima.module.css";
import {clsx} from "clsx";

const cryptoData = [
  {
    id: "btc",
    name: "BTC",
    fullName: "Bitcoin",
    image: "/images/profile/image-2-2.png",
    data: [
      { date: '06:00', value: 76000 },
      { date: '12:00', value: 77000 },
      { date: '18:00', value: 76500 },
      { date: '00:00', value: 78000 },
    ],
  },
  {
    id: "eth",
    name: "ETH",
    fullName: "Ethereum",
    image: "/images/profile/image-2-1.png",
    data: [
      { date: '06:00', value: 1400 },
      { date: '12:00', value: 1500 },
      { date: '18:00', value: 1600 },
      { date: '00:00', value: 1800 },
    ],
  },
  {
    id: "usdt",
    name: "USDT",
    fullName: "Tether",
    image: "/images/profile/image-2.png",
    data: [
      { date: '06:00', value: 0.923 },
      { date: '12:00', value: 0.924 },
      { date: '18:00', value: 0.925 },
      { date: '00:00', value: 0.927 },
    ],
  },
];

const timePeriods = [
  { value: "1y", label: "1г" },
  { value: "6m", label: "6м" },
  { value: "1m", label: "1м" },
  { value: "1w", label: "1н" },
  { value: "1d", label: "1д" },
  { value: "1h", label: "1ч" },
];

export const DivWrapperByAnima = (): JSX.Element => {
  return (
    <section className={styles.container}>
      <h2 className="text-violet-600 text-3xl font-normal mb-8 [font-family:'Manrope',Helvetica]">
        Инвестиции
      </h2>

      <div className={styles.cryptoGrid}>
        {cryptoData.map((crypto) => (
          <Card key={crypto.id} className={clsx(styles.cryptoCard, "!bg-card")}>
            <CardContent className={styles.cardContent}>
              <div className={styles.cardHeader}>
                <div className={styles.cryptoInfo}>
                  <img
                    className={styles.cryptoImage}
                    alt={crypto.name}
                    src={crypto.image}
                  />
                  <div>
                    <div className={clsx(styles.cryptoName, "!text-subcard-text")}>{crypto.name}</div>
                    <div className={clsx(styles.cryptoFullName, "!text-subcard-text/80")}>{crypto.fullName}</div>
                  </div>
                </div>

                {/* Time Period Toggle */}
                <ToggleGroup
                  type="single"
                  defaultValue="1d"
                  className="bg-subcard rounded-[15px]"
                >
                  {timePeriods.map((period, i) => (
                    <ToggleGroupItem
                      key={i}
                      value={period.value}
                      className={`px-2.5 py-[9px] text-lg font-normal [font-family:'Manrope',Helvetica] ${
                        period.value === "1d"
                          ? "!bg-violet-600 font-medium"
                          : "text-subcard-text"
                      } ${i === 0 ? "rounded-l-[15px]" : ""} ${
                        i === timePeriods.length - 1 ? "rounded-r-[15px]" : ""
                      }`}
                    >
                      {period.label}
                    </ToggleGroupItem>
                  ))}
                </ToggleGroup>
              </div>

              <div className={styles.chartContainer}>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={crypto.data}>
                    <defs>
                      <linearGradient id={`color${crypto.id}`} x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#9c6bff" stopOpacity={0.8}/>
                        <stop offset="95%" stopColor="#9c6bff" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#2f2f3b"/>
                    <XAxis
                      dataKey="date"
                      stroke="#a2a2b3"
                      tick={{fill: '#a2a2b3'}}
                    />
                    <YAxis
                      stroke="#a2a2b3"
                      tick={{fill: '#a2a2b3'}}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#2f2f3b',
                        border: 'none',
                        borderRadius: '15px',
                        color: '#eaeaf2'
                      }}
                    />
                    <Area
                      type="monotone"
                      dataKey="value"
                      stroke="#9c6bff"
                      fillOpacity={1}
                      fill={`url(#color${crypto.id})`}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>

              {/* Stats Section */}
              <div className="w-full h-12 bg-gray-100 rounded-[15px] mb-5 !bg-subcard flex items-center justify-between px-5">
                <div className="inline-flex items-center gap-2.5">
                  <div className="font-normal text-subcard-text text-sm [font-family:'Manrope',Helvetica]">
                    День:
                  </div>
                  <div className="font-normal text-subcard-text text-sm [font-family:'Manrope',Helvetica]">
                    0.00%
                  </div>
                </div>

                <div className="inline-flex items-center gap-2.5">
                  <div className="font-normal text-subcard-text text-sm [font-family:'Manrope',Helvetica]">
                    Месяц:
                  </div>
                  <div className="font-normal text-subcard-text text-sm [font-family:'Manrope',Helvetica]">
                    00.00%
                  </div>
                </div>

                <div className="inline-flex items-center gap-2.5">
                  <div className="font-normal text-subcard-text text-sm [font-family:'Manrope',Helvetica]">
                    Общий:
                  </div>
                  <div className="font-normal text-subcard-text text-sm [font-family:'Manrope',Helvetica]">
                    000.00%
                  </div>
                </div>
              </div>

              {/* Investment Info */}
              <div className="w-full flex justify-between mb-5 text-subcard-text">
                <div className="flex flex-col items-start gap-[5px]">
                  <div className="font-normal text-sm [font-family:'Manrope',Helvetica]">
                    Дата инвестирования:
                  </div>
                  <div className="font-normal  text-sm [font-family:'Manrope',Helvetica]">
                    00.00.0000
                  </div>
                </div>

                <div className="flex flex-col items-center gap-[5px]">
                  <div className="font-normal text-sm [font-family:'Manrope',Helvetica]">
                    Торгует:
                  </div>
                  <div className="font-normal text-sm [font-family:'Manrope',Helvetica]">
                    <span className="font-medium">Дней:</span>
                    <span> 0</span>
                  </div>
                </div>

                <div className="flex flex-col items-end gap-[5px]">
                  <div className="font-normal text-sm [font-family:'Manrope',Helvetica]">
                    Сумма:
                  </div>
                  <div className="font-normal text-sm [font-family:'Manrope',Helvetica]">
                    000 USDT
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-5">
                <Button
                  className="flex-1 md:h-[48px] bg-violet-600 text-white rounded-[15px]  py-[15px] h-auto">
                  <span className="font-medium text-lg text-center leading-[18px] [font-family:'Manrope',Helvetica]">
                    Инвестировать
                  </span>
                </Button>

                <Button
                  variant="outline"
                  className="flex-1 md:h-[48px] bg-transparent text-subcard-text bg-subcard rounded-[15px] border-2 border-solid border-violet-600 py-[15px] h-auto"
                >
                  <span className="font-medium text-lg text-center leading-[18px] [font-family:'Manrope',Helvetica]">
                    Вывести
                  </span>
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </section>
  );
};
