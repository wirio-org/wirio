from typing import ClassVar


class ConfigurationPath:
    """Provide utility methods and constants for manipulating configuration paths."""

    KEY_DELIMITER: ClassVar[str] = ":"

    @staticmethod
    def get_section_key(path: str) -> str:
        """Extract the last path segment from the path.

        Args:
            path: The path.

        Returns:
            The last path segment of the path.

        """
        last_key_delimiter_index = path.rfind(ConfigurationPath.KEY_DELIMITER)

        if last_key_delimiter_index < 0:
            return path

        return path[last_key_delimiter_index + 1 :]
