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

const cryptoData = [
  {
    id: "btc",
    name: "BTC",
    fullName: "Bitcoin",
    image: "/image/profile/image-2-2.png",
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
    image: "/image/profile/image-2-1.png",
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
    image: "/image/profile/image-2.png",
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
      <h2 className={styles.title}>Инвестиции</h2>

      <div className={styles.cryptoGrid}>
        {cryptoData.map((crypto) => (
          <Card key={crypto.id} className={styles.cryptoCard}>
            <CardContent className={styles.cardContent}>
              <div className={styles.cardHeader}>
                <div className={styles.cryptoInfo}>
                  <img
                    className={styles.cryptoImage}
                    alt={crypto.name}
                    src={crypto.image}
                  />
                  <div>
                    <div className={styles.cryptoName}>{crypto.name}</div>
                    <div className={styles.cryptoFullName}>{crypto.fullName}</div>
                  </div>
                </div>

                <ToggleGroup
                  type="single"
                  defaultValue="1d"
                  className={styles.toggleGroup}
                >
                  {timePeriods.map((period) => (
                    <ToggleGroupItem
                      key={period.value}
                      value={period.value}
                      className={styles.toggleItem}
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
                        <stop offset="5%" stopColor="#9c6bff" stopOpacity={0.8} />
                        <stop offset="95%" stopColor="#9c6bff" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#2f2f3b" />
                    <XAxis
                      dataKey="date"
                      stroke="#a2a2b3"
                      tick={{ fill: '#a2a2b3' }}
                    />
                    <YAxis
                      stroke="#a2a2b3"
                      tick={{ fill: '#a2a2b3' }}
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

              <div className={styles.statsRow}>
                <div className={styles.statItem}>
                  <span>День:</span>
                  <span>0.00%</span>
                </div>
                <div className={styles.statItem}>
                  <span>Месяц:</span>
                  <span>00.00%</span>
                </div>
                <div className={styles.statItem}>
                  <span>Общий:</span>
                  <span>000.00%</span>
                </div>
              </div>

              <div className={styles.investmentInfo}>
                <div>
                  <span>Дата инвестирования:</span>
                  <span> 00.00.0000</span>
                </div>
                <div>
                  <span>Торгует:</span>
                  <span>Дней: 0</span>
                </div>
                <div>
                  <span>Сумма:</span>
                  <span>000 USDT</span>
                </div>
              </div>

              <div className={styles.actionButtons}>
                <Button className={styles.investButton}>
                  Инвестировать
                </Button>
                <Button className={styles.withdrawButton}>
                  Вывести
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </section>
  );
};
