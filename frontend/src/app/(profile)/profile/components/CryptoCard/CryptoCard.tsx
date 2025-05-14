import React from "react";
import { Button } from "../../components/ui/button";
import { Card, CardContent } from "../../components/ui/card";
import { ToggleGroup, ToggleGroupItem } from "../../components/ui/toggle-group";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import styles from "./CryptoCard.module.css";
import { TimePeriodSelector } from "../TimePeriodSelector/TimePeriodSelector";
import { StatsRow } from "../StatsRow/StatsRow";
import { InvestmentInfo } from "../InvestmentInfo/InvestmentInfo";

interface CryptoCardProps {
  id: string;
  name: string;
  fullName: string;
  image: string;
  data: Array<{ date: string; value: number }>;
}

export const CryptoCard: React.FC<CryptoCardProps> = ({ id, name, fullName, image, data }) => {
  return (
    <Card className={styles.cryptoCard}>
      <CardContent className={styles.cardContent}>
        <div className={styles.cardHeader}>
          <div className={styles.cryptoInfo}>
            <img
              className={styles.cryptoImage}
              alt={name}
              src={image}
            />
            <div>
              <div className={styles.cryptoName}>{name}</div>
              <div className={styles.cryptoFullName}>{fullName}</div>
            </div>
          </div>

          <TimePeriodSelector />
        </div>

        <div className={styles.chartContainer}>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={data}>
              <defs>
                <linearGradient id={`color${id}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#9c6bff" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#9c6bff" stopOpacity={0}/>
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
                fill={`url(#color${id})`}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <StatsRow />
        <InvestmentInfo />

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
  );
};