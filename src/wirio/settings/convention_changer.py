import re


class ConventionChanger:
    @staticmethod
    def to_snake_case(string_to_convert: str) -> str:
        """Convert a PascalCase, camelCase, or kebab-case string to snake_case."""
        # Handle the sequence of uppercase letters followed by a lowercase letter
        converted_string = re.sub(
            r"([A-Z]+)([A-Z][a-z])",
            lambda match: f"{match.group(1)}_{match.group(2)}",
            string_to_convert,
        )

        # Insert an underscore between a lowercase letter and an uppercase letter
        converted_string = re.sub(
            r"([a-z])([A-Z])",
            lambda match: f"{match.group(1)}_{match.group(2)}",
            converted_string,
        )

        # Insert an underscore between a digit and an uppercase letter
        converted_string = re.sub(
            r"([0-9])([A-Z])",
            lambda match: f"{match.group(1)}_{match.group(2)}",
            converted_string,
        )

        # Insert an underscore between a lowercase letter and a digit
        converted_string = re.sub(
            r"([a-z])([0-9])",
            lambda match: f"{match.group(1)}_{match.group(2)}",
            converted_string,
        )

        # Replace hyphens with underscores to handle kebab-case
        converted_string = converted_string.replace("-", "_")

        return converted_string.lower()
