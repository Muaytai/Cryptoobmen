from django.core.management.base import BaseCommand
from crypto.models import Cryptocurrency

class Command(BaseCommand):
    help = 'Sets the correct contract address and decimals for USDT (TRC20) on Nile Testnet'

    def handle(self, *args, **options):
        usdt_symbol = 'USDT'
        # АДРЕС С ОФИЦИАЛЬНОГО FAUCET'А NILE (nileex.io)
        contract_address = 'TXYZopYRdj2D9XRtbG411XZZ3kM5VkAeBf'
        decimals = 6

        try:
            usdt_currency = Cryptocurrency.objects.get(symbol=usdt_symbol)
            
            usdt_currency.contract_address = contract_address
            usdt_currency.decimals = decimals
            usdt_currency.save()
            
            self.stdout.write(self.style.SUCCESS(
                f"Successfully updated {usdt_symbol}: "
                f"Contract Address set to {contract_address}, "
                f"Decimals set to {decimals}."
            ))
            
        except Cryptocurrency.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                f"Cryptocurrency with symbol '{usdt_symbol}' does not exist. "
                "Please create it in the admin panel first."
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {e}")) 