package com.example.user;

import java.util.Optional;

public class JdbcUserRepository implements UserRepository {
    @Override
    public Optional<User> findById(Long id) {
        if (id == null) {
            return Optional.empty();
        }
        return Optional.of(new User(id, "user-" + id));
    }
}
