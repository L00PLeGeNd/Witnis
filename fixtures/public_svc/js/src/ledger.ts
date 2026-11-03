export class Ledger {
  private total = 0;

  record(amountCents: number): void {
    if (amountCents > 0) this.total += amountCents;
  }

  balance(): number {
    return this.total;
  }
}
