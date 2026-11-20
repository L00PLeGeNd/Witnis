"""Billing service."""

from .models import Invoice


def audit(fn):  # type: ignore[no-untyped-def]
    return fn


class BillingService:
    """Charges invoices after auth."""

    @audit
    def charge(self, invoice: Invoice, token: str) -> bool:
        if not invoice.is_payable():
            return False
        return bool(token) and invoice.amount_cents < 1_000_000


class PromoBilling(BillingService):
    def charge(self, invoice: Invoice, token: str) -> bool:
        if invoice.currency != "USD":
            return False
        return super().charge(invoice, token)
