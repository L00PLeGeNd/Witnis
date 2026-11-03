# semantic_java_di

Synthetic Spring-**style** DI slice (original Apache-2.0 sample for Witnis).

## Intent

Human-expected engineering relations:

1. `UserController.get` **calls** `UserService.findUser`
2. `UserService` **depends on** `UserRepository` via `@Autowired` field injection
3. `UserRepository` is an **interface**; `JdbcUserRepository` is the **implementation**

## Current Witnis expectation

Shallow Java indexing may see classes/methods/imports and simple call names.

It is **not** expected (yet) to reliably emit:

- injection edges for `@Autowired`
- interface → implementation binding
- AOP / proxy / generic erasure accuracy

Use this fixture with ground-truth labels to track progress — not to claim Spring support today.
