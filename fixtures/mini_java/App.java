package com.example;

import com.example.auth.AuthService;

public class App {
    public static void main(String[] args) {
        AuthService svc = new AuthService();
        System.out.println(svc.login("alice", "secret"));
    }
}
