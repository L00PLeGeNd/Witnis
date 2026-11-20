package com.example.auth;

public class TokenGateway {
    public String issue(String user) {
        return "tok-" + user;
    }

    public boolean verify(String token) {
        return token != null && token.startsWith("tok-");
    }
}
