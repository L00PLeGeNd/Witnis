"""Billing domain models."""

from dataclasses import dataclass


@dataclass
class Invoice:
    id: str
    amount_cents: int
    currency: str = "USD"

    def is_payable(self) -> bool:
        return self.amount_cents > 0
