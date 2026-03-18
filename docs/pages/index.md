# Introduction

<div align="center">
<img alt="Logo" src="https://raw.githubusercontent.com/AndreuCodina/wirio/refs/heads/main/docs/logo.png" width="450" height="450">
</div>

## What is Dependency Injection

**Dependency Injection (DI)** is a design pattern where a class receives the objects it depends on from the outside, instead of creating them itself. This separates _object construction_ from _object usage_, making code easier to test and change.

### Benefits of Dependency Injection

- **Loose coupling**

  Easily extend or change the functionality of a system by combining the components in a different way.

- **Improved testability**

  Dependencies can be replaced with mocks, stubs, or simple test doubles, enabling fast and isolated unit tests.

- **Better maintainability**

  Object creation, settings, and business logic are clearly separated, making the codebase easier to understand and evolve.

- **Controlled variability**

  Different behaviors can be provided at runtime (for example, real vs. fake dependencies) without modifying the consuming code.

- **Centralized wiring**

  Object creation and dependency wiring live in one place (the composition root), keeping domain and application logic clean.

In short, DI does not magically decouple behavior, but it **decouples construction**, which already brings significant practical benefits in Python.

## Features of Wirio

- **Use it everywhere:** Use dependency injection in web servers, background tasks, console applications, Jupyter notebooks, tests, etc.
- **Lifetimes**: `Singleton` (same instance per application), `Scoped` (same instance per HTTP request scope) and `Transient` (different instance per resolution).
- **FastAPI integration** out of the box, and pluggable to any web framework.
- **Automatic resolution and disposal**: Automatically resolve constructor parameters and manage async and non-async context managers. It's no longer our concern to know how to create or dispose services.
- **Clear design** inspired by one of the most used and battle-tested DI libraries, adding async-native support, important features and good defaults.
- **Centralized configuration**: Register all services in one place using a clean syntax, and without decorators.
- **ty** and **Pyright** strict compliant.
