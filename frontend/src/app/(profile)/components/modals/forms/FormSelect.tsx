import Select, {
  components,
  SingleValueProps,
  OptionProps,
  ClassNamesConfig,
} from "react-select";
import styles from "./formField.module.css";
import { OptionType } from "../types/types";
import Image from "next/image";


const CustomSingleValue = (props: SingleValueProps<OptionType>) => (
  <components.SingleValue {...props} className="flex items-center">
    <Image
      width={16}
      height={16}
      src={props.data.icon}
      alt={props.data.label}
      className="w-4 h-4 mr-2"
    />
    <span className="text-subcard-text">{props.data.label}</span>
  </components.SingleValue>
);

const CustomOption = (props: OptionProps<OptionType>) => (
  <components.Option {...props}>
    <div className="flex items-center gap-2 px-1 py-1">
      <Image
        width={16}
        height={16}
        src={props.data.icon}
        alt={props.data.label}
        className="w-4 h-4"
      />
      <span className="text-subcard-text">{props.data.label}</span>
    </div>
  </components.Option>
);

interface Props {
  error?: string;
  label: string;
  required?: boolean;
  options: OptionType[];
  value: string;
  onChange: (value: string) => void;
  onBlur?: () => void;
  name?: string;
}

const FormSelect = ({label, required, error, options, value, onChange, onBlur, name}: Props) => {
  const selectedOption =
    options.find((option) => option.value === value) ?? null;

  const handleChange = (newValue: OptionType | null) => {
    onChange(newValue?.value ?? "");
  };

  const classNames: ClassNamesConfig<OptionType> = {
    control: ({ isFocused }) =>
      `bg-card border rounded-lg py-2 px-3 mt-1 text-gray-100 ${
        isFocused
          ? "ring-2 ring-violet-500 border-violet-500"
          : "ring-2 ring-gray-500 border-gray-500"
      }`,
    option: ({ isSelected }) =>
      `bg-subcard p-1 text-subcard-text  items-center ${
        isSelected ? "bg-violet-400" : "bg-gray-800 hover:bg-gray-400"
      }`,
    menuList: () => "bg-subcard rounded-xl text-subcard-text mt-1 shadow-lg",
    singleValue: () => "flex w-full text-subcard-text",
    placeholder: () => "text-gray-400",
    dropdownIndicator: () =>
      "flex w-full text-subcard-text hover:text-gray-300",
    indicatorSeparator: () => "",
  };

  return (
    <label className={styles.label}>
      <span className="text-subcard-text/70">
        {required && "*"}
        {label}
      </span>
      <Select
        inputId={name}
        name={name}
        options={options}
        components={{ SingleValue: CustomSingleValue, Option: CustomOption }}
        classNames={classNames}
        value={selectedOption}
        onChange={(newValue) => handleChange(newValue as OptionType | null)}
        onBlur={onBlur}
        placeholder="Выберите способ вывода"
        isMulti={false}
        unstyled
      />
      {error && <span className="text-red-500 text-xs mt-1">{error}</span>}
    </label>
  );
};

export default FormSelect;
