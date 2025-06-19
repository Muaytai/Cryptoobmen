"""Абстрактный интерфейс провайдера блокчейна.

Каждый драйвер (TronProvider, BitcoinProvider, EvmProvider и т.д.)
должен реализовать следующие методы. Это позволит легко переключать
сетевые реализации, а бизнес-логика проекта останется неизменной.
"""
from __future__ import annotations

import abc
from typing import Callable, Protocol, Any, Dict


class DepositCallback(Protocol):
    """Сигнатура функции-колбэка для поступивших депозитов."""

    def __call__(self, tx_hash: str, address: str, amount: int, raw_tx: Dict[str, Any]) -> None:  # noqa: D401,E501
        ...


class BlockchainProvider(abc.ABC):
    network: str  # читаемое имя сети/блокчейна (например, 'Tron Nile')

    @abc.abstractmethod
    def generate_address(self, user_id: int | str) -> dict[str, str]:
        """Возвращает словарь с публичным address и приватным ключом (hex/bytes).

        Привязка к user_id нужна, если требуется детерминированная генерация или
        сохранение в БД.
        """

    @abc.abstractmethod
    def get_balance(self, address: str, contract_address: str | None = None) -> int:
        """Возвращает баланс адреса в *base units* (sun, wei, satoshi).

        `contract_address` указываем, если нужно проверить токен (ERC-20, TRC-20).
        """

    @abc.abstractmethod
    def send_tx(
        self,
        priv_key_hex: str,
        to_address: str,
        amount: int,
        contract_address: str | None = None,
    ) -> str:
        """Подписывает и отправляет перевод, возвращает tx_hash."""

    def listen_deposits(
        self,
        system_address: str,
        callback: DepositCallback,
        start_block: int | None = None,
    ) -> None:
        """Опрашивает/стримит блоки и вызывает callback при входящем депозите.

        Базовая реализация может быть пустой. Драйверы могут перекрывать.
        """
        raise NotImplementedError
