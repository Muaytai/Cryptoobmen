from abc import ABC, abstractmethod
from decimal import Decimal
from typing import List, Dict, Any

class BaseBlockchainService(ABC):
    """
    Абстрактный базовый класс для взаимодействия с различными блокчейнами.
    Определяет общий интерфейс, который должен быть реализован для каждой сети.
    """

    def __init__(self, network: str):
        self.network = network

    @abstractmethod
    def get_transactions(self, address: str, min_timestamp: int = 0) -> List[Dict[str, Any]]:
        """
        Получает список входящих транзакций для указанного адреса.

        :param address: Адрес кошелька для проверки.
        :param min_timestamp: Минимальная временная метка для поиска транзакций (в миллисекундах).
        :return: Список словарей, где каждый словарь представляет транзакцию.
                 Пример: [{'transaction_id': '...', 'from_address': '...', 'to_address': '...', 'value': '1000000', 'memo': '...'}]
        """
        pass

    @abstractmethod
    def send_transaction(self, private_key: str, to_address: str, amount: Decimal, memo: str = "") -> str:
        """
        Отправляет транзакцию в блокчейн.

        :param private_key: Приватный ключ от кошелька отправителя.
        :param to_address: Адрес получателя.
        :param amount: Сумма для отправки (в основной единице, например, USDT, а не в сатоши/sun).
        :param memo: Опциональное примечание к транзакции.
        :return: Хэш (ID) созданной транзакции.
        """
        pass

    @abstractmethod
    def get_balance(self, address: str) -> Decimal:
        """
        Получает баланс указанного адреса.

        :param address: Адрес кошелька.
        :return: Баланс в виде объекта Decimal.
        """
        pass

    @abstractmethod
    def create_new_address(self, **kwargs) -> str:
        """
        Создает новый адрес для пополнения.
        Может использовать user_id или другие параметры для HD-генерации.

        :return: Строка с новым адресом.
        """
        pass

    @staticmethod
    def to_atomic_unit(amount: Decimal, decimals: int) -> int:
        """
        Конвертирует сумму из основной единицы в атомарную (например, USDT в sun).
        """
        return int(amount * (10 ** decimals))

    @staticmethod
    def from_atomic_unit(amount: int, decimals: int) -> Decimal:
        """
        Конвертирует сумму из атомарной единицы в основную.
        """
        return Decimal(amount) / (10 ** decimals)
