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
import styles from "./ViewWrapperByAnima.module.css";

export const ViewWrapperByAnima = (): JSX.Element => {
  const data = [
    { date: '11.03', value: 0.07 },
    { date: '15.03', value: 0.08 },
    { date: '19.03', value: 0.075 },
    { date: '23.03', value: 0.09 },
    { date: '27.03', value: 0.085 },
    { date: '31.03', value: 0.095 },
    { date: '04.04', value: 0.09 },
    { date: '08.04', value: 0.085 },
    { date: '12.04', value: 0.09 },
  ];

  const timePeriods = [
    { value: "1y", label: "1 г" },
    { value: "6m", label: "6 м" },
    { value: "1m", label: "1 м" },
    { value: "1w", label: "1 н" },
    { value: "1d", label: "1 д", active: true },
    { value: "1h", label: "1 ч" },
  ];

  return (
    <section className={styles.container}>
      <h2 className={styles.title}>Токены</h2>

      <div className={styles.content}>
        {/* Token Info Card */}
        <Card className={styles.tokenInfoCard}>
          <CardContent className={styles.cardContent}>
            <h3 className={styles.tokenName}>CTokenX</h3>
            <p className={styles.tokenDescription}>
              Утилитарный токен для оплаты внутри платформы
            </p>

            <div className={styles.tokenPrice}>
              <span className={styles.priceValue}>$0,09</span>
              <span className={styles.priceChange}>+2,4%</span>
            </div>

            <div className={styles.statsSection}>
              <p className={styles.statsLabel}>Объём торгов (24ч)</p>
              <p className={styles.statsValue}>$230.000</p>
            </div>

            <div className={styles.statsSection}>
              <p className={styles.statsLabel}>Рыночная капитализация</p>
              <p className={styles.statsValue}>$14.870.000</p>
            </div>

            <div className={styles.statsSection}>
              <p className={styles.statsLabel}>Оборот / Циркуляция</p>
              <p className={styles.statsValue}>210.000.000 CTokenX</p>
            </div>

            <div className={styles.statsSection}>
              <p className={styles.statsLabel}>Максимальное предложение</p>
              <p className={styles.statsValue}>1.000.000.000 CTokenX</p>
            </div>

            <Card className={styles.tokenBalanceCard}>
              <CardContent className={styles.cardContent}>
                <p className={styles.balanceLabel}>Мои токены</p>
                <p className={styles.balanceValue}>50 CTokenX</p>
                <p className={styles.balanceUSDT}>≈ 4.50 USDT</p>

                <div className={styles.balanceActions}>
                  <Button className={`${styles.actionButton} ${styles.primaryButton}`}>
                    Купить
                  </Button>
                  <Button className={`${styles.actionButton} ${styles.outlineButton}`}>
                    Продать
                  </Button>
                </div>
              </CardContent>
            </Card>
          </CardContent>
        </Card>

        {/* Chart Card */}
        <Card className={styles.chartCard}>
          <CardContent className={styles.cardContent}>
            <div className={styles.chartHeader}>
              <div className={styles.tokenIcon} style={{ backgroundImage: 'url(/vector-2.svg)' }} />
              <div className={styles.tokenInfo}>
                <p className={styles.tokenName}>CTokenX</p>
                <p className={styles.tokenDescription}>CTokenX Token</p>
              </div>
            </div>

            <div className={styles.chartControls}>
              <ToggleGroup type="single" defaultValue="1d" className={styles.toggleGroup}>
                {timePeriods.map((period) => (
                  <ToggleGroupItem
                    key={period.value}
                    value={period.value}
                    className={`${styles.toggleItem} ${period.active ? styles.toggleItemActive : ''}`}
                  >
                    {period.label}
                  </ToggleGroupItem>
                ))}
              </ToggleGroup>
            </div>

            <div className={styles.chartContainer}>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data}>
                  <defs>
                    <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
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
                    domain={[0, 0.12]}
                    tickCount={7}
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
                    fill="url(#colorValue)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>
    </section>
  );
};
