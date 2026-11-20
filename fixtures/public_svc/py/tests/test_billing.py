from py.billing.models import Invoice
from py.billing.service import BillingService


def test_charge_ok():
    svc = BillingService()
    inv = Invoice(id="1", amount_cents=100)
    assert svc.charge(inv, "tok-a") is True
