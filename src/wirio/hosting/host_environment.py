import inspect
import os
from pathlib import Path
from typing import Final, final

from wirio._utils._python_runtime_path import PythonRuntimePath
from wirio.hosting._environment_variable import EnvironmentVariable
from wirio.hosting.environment import Environment


@final
class HostEnvironment:
    """Provide information about the hosting environment an application is running in."""

    _environment_name: Final[str]
    _content_root_path: Final[str]

    def __init__(self, content_root_path: str | None = None) -> None:
        """Initialize the host environment.

        Args:
            content_root_path: Absolute path to the directory that contains the application content files.
                If not provided, the content root path will be inferred from the caller file path.

        """
        self._environment_name = self.get_current_environment_name()
        self._content_root_path = (
            content_root_path
            if content_root_path is not None
            else self._get_caller_directory_path()
        )

    @staticmethod
    def get_current_environment_name() -> str:
        return os.getenv(
            EnvironmentVariable.WIRIO_ENVIRONMENT.value, Environment.LOCAL.value
        )

    @property
    def environment_name(self) -> str:
        """Environment name."""
        return self._environment_name

    @property
    def content_root_path(self) -> str:
        """Absolute path to the directory that contains the application content files."""
        return self._content_root_path

    def is_environment(self, environment_name: str) -> bool:
        """Compare the current host environment name against the specified value."""
        return self._environment_name == environment_name

    def is_local(self) -> bool:
        """Check if the current host environment name is `local`."""
        return self.is_environment(Environment.LOCAL.value)

    def is_development(self) -> bool:
        """Check if the current host environment name is `development`."""
        return self.is_environment(Environment.DEVELOPMENT.value)

    def is_staging(self) -> bool:
        """Check if the current host environment name is `staging`."""
        return self.is_environment(Environment.STAGING.value)

    def is_production(self) -> bool:
        """Check if the current host environment name is `production`."""
        return self.is_environment(Environment.PRODUCTION.value)

    def _get_caller_directory_path(self) -> str:
        current_frame = inspect.currentframe()

        if current_frame is None:
            return str(Path.cwd().resolve())

        package_root = Path(__file__).resolve().parent
        current_working_directory = Path.cwd().expanduser().resolve()

        try:
            stack_frame = current_frame.f_back

            while stack_frame is not None:
                notebook_path = stack_frame.f_globals.get("__vsc_ipynb_file__")

                if isinstance(notebook_path, str):
                    resolved_notebook_path = Path(notebook_path).expanduser().resolve()

                    if resolved_notebook_path.exists():
                        return str(resolved_notebook_path.parent)

                current_frame_path = Path(stack_frame.f_code.co_filename)

                if current_frame_path.exists():
                    resolved_current_frame_path = current_frame_path.resolve()

                    if package_root not in resolved_current_frame_path.parents:
                        if PythonRuntimePath.is_python_runtime_path(
                            resolved_current_frame_path
                        ):
                            stack_frame = stack_frame.f_back
                            continue

                        return str(resolved_current_frame_path.parent)

                stack_frame = stack_frame.f_back

            return str(current_working_directory)
        finally:
            del current_frame
