import { requireToken } from "./auth";

export class BillingClient {
  charge(amountCents: number, token: string): boolean {
    if (!requireToken(token)) return false;
    return amountCents > 0 && amountCents < 1_000_000;
  }
}
