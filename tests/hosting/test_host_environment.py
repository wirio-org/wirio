import inspect
import os
from pathlib import Path
from types import CodeType, FrameType

from pytest_mock import MockerFixture

from wirio._utils._python_runtime_path import PythonRuntimePath
from wirio.hosting._environment_variable import EnvironmentVariable
from wirio.hosting.environment import Environment
from wirio.hosting.host_environment import HostEnvironment


class TestHostEnvironment:
    def test_return_default_environment_name_when_environment_variable_is_not_set(
        self, mocker: MockerFixture
    ) -> None:
        expected_default_environment_name = Environment.LOCAL.value
        mocker.patch.dict(os.environ, {}, clear=True)

        environment = HostEnvironment(content_root_path="")

        assert environment.environment_name == expected_default_environment_name

    def test_return_updated_environment_name_when_environment_variable_is_set(
        self, mocker: MockerFixture
    ) -> None:
        expected_environment_name = "current_environment"
        mocker.patch.dict(
            os.environ,
            {EnvironmentVariable.WIRIO_ENVIRONMENT.value: expected_environment_name},
        )

        environment = HostEnvironment(content_root_path="")

        assert environment.environment_name == expected_environment_name

    def test_check_environment_equality(self, mocker: MockerFixture) -> None:
        expected_environment_name = "current_environment"
        not_expected_environment_name = "not_current_environment"
        mocker.patch.dict(
            os.environ,
            {EnvironmentVariable.WIRIO_ENVIRONMENT.value: expected_environment_name},
        )

        environment = HostEnvironment(content_root_path="")

        assert environment.is_environment(expected_environment_name)
        assert not environment.is_environment(not_expected_environment_name)

    def test_return_if_the_current_environment_is_the_requested_one(
        self, mocker: MockerFixture
    ) -> None:
        mocker.patch.dict(
            os.environ,
            {EnvironmentVariable.WIRIO_ENVIRONMENT.value: Environment.LOCAL.value},
        )
        environment = HostEnvironment(content_root_path="")
        assert environment.is_local()

        mocker.patch.dict(
            os.environ,
            {
                EnvironmentVariable.WIRIO_ENVIRONMENT.value: Environment.DEVELOPMENT.value
            },
        )
        environment = HostEnvironment(content_root_path="")
        assert environment.is_development()

        mocker.patch.dict(
            os.environ,
            {EnvironmentVariable.WIRIO_ENVIRONMENT.value: Environment.STAGING.value},
        )
        environment = HostEnvironment(content_root_path="")
        assert environment.is_staging()

        mocker.patch.dict(
            os.environ,
            {EnvironmentVariable.WIRIO_ENVIRONMENT.value: Environment.PRODUCTION.value},
        )
        environment = HostEnvironment(content_root_path="")
        assert environment.is_production()

    def test_return_caller_directory_as_content_root_path_when_no_content_root_path_is_provided(
        self,
    ) -> None:
        expected_content_root_path = str(Path(__file__).parent.resolve())

        environment = HostEnvironment()

        assert environment.content_root_path == expected_content_root_path

    def test_return_notebook_directory_as_content_root_path_when_running_in_notebook(
        self, mocker: MockerFixture, tmp_path: Path
    ) -> None:
        notebook_path = tmp_path / "notebook.ipynb"
        notebook_path.write_text("{}")

        code_mock = mocker.create_autospec(CodeType, instance=True)
        code_mock.co_filename = ""

        notebook_frame = mocker.create_autospec(FrameType, instance=True)
        notebook_frame.f_back = None
        notebook_frame.f_globals = {"__vsc_ipynb_file__": str(notebook_path)}
        notebook_frame.f_code = code_mock

        current_frame = mocker.create_autospec(FrameType, instance=True)
        current_frame.f_back = notebook_frame
        current_frame.f_globals = {}
        current_frame.f_code = code_mock

        mocker.patch(
            f"{HostEnvironment.__module__}.{inspect.__name__}.{inspect.currentframe.__name__}",
            autospec=True,
            return_value=current_frame,
        )

        environment = HostEnvironment()

        assert environment.content_root_path == str(tmp_path.resolve())

    def test_skip_runtime_path_and_advance_to_next_stack_frame(
        self, mocker: MockerFixture, tmp_path: Path
    ) -> None:
        runtime_file_path = tmp_path / "runtime_like.py"
        runtime_file_path.write_text("# runtime")

        caller_file_path = tmp_path / "caller.py"
        caller_file_path.write_text("# caller")

        current_code_mock = mocker.create_autospec(CodeType, instance=True)
        current_code_mock.co_filename = ""

        runtime_code_mock = mocker.create_autospec(CodeType, instance=True)
        runtime_code_mock.co_filename = str(runtime_file_path)

        caller_code_mock = mocker.create_autospec(CodeType, instance=True)
        caller_code_mock.co_filename = str(caller_file_path)

        caller_frame = mocker.create_autospec(FrameType, instance=True)
        caller_frame.f_back = None
        caller_frame.f_globals = {}
        caller_frame.f_code = caller_code_mock

        runtime_frame = mocker.create_autospec(FrameType, instance=True)
        runtime_frame.f_back = caller_frame
        runtime_frame.f_globals = {}
        runtime_frame.f_code = runtime_code_mock

        current_frame = mocker.create_autospec(FrameType, instance=True)
        current_frame.f_back = runtime_frame
        current_frame.f_globals = {}
        current_frame.f_code = current_code_mock

        mocker.patch(
            f"{HostEnvironment.__module__}.{inspect.__name__}.{inspect.currentframe.__name__}",
            autospec=True,
            return_value=current_frame,
        )

        resolved_runtime_file_path = runtime_file_path.resolve()
        mocker.patch.object(
            PythonRuntimePath,
            PythonRuntimePath.is_python_runtime_path.__name__,
            autospec=True,
            side_effect=lambda resolved_path: (  # pyright: ignore[reportUnknownLambdaType]
                resolved_path == resolved_runtime_file_path
            ),
        )

        environment = HostEnvironment()

        assert environment.content_root_path == str(tmp_path.resolve())

    def test_return_current_working_directory_when_no_stack_frame_matches(
        self, mocker: MockerFixture
    ) -> None:
        expected_current_working_directory = str(Path.cwd().resolve())

        current_code_mock = mocker.create_autospec(CodeType, instance=True)
        current_code_mock.co_filename = ""

        current_frame = mocker.create_autospec(FrameType, instance=True)
        current_frame.f_back = None
        current_frame.f_globals = {}
        current_frame.f_code = current_code_mock

        mocker.patch(
            f"{HostEnvironment.__module__}.{inspect.__name__}.{inspect.currentframe.__name__}",
            autospec=True,
            return_value=current_frame,
        )

        environment = HostEnvironment()

        assert environment.content_root_path == expected_current_working_directory

    def test_return_current_working_directory_when_current_frame_is_none(
        self, mocker: MockerFixture
    ) -> None:
        expected_current_working_directory = str(Path.cwd().resolve())

        mocker.patch(
            f"{HostEnvironment.__module__}.{inspect.__name__}.{inspect.currentframe.__name__}",
            autospec=True,
            return_value=None,
        )

        environment = HostEnvironment()

        assert environment.content_root_path == expected_current_working_directory
