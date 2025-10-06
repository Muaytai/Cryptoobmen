import React from "react";
import { ToggleGroup, ToggleGroupItem } from "../../components/ui/toggle-group";
import styles from "./TimePeriodSelector.module.css";

const timePeriods = [
  { value: "1y", label: "1 г" },
  { value: "6m", label: "6 м" },
  { value: "1m", label: "1 м" },
  { value: "1w", label: "1 н" },
  { value: "1d", label: "1 д" },
  { value: "1h", label: "1 ч" },
];

export const TimePeriodSelector: React.FC = () => {
  return (
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
  );
};