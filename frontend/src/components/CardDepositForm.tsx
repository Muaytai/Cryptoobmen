'use client';

import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Button, 
  FormControl, 
  FormLabel, 
  Input, 
  Select, 
  VStack, 
  HStack, 
  Text, 
  Heading, 
  useToast, 
  Divider,
  InputGroup,
  InputLeftElement,
  InputRightElement,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
  Tooltip,
  Alert,
  AlertIcon
} from '@chakra-ui/react';
import { InfoIcon } from '@chakra-ui/icons';
import axios from 'axios';
import { useAuthStore } from '@/store/useAuthStore';

interface CardData {
  cardNumber: string;
  cardHolder: string;
  expiryDate: string;
  cvv: string;
  amount: string;
  currency: string;
  targetCurrency: string;
}

interface Currency {
  id: number;
  name: string;
  symbol: string;
  is_active: boolean;
  is_system: boolean;
}

interface Wallet {
  id: number;
  user: number;
  crypto: {
    id: number;
    symbol: string;
    name: string;
  };
  address: string;
  available_balance: string;
}

const CardDepositForm: React.FC = () => {
  const { tokens } = useAuthStore();
  const token = tokens?.access;
  const toast = useToast();
  
  const [currencies, setCurrencies] = useState<Currency[]>([]);
  const [wallets, setWallets] = useState<Wallet[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [cardData, setCardData] = useState<CardData>({
    cardNumber: '',
    cardHolder: '',
    expiryDate: '',
    cvv: '',
    amount: '',
    currency: 'RUB',
    targetCurrency: ''
  });
  const [cardType, setCardType] = useState<string>('');
  const [estimatedAmount, setEstimatedAmount] = useState<number | null>(null);
  const [fee, setFee] = useState<number>(0);
  
  // Загрузка списка криптовалют и кошельков
  useEffect(() => {
    const fetchData = async () => {
      try {
        // Загружаем криптовалюты
        const currenciesResponse = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/crypto/cryptocurrencies/`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        // Фильтруем только системные валюты для пополнения
        const systemCurrencies = currenciesResponse.data.filter(
          (c: Currency) => c.is_system && c.is_active
        );
        
        setCurrencies(systemCurrencies);
        
        // Загружаем кошельки пользователя
        const walletsResponse = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/crypto/wallets/`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        setWallets(walletsResponse.data);
        
        // Устанавливаем значения по умолчанию, если есть доступные валюты
        if (systemCurrencies.length > 0) {
          const defaultCurrency = systemCurrencies.find((c: Currency) => c.symbol === 'USDT') || systemCurrencies[0];
          setCardData(prev => ({
            ...prev,
            targetCurrency: defaultCurrency.symbol
          }));
        }
      } catch (error) {
        console.error('Ошибка при загрузке данных:', error);
        toast({
          title: 'Ошибка',
          description: 'Не удалось загрузить данные',
          status: 'error',
          duration: 5000,
          isClosable: true,
        });
      }
    };
    
    if (token) {
      fetchData();
    }
  }, [token, toast]);
  
  // Обновление расчетов при изменении формы
  useEffect(() => {
    if (cardData.amount && cardData.targetCurrency) {
      calculateEstimatedAmount();
    }
  }, [cardData.amount, cardData.currency, cardData.targetCurrency]);
  
  const calculateEstimatedAmount = () => {
    // Здесь должен быть запрос к API для получения актуального курса
    // Для демонстрации используем упрощенные курсы
    const rates: Record<string, number> = {
      'RUB_USDT': 0.01,
      'RUB_BTC': 0.0000005,
      'RUB_ETH': 0.000008,
      'USD_USDT': 1.0,
      'USD_BTC': 0.00003,
      'USD_ETH': 0.0005,
      'EUR_USDT': 1.1,
      'EUR_BTC': 0.000035,
      'EUR_ETH': 0.00055,
    };
    
    const rateKey = `${cardData.currency}_${cardData.targetCurrency}`;
    const rate = rates[rateKey] || 1;
    
    // Рассчитываем комиссию (2%)
    const feePercentage = 2;
    const amount = parseFloat(cardData.amount);
    const feeAmount = (amount * feePercentage) / 100;
    setFee(feeAmount);
    
    // Рассчитываем сумму к получению
    const estimated = (amount - feeAmount) * rate;
    setEstimatedAmount(estimated);
  };
  
  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    
    if (name === 'cardNumber') {
      // Форматирование номера карты (XXXX XXXX XXXX XXXX)
      const formattedValue = value
        .replace(/\s/g, '')
        .replace(/\D/g, '')
        .replace(/(\d{4})(?=\d)/g, '$1 ')
        .trim()
        .slice(0, 19);
      
      // Определение типа карты
      let type = '';
      if (/^4/.test(formattedValue.replace(/\s/g, ''))) {
        type = 'Visa';
      } else if (/^5[1-5]/.test(formattedValue.replace(/\s/g, ''))) {
        type = 'MasterCard';
      } else if (/^3[47]/.test(formattedValue.replace(/\s/g, ''))) {
        type = 'American Express';
      } else if (/^2/.test(formattedValue.replace(/\s/g, ''))) {
        type = 'Мир';
      }
      
      setCardType(type);
      setCardData(prev => ({ ...prev, [name]: formattedValue }));
      return;
    }
    
    if (name === 'expiryDate') {
      // Форматирование даты истечения (MM/YY)
      const formattedValue = value
        .replace(/\D/g, '')
        .replace(/(\d{2})(?=\d)/g, '$1/')
        .trim()
        .slice(0, 5);
      
      setCardData(prev => ({ ...prev, [name]: formattedValue }));
      return;
    }
    
    if (name === 'cvv') {
      // Ограничение CVV до 3-4 цифр
      const formattedValue = value
        .replace(/\D/g, '')
        .slice(0, 4);
      
      setCardData(prev => ({ ...prev, [name]: formattedValue }));
      return;
    }
    
    setCardData(prev => ({ ...prev, [name]: value }));
  };
  
  const handleAmountChange = (valueAsString: string) => {
    setCardData(prev => ({
      ...prev,
      amount: valueAsString
    }));
  };
  
  const getWalletBalance = (symbol: string): number => {
    const wallet = wallets.find(w => w.crypto.symbol === symbol);
    return wallet ? parseFloat(wallet.available_balance) : 0;
  };
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!cardData.cardNumber || !cardData.cardHolder || !cardData.expiryDate || !cardData.cvv || !cardData.amount || !cardData.targetCurrency) {
      toast({
        title: 'Ошибка',
        description: 'Пожалуйста, заполните все обязательные поля',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
      return;
    }
    
    // Валидация номера карты (упрощенно)
    if (cardData.cardNumber.replace(/\s/g, '').length < 16) {
      toast({
        title: 'Ошибка',
        description: 'Неверный номер карты',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
      return;
    }
    
    // Валидация срока действия карты (упрощенно)
    const [month, year] = cardData.expiryDate.split('/');
    const expiryDate = new Date();
    expiryDate.setFullYear(2000 + parseInt(year), parseInt(month) - 1, 1);
    
    if (expiryDate < new Date()) {
      toast({
        title: 'Ошибка',
        description: 'Срок действия карты истек',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
      return;
    }
    
    setLoading(true);
    
    try {
      // Формируем данные для отправки на сервер
      const depositData = {
        card_number: cardData.cardNumber.replace(/\s/g, ''),
        card_holder: cardData.cardHolder,
        expiry_date: cardData.expiryDate,
        cvv: cardData.cvv,
        amount: parseFloat(cardData.amount),
        currency: cardData.currency,
        target_currency: cardData.targetCurrency
      };
      
      const response = await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL}/crypto/deposit/card/`,
        depositData,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );
      
      toast({
        title: 'Успешно!',
        description: `Ваш кошелек пополнен на ${response.data.received_amount} ${response.data.target_currency}`,
        status: 'success',
        duration: 5000,
        isClosable: true,
      });
      
      // Сбрасываем форму
      setCardData({
        ...cardData,
        cardNumber: '',
        cardHolder: '',
        expiryDate: '',
        cvv: '',
        amount: ''
      });
      
      setEstimatedAmount(null);
      setFee(0);
      
      // Обновляем список кошельков
      const walletsResponse = await axios.get(`${process.env.NEXT_PUBLIC_API_URL}/crypto/wallets/`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setWallets(walletsResponse.data);
      
    } catch (error) {
      console.error('Ошибка при пополнении:', error);
      toast({
        title: 'Ошибка',
        description: error.response?.data?.error || 'Произошла ошибка при пополнении кошелька',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <Box p={5} shadow="md" borderWidth="1px" borderRadius="md" bg="white">
      <Heading size="md" mb={4}>Пополнение с банковской карты</Heading>
      
      <form onSubmit={handleSubmit}>
        <VStack spacing={4} align="flex-start">
          <FormControl isRequired>
            <FormLabel>Номер карты</FormLabel>
            <InputGroup>
              <Input
                name="cardNumber"
                value={cardData.cardNumber}
                onChange={handleChange}
                placeholder="XXXX XXXX XXXX XXXX"
                maxLength={19}
              />
              {cardType && (
                <InputRightElement width="4.5rem">
                  <Text fontSize="sm" fontWeight="bold">{cardType}</Text>
                </InputRightElement>
              )}
            </InputGroup>
          </FormControl>
          
          <FormControl isRequired>
            <FormLabel>Имя владельца</FormLabel>
            <Input
              name="cardHolder"
              value={cardData.cardHolder}
              onChange={handleChange}
              placeholder="IVAN IVANOV"
              textTransform="uppercase"
            />
          </FormControl>
          
          <HStack w="100%" spacing={6}>
            <FormControl isRequired>
              <FormLabel>Срок действия</FormLabel>
              <Input
                name="expiryDate"
                value={cardData.expiryDate}
                onChange={handleChange}
                placeholder="MM/YY"
                maxLength={5}
              />
            </FormControl>
            
            <FormControl isRequired>
              <FormLabel>CVV</FormLabel>
              <Input
                name="cvv"
                value={cardData.cvv}
                onChange={handleChange}
                placeholder="123"
                maxLength={4}
                type="password"
              />
            </FormControl>
          </HStack>
          
          <Divider />
          
          <FormControl isRequired>
            <FormLabel>Сумма пополнения</FormLabel>
            <HStack w="100%" spacing={4}>
              <NumberInput
                min={100}
                value={cardData.amount}
                onChange={handleAmountChange}
                flex="2"
              >
                <NumberInputField placeholder="Введите сумму" />
                <NumberInputStepper>
                  <NumberIncrementStepper />
                  <NumberDecrementStepper />
                </NumberInputStepper>
              </NumberInput>
              
              <Select 
                name="currency" 
                value={cardData.currency} 
                onChange={handleChange}
                flex="1"
              >
                <option value="RUB">RUB</option>
                <option value="USD">USD</option>
                <option value="EUR">EUR</option>
              </Select>
            </HStack>
            <Text fontSize="xs" mt={1} color="gray.500">
              Минимальная сумма пополнения: 100 RUB / 1 USD / 1 EUR
            </Text>
          </FormControl>
          
          <FormControl isRequired>
            <FormLabel>
              Получить в валюте 
              <Tooltip 
                label="Выберите криптовалюту, в которой хотите получить средства на свой кошелек"
                placement="top"
              >
                <InfoIcon ml={1} mb={1} boxSize={3} />
              </Tooltip>
            </FormLabel>
            <Select 
              name="targetCurrency" 
              value={cardData.targetCurrency} 
              onChange={handleChange}
              placeholder="Выберите валюту"
            >
              {currencies.map((currency) => (
                <option key={currency.id} value={currency.symbol}>
                  {currency.name} ({currency.symbol})
                </option>
              ))}
            </Select>
            {cardData.targetCurrency && (
              <Text fontSize="sm" mt={1}>
                Текущий баланс: {getWalletBalance(cardData.targetCurrency)} {cardData.targetCurrency}
              </Text>
            )}
          </FormControl>
          
          {estimatedAmount !== null && (
            <Box w="100%" p={3} bg="gray.50" borderRadius="md">
              <VStack align="flex-start" spacing={2}>
                <HStack justify="space-between" w="100%">
                  <Text fontSize="sm">Комиссия (2%):</Text>
                  <Text fontSize="sm" fontWeight="bold">{fee.toFixed(2)} {cardData.currency}</Text>
                </HStack>
                <HStack justify="space-between" w="100%">
                  <Text fontSize="sm">Курс обмена:</Text>
                  <Text fontSize="sm" fontWeight="bold">1 {cardData.currency} = {(estimatedAmount / (parseFloat(cardData.amount) - fee)).toFixed(8)} {cardData.targetCurrency}</Text>
                </HStack>
                <Divider />
                <HStack justify="space-between" w="100%">
                  <Text>Вы получите:</Text>
                  <Text fontWeight="bold">{estimatedAmount.toFixed(8)} {cardData.targetCurrency}</Text>
                </HStack>
              </VStack>
            </Box>
          )}
          
          <Alert status="info" borderRadius="md">
            <AlertIcon />
            <Text fontSize="sm">
              Пополнение происходит мгновенно. Комиссия за пополнение составляет 2%.
            </Text>
          </Alert>
          
          <Button 
            type="submit" 
            colorScheme="blue" 
            isLoading={loading}
            w="100%"
            mt={2}
          >
            Пополнить кошелек
          </Button>
        </VStack>
      </form>
    </Box>
  );
};

export default CardDepositForm;
