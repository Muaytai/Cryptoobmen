import React from 'react';
import Select, {
  components,
  SingleValueProps,
  OptionProps,
  SingleValue,
  ActionMeta,
  StylesConfig,
  GroupBase
} from 'react-select';

interface OptionType {
  value: string;
  label: string;
  icon: string; // путь к иконке
}

const options: OptionType[] = [
  {value: 'usdt', label: 'USDT (TRC20)', icon: '/images/profile/vector-usdt.svg'},
  {value: 'btc', label: 'Bitcoin', icon: '/images/profile/bitcoin.svg'},
  {value: 'eth', label: 'Ethereum', icon: '/images/profile/ethereum.svg'},
];

const CustomSingleValue = (props: SingleValueProps<OptionType>) => (
  <components.SingleValue {...props}>
    <img
      src={props.data.icon}
      alt={props.data.label}
      style={{width: 20, height: 20, marginRight: 8}}
    />
    {props.data.label}
  </components.SingleValue>
);

const CustomOption = (props: OptionProps<OptionType>) => (
  <components.Option {...props}>
    <img
      src={props.data.icon}
      alt={props.data.label}
      style={{width: 20, height: 20, marginRight: 8}}
    />
    {props.data.label}
  </components.Option>
);

const FormSelect = () => {
  const handleChange = (
    newValue: SingleValue<OptionType>,
    _actionMeta: ActionMeta<OptionType>
  ) => {
    console.log('Выбрано:', newValue);
  };

  const customStyles: StylesConfig<OptionType, false, GroupBase<OptionType>> = {
    control: (provided) => ({
      ...provided,
      backgroundColor: '#1f1f23',
      borderColor: '#4b5563',
      borderRadius: '12px',
      padding: '8px 12px',
      color: '#f3f4f6',
    }),
    option: (provided, state) => ({
      ...provided,
      backgroundColor: state.isSelected ? '#7c3aed' : '#2a2a31',
      color: '#f3f4f6',
      padding: '10px',
    }),
  };

  return (
    <Select
      options={options}
      components={{SingleValue: CustomSingleValue, Option: CustomOption}}
      styles={customStyles}
      onChange={handleChange}
      placeholder="Выберите способ"
      isMulti={false} // важно!
    />
  );
};

export default FormSelect;
