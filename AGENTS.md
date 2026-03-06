# AGENTS.md

# Environment

- Package manager: `uv`.
- Check code is correct: `make check-code`.

# General guidance

- Use American English.
- Use type hints everywhere.
- Use standard decorators, such as `override`, when appropriate.

# Testing

- Run tests using `uv`.
- Test files must be placed in the `tests` directory, mirroring the structure of the `src` directory.
- Test names must start with `test_`, be followed by a verb in present tense, and read as `The test should...`. The names mustn't include the word "should", and they must be descriptive and concise, avoiding the inclusion of the tested function whenever possible. Examples: `test_create_user`, `test_fail_when_creating_user_with_untrusted_email`, `test_ban_user_using_administrator_account`.
- Append new test cases to the end of the existing ones.
- When mocks are needed, use `MockerFixture`.
- `MockerFixture` should use the `create_autospec` method to create mocks, and the `instance=True` parameter should be passed to ensure the mock behaves like an instance of the class being mocked. `mocker.Mock()` should be avoided, as it creates a generic mock that doesn't enforce the interface of the mocked class.

# Documentation

- The documentation must be placed in the `docs` directory or the `README` file.
- Use "we" to refer to the reader and the author together.
