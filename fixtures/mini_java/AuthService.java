package com.example.auth;

public class AuthService {
    public boolean login(String username, String password) {
        return username != null && password != null && !username.isEmpty();
    }
}
