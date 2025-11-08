import pytest
from model_bakery import baker

from crypto.tasks import process_withdrawal, check_blockchain_deposits
from transactions.models import Transfer


@pytest.mark.django_db
def test_process_withdrawal_success():
    """process_withdrawal должна перевести перевод из PENDING в SUCCESS."""
    transfer: Transfer = baker.make(
        Transfer,
        status=Transfer.Status.PENDING,  # type: ignore[attr-defined]
        type="out",  # исходящий перевод
    )

    tx_hash = process_withdrawal(transfer.id)

    transfer.refresh_from_db()
    assert tx_hash == transfer.tx_hash
    assert transfer.status == Transfer.Status.SUCCESS  # type: ignore[attr-defined]
    assert transfer.fee is not None
    assert transfer.completed_at is not None


@pytest.mark.django_db
def test_check_blockchain_deposits_returns_str(caplog):
    """Заглушка check_blockchain_deposits возвращает строку и пишет лог."""
    caplog.set_level("INFO")
    result = check_blockchain_deposits()
    assert isinstance(result, str)
    assert "check_blockchain_deposits" in " ".join(caplog.messages)
