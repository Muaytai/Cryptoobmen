import React, {JSX} from "react";
import {Button} from "../../components/ui/button";
import {Card, CardContent} from "../../components/ui/card";
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
import clsx from "clsx";
import styles from "./TokensSection.module.css";

export const TokensSection = (): JSX.Element => {
  const data = [
    {date: '11.03', value: 0.07},
    {date: '15.03', value: 0.08},
    {date: '19.03', value: 0.075},
    {date: '23.03', value: 0.09},
    {date: '27.03', value: 0.085},
    {date: '31.03', value: 0.095},
    {date: '04.04', value: 0.09},
    {date: '08.04', value: 0.085},
    {date: '12.04', value: 0.09},
  ];

  const timePeriods = [
    {value: "1y", label: "1г"},
    {value: "6m", label: "6м"},
    {value: "1m", label: "1м"},
    {value: "1w", label: "1н"},
    {value: "1d", label: "1д", active: true},
    {value: "1h", label: "1ч"},
  ];

  return (
    <section className={styles.container}>
      <h2 className="text-violet-600 text-3xl font-normal mb-8 [font-family:'Manrope',Helvetica]">
        Токены
      </h2>

      <div className={styles.content}>
        {/* Token Info Card */}
        <Card className={clsx(styles.tokenInfoCard, "w-full !bg-card rounded-[15px] md:rounded-[25px] shadow-[0px_0px_20px_#0000004c]")}>
          <CardContent className="!p-0 md:p-5 relative">
            <div className="mb-8 md:mb-12">
              <h3
                className="text-lg md:text-xl font-normal text-[#1a1a1a] dark:text-white [font-family:'Manrope',Helvetica]">
                CTokenX
              </h3>
              <p className="text-xs md:text-sm font-medium text-gray-500 [font-family:'Manrope',Helvetica]">
                Утилитарный токен для оплаты внутри платформы
              </p>
            </div>

            <div className="mb-6 md:mb-8">
              <div className="flex items-center h-9 md:h-11">
                <span
                  className="text-2xl md:text-[32px] font-normal text-[#1a1a1a] dark:text-white [font-family:'Manrope',Helvetica]">
                  $0,09
                </span>
                <span
                  className="ml-3 md:ml-4 text-base md:text-xl font-normal text-emerald-500 [font-family:'Manrope',Helvetica]">
                  +2,4%
                </span>
              </div>
            </div>

            <div className="space-y-6 md:space-y-8">
              <div className="h-[40px] md:h-[52px]">
                <p className="text-xs md:text-sm font-medium text-gray-500 [font-family:'Manrope',Helvetica]">
                  Объём торгов (24ч)
                </p>
                <p
                  className="text-base md:text-xl font-medium text-[#1a1a1a] dark:text-white [font-family:'Manrope',Helvetica] mt-1">
                  $230.000
                </p>
              </div>

              <div className="h-[40px] md:h-[52px]">
                <p className="text-xs md:text-sm font-medium text-gray-500 [font-family:'Manrope',Helvetica]">
                  Рыночная капитализация
                </p>
                <p
                  className="text-base md:text-xl font-medium text-[#1a1a1a] dark:text-white [font-family:'Manrope',Helvetica] mt-1">
                  $14.870.000
                </p>
              </div>

              <div className="h-[40px] md:h-[52px]">
                <p className="text-xs md:text-sm font-medium text-gray-500 [font-family:'Manrope',Helvetica]">
                  Оборот / Циркуляция
                </p>
                <p
                  className="text-base md:text-xl font-medium text-[#1a1a1a] dark:text-white [font-family:'Manrope',Helvetica] mt-1">
                  210.000.000 CTokenX
                </p>
              </div>

              <div className="h-[40px] md:h-[52px]">
                <p className="text-xs md:text-sm font-medium text-gray-500 [font-family:'Manrope',Helvetica]">
                  Максимальное предложение
                </p>
                <p
                  className="text-base md:text-xl font-medium text-[#1a1a1a] dark:text-white [font-family:'Manrope',Helvetica] mt-1">
                  1.000.000.000 CTokenX
                </p>
              </div>
            </div>

            <div
              className="flex justify-between gap-4 mt-6 md:mt-8 p-4 md:p-5 bg-gray-100 dark:bg-gray-800 rounded-[15px]">
              <div className="mb-6 md:mb-8">
                <p className="text-xs md:text-sm font-medium text-gray-500 [font-family:'Manrope',Helvetica]">
                  Мои токены
                </p>
                <p
                  className="text-2xl md:text-[32px] font-medium text-[#1a1a1a] dark:text-white [font-family:'Manrope',Helvetica] mt-1">
                  50 CTokenX
                </p>
                <p className="text-xs md:text-sm font-medium text-gray-500 [font-family:'Manrope',Helvetica] mt-1">
                  ≈ 4.50 USDT
                </p>
              </div>

              <div className="flex flex-col gap-3 md:gap-4">
                <Button
                  className="w-[160px] h-[36px] md:h-[48px] bg-violet-600 rounded-[15px] ">
                <span
                  className="font-medium text-white text-sm md:text-lg text-center [font-family:'Manrope',Helvetica]">
                  Купить
                </span>
                </Button>
                <Button
                  variant="outline"
                  className="w-[160px]  h-[36px] md:h-[48px] rounded-[15px] bg-subcard border-2 border-solid border-violet-600"
                >
                <span
                  className="font-medium text-subcard-text text-sm md:text-lg text-center [font-family:'Manrope',Helvetica]">
                  Продать
                </span>
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Chart Card */}
        <Card className={clsx(styles.chartCard, "!bg-card")}>
          <CardContent className={styles.cardContent}>
            <div className="flex flex-col md:flex-row items-start md:items-center gap-4 md:gap-0 mb-6 md:mb-8">
              <div className="flex items-center gap-3 md:gap-5">
                <div
                  className="w-10 h-10 md:w-12 md:h-12 bg-white dark:bg-gray-800 rounded-3xl bg-[url(/images/profile/vector-5_1.svg)] bg-[100%_100%]"/>
                <div>
                  <p
                    className="text-lg md:text-xl font-normal text-[#1a1a1a] dark:text-white [font-family:'Manrope',Helvetica]">
                    CTokenX
                  </p>
                  <p className="text-xs md:text-sm font-medium text-gray-500 [font-family:'Manrope',Helvetica]">
                    CTokenX Token
                  </p>
                </div>
              </div>

              <div className="w-full md:w-auto md:ml-auto">
                <ToggleGroup
                  type="single"
                  defaultValue="1d"
                  className="bg-gray-100 dark:bg-gray-800 rounded-[15px] h-10 md:h-12 w-full md:w-auto"
                >
                  {timePeriods.map((period) => (
                    <ToggleGroupItem
                      key={period.value}
                      value={period.value}
                      className={`px-2 md:px-2.5 py-2 md:py-[9px] text-sm md:text-lg font-normal ${
                        period.active
                          ? "!bg-violet-600 font-medium"
                          : "text-subcard-text/80 hover:!text-subcard-text"
                      } [font-family:'Manrope',Helvetica]`}
                    >
                      {period.label}
                    </ToggleGroupItem>
                  ))}
                </ToggleGroup>
              </div>
            </div>

            <div className={styles.chartContainer}>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data}>
                  <defs>
                    <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#9c6bff" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="#9c6bff" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#2f2f3b"/>
                  <XAxis
                    dataKey="date"
                    stroke="#a2a2b3"
                    tick={{fill: '#a2a2b3'}}
                    tickMargin={16}
                  />
                  <YAxis
                    stroke="#a2a2b3"
                    tick={{fill: '#a2a2b3'}}
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
