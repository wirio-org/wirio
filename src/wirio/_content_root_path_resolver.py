import inspect
from pathlib import Path
from typing import Final, final

from wirio._utils._python_runtime_path import PythonRuntimePath


@final
class ContentRootPathResolver:
    _package_root: Final[Path]

    def __init__(self, package_root: Path) -> None:
        self._package_root = package_root

    def resolve_path(self) -> str:  # noqa: C901, PLR0911
        current_frame = inspect.currentframe()

        if current_frame is None:
            return str(Path.cwd().expanduser().resolve())

        try:
            current_working_directory = Path.cwd().expanduser().resolve()
            resolved_package_frame_path: Path | None = None
            found_only_runtime_external_frames = False
            stack_frame = current_frame.f_back

            while stack_frame is not None:
                notebook_path = stack_frame.f_globals.get("__vsc_ipynb_file__")

                if isinstance(notebook_path, str):
                    resolved_notebook_path = Path(notebook_path).expanduser().resolve()

                    if resolved_notebook_path.exists():
                        if (
                            resolved_package_frame_path is not None
                            and resolved_package_frame_path.parent != self._package_root
                        ):
                            return str(resolved_package_frame_path.parent)

                        return str(resolved_notebook_path.parent)

                current_frame_filename = stack_frame.f_code.co_filename
                current_frame_path = Path(current_frame_filename)

                if not current_frame_path.exists():
                    stack_frame = stack_frame.f_back
                    continue

                resolved_current_frame_path = current_frame_path.resolve()

                if self._package_root not in resolved_current_frame_path.parents:
                    if PythonRuntimePath.is_python_runtime_path(
                        resolved_current_frame_path
                    ):
                        found_only_runtime_external_frames = True
                        stack_frame = stack_frame.f_back
                        continue

                    if (
                        resolved_package_frame_path is not None
                        and resolved_package_frame_path.parent != self._package_root
                    ):
                        return str(resolved_package_frame_path.parent)

                    return str(resolved_current_frame_path.parent)

                resolved_package_frame_path = resolved_current_frame_path
                stack_frame = stack_frame.f_back

            if resolved_package_frame_path is None:
                return str(current_working_directory)

            if found_only_runtime_external_frames:
                return str(current_working_directory)

            return str(resolved_package_frame_path.parent)
        finally:
            del current_frame
