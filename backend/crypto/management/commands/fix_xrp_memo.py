from django.core.management.base import BaseCommand
from crypto.models import Cryptocurrency

class Command(BaseCommand):
    help = 'Обновляет поле requires_memo для XRP'

    def handle(self, *args, **options):
        try:
            # Находим XRP
            xrp = Cryptocurrency.objects.get(symbol='XRP', network='XRP')
            
            if xrp.requires_memo:
                self.stdout.write(self.style.SUCCESS(
                    f'✅ XRP уже имеет requires_memo=True (ID: {xrp.id})'
                ))
            else:
                xrp.requires_memo = True
                xrp.save()
                self.stdout.write(self.style.SUCCESS(
                    f'✅ Обновлено поле requires_memo=True для XRP (ID: {xrp.id})'
                ))
            
            # Также обновляем BNB если нужно
            try:
                bnb = Cryptocurrency.objects.get(symbol='BNB', network='BEP20')
                if not bnb.requires_memo:
                    bnb.requires_memo = True
                    bnb.save()
                    self.stdout.write(self.style.SUCCESS(
                        f'✅ Обновлено поле requires_memo=True для BNB (ID: {bnb.id})'
                    ))
                else:
                    self.stdout.write(self.style.SUCCESS(
                        f'✅ BNB уже имеет requires_memo=True (ID: {bnb.id})'
                    ))
            except Cryptocurrency.DoesNotExist:
                self.stdout.write(self.style.WARNING('BNB не найден, пропускаем'))
                
        except Cryptocurrency.DoesNotExist:
            self.stdout.write(self.style.ERROR('❌ XRP не найден в базе данных!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Ошибка: {e}'))

