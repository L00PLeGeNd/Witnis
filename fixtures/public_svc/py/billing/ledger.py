"""Simple ledger for public_svc."""

from .models import Invoice


class Ledger:
    def __init__(self) -> None:
        self._rows: list[Invoice] = []

    def record(self, invoice: Invoice) -> None:
        if invoice.is_payable():
            self._rows.append(invoice)

    def total_cents(self) -> int:
        return sum(i.amount_cents for i in self._rows)
