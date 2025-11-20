"""
Команда для проверки статуса транзакции консолидации
"""
from django.core.management.base import BaseCommand
from transactions.models import Transaction
from crypto.blockchain.factory import get_blockchain_service


class Command(BaseCommand):
    help = 'Проверяет статус транзакции консолидации в блокчейне'

    def add_arguments(self, parser):
        parser.add_argument('--tx-hash', type=str, help='Хеш транзакции (опционально)')

    def handle(self, *args, **options):
        tx_hash = options.get('tx_hash')
        
        if not tx_hash:
            # Находим последнюю транзакцию консолидации
            consolidation = Transaction.objects.filter(
                type='consolidation',
                status='pending'
            ).order_by('-timestamp').first()
            
            if not consolidation:
                self.stdout.write(self.style.WARNING("Нет pending транзакций консолидации"))
                return
            
            tx_hash = consolidation.tx_hash
            self.stdout.write(f"Найдена транзакция консолидации: {tx_hash}")
        
        # Проверяем статус в блокчейне
        try:
            consolidation = Transaction.objects.get(tx_hash=tx_hash, type='consolidation')
            service = get_blockchain_service(consolidation.crypto.network or consolidation.crypto.symbol)
            
            self.stdout.write(f"\n=== Проверка транзакции в блокчейне ===")
            self.stdout.write(f"TX Hash: {tx_hash}")
            self.stdout.write(f"Currency: {consolidation.crypto.symbol}")
            self.stdout.write(f"Status in DB: {consolidation.status}")
            
            is_confirmed = service.is_transaction_confirmed(tx_hash)
            
            if is_confirmed:
                self.stdout.write(self.style.SUCCESS(f"\n✅ Транзакция ПОДТВЕРЖДЕНА в блокчейне!"))
                self.stdout.write(self.style.WARNING("Но статус в БД еще 'pending'. Возможно, проверка подтверждений еще не сработала."))
                self.stdout.write("Подождите 1-2 минуты, система автоматически обновит статус.")
            else:
                self.stdout.write(self.style.WARNING(f"\n⏳ Транзакция еще НЕ подтверждена в блокчейне"))
                self.stdout.write("Это нормально для Bitcoin testnet - подтверждение может занять 10-60 минут.")
                self.stdout.write("Система проверяет подтверждение каждую минуту автоматически.")
            
            # Дополнительная информация
            self.stdout.write(f"\n=== Дополнительная информация ===")
            self.stdout.write(f"User: {consolidation.user.email}")
            self.stdout.write(f"Amount: {consolidation.amount} {consolidation.crypto.symbol}")
            self.stdout.write(f"Created: {consolidation.timestamp}")
            
        except Transaction.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Транзакция {tx_hash} не найдена в базе данных"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ошибка при проверке: {e}"))

