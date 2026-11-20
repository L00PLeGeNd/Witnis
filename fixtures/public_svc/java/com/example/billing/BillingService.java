package com.example.billing;

import com.example.auth.TokenGateway;

public class BillingService {
    private final TokenGateway gateway = new TokenGateway();

    public boolean charge(int amountCents, String token) {
        if (!gateway.verify(token)) {
            return false;
        }
        return amountCents > 0 && amountCents < 1_000_000;
    }
}
