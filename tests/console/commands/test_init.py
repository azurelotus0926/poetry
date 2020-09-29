import sys

import pytest

from poetry.utils._compat import Path
from poetry.utils._compat import decode
from tests.helpers import get_package


@pytest.fixture
def source_dir(tmp_path):  # type: (Path) -> Path
    yield Path(tmp_path.as_posix())


@pytest.fixture(autouse=True)
def patches(mocker, source_dir):
    patch = mocker.patch("poetry.utils._compat.Path.cwd")
    patch.return_value = source_dir


@pytest.fixture
def tester(command_tester_factory):
    return command_tester_factory("init")


@pytest.fixture
def init_basic_inputs():
    return "\n".join(
        [
            "my-package",  # Package name
            "1.2.3",  # Version
            "This is a description",  # Description
            "n",  # Author
            "MIT",  # License
            "~2.7 || ^3.6",  # Python
            "n",  # Interactive packages
            "n",  # Interactive dev packages
            "\n",  # Generate
        ]
    )


@pytest.fixture()
def init_basic_toml():
    return """\
[tool.poetry]
name = "my-package"
version = "1.2.3"
description = "This is a description"
authors = ["Your Name <you@example.com>"]
license = "MIT"

[tool.poetry.dependencies]
python = "~2.7 || ^3.6"

[tool.poetry.dev-dependencies]
"""


def test_basic_interactive(tester, init_basic_inputs, init_basic_toml):
    tester.execute(inputs=init_basic_inputs)
    assert init_basic_toml in tester.io.fetch_output()


def test_interactive_with_dependencies(tester, repo):
    repo.add_package(get_package("django-pendulum", "0.1.6-pre4"))
    repo.add_package(get_package("pendulum", "2.0.0"))
    repo.add_package(get_package("pytest", "3.6.0"))

    inputs = [
        "my-package",  # Package name
        "1.2.3",  # Version
        "This is a description",  # Description
        "n",  # Author
        "MIT",  # License
        "~2.7 || ^3.6",  # Python
        "",  # Interactive packages
        "pendulu",  # Search for package
        "1",  # Second option is pendulum
        "",  # Do not set constraint
        "",  # Stop searching for packages
        "",  # Interactive dev packages
        "pytest",  # Search for package
        "0",
        "",
        "",
        "\n",  # Generate
    ]
    tester.execute(inputs="\n".join(inputs))

    expected = """\
[tool.poetry]
name = "my-package"
version = "1.2.3"
description = "This is a description"
authors = ["Your Name <you@example.com>"]
license = "MIT"

[tool.poetry.dependencies]
python = "~2.7 || ^3.6"
pendulum = "^2.0.0"

[tool.poetry.dev-dependencies]
pytest = "^3.6.0"
"""

    assert expected in tester.io.fetch_output()


def test_empty_license(tester):
    inputs = [
        "my-package",  # Package name
        "1.2.3",  # Version
        "",  # Description
        "n",  # Author
        "",  # License
        "",  # Python
        "n",  # Interactive packages
        "n",  # Interactive dev packages
        "\n",  # Generate
    ]
    tester.execute(inputs="\n".join(inputs))

    expected = """\
[tool.poetry]
name = "my-package"
version = "1.2.3"
description = ""
authors = ["Your Name <you@example.com>"]

[tool.poetry.dependencies]
python = "^{python}"

[tool.poetry.dev-dependencies]
""".format(
        python=".".join(str(c) for c in sys.version_info[:2])
    )

    assert expected in tester.io.fetch_output()


def test_interactive_with_git_dependencies(tester, repo):
    repo.add_package(get_package("pendulum", "2.0.0"))
    repo.add_package(get_package("pytest", "3.6.0"))

    inputs = [
        "my-package",  # Package name
        "1.2.3",  # Version
        "This is a description",  # Description
        "n",  # Author
        "MIT",  # License
        "~2.7 || ^3.6",  # Python
        "",  # Interactive packages
        "git+https://github.com/demo/demo.git",  # Search for package
        "",  # Stop searching for packages
        "",  # Interactive dev packages
        "pytest",  # Search for package
        "0",
        "",
        "",
        "\n",  # Generate
    ]
    tester.execute(inputs="\n".join(inputs))

    expected = """\
[tool.poetry]
name = "my-package"
version = "1.2.3"
description = "This is a description"
authors = ["Your Name <you@example.com>"]
license = "MIT"

[tool.poetry.dependencies]
python = "~2.7 || ^3.6"
demo = {git = "https://github.com/demo/demo.git"}

[tool.poetry.dev-dependencies]
pytest = "^3.6.0"
"""

    assert expected in tester.io.fetch_output()


def test_interactive_with_git_dependencies_with_reference(tester, repo):
    repo.add_package(get_package("pendulum", "2.0.0"))
    repo.add_package(get_package("pytest", "3.6.0"))

    inputs = [
        "my-package",  # Package name
        "1.2.3",  # Version
        "This is a description",  # Description
        "n",  # Author
        "MIT",  # License
        "~2.7 || ^3.6",  # Python
        "",  # Interactive packages
        "git+https://github.com/demo/demo.git@develop",  # Search for package
        "",  # Stop searching for packages
        "",  # Interactive dev packages
        "pytest",  # Search for package
        "0",
        "",
        "",
        "\n",  # Generate
    ]
    tester.execute(inputs="\n".join(inputs))

    expected = """\
[tool.poetry]
name = "my-package"
version = "1.2.3"
description = "This is a description"
authors = ["Your Name <you@example.com>"]
license = "MIT"

[tool.poetry.dependencies]
python = "~2.7 || ^3.6"
demo = {git = "https://github.com/demo/demo.git", rev = "develop"}

[tool.poetry.dev-dependencies]
pytest = "^3.6.0"
"""

    assert expected in tester.io.fetch_output()


def test_interactive_with_git_dependencies_and_other_name(tester, repo):
    repo.add_package(get_package("pendulum", "2.0.0"))
    repo.add_package(get_package("pytest", "3.6.0"))

    inputs = [
        "my-package",  # Package name
        "1.2.3",  # Version
        "This is a description",  # Description
        "n",  # Author
        "MIT",  # License
        "~2.7 || ^3.6",  # Python
        "",  # Interactive packages
        "git+https://github.com/demo/pyproject-demo.git",  # Search for package
        "",  # Stop searching for packages
        "",  # Interactive dev packages
        "pytest",  # Search for package
        "0",
        "",
        "",
        "\n",  # Generate
    ]
    tester.execute(inputs="\n".join(inputs))

    expected = """\
[tool.poetry]
name = "my-package"
version = "1.2.3"
description = "This is a description"
authors = ["Your Name <you@example.com>"]
license = "MIT"

[tool.poetry.dependencies]
python = "~2.7 || ^3.6"
demo = {git = "https://github.com/demo/pyproject-demo.git"}

[tool.poetry.dev-dependencies]
pytest = "^3.6.0"
"""

    assert expected in tester.io.fetch_output()


def test_interactive_with_directory_dependency(tester, repo):
    repo.add_package(get_package("pendulum", "2.0.0"))
    repo.add_package(get_package("pytest", "3.6.0"))

    inputs = [
        "my-package",  # Package name
        "1.2.3",  # Version
        "This is a description",  # Description
        "n",  # Author
        "MIT",  # License
        "~2.7 || ^3.6",  # Python
        "",  # Interactive packages
        "../../fixtures/git/github.com/demo/demo",  # Search for package
        "",  # Stop searching for packages
        "",  # Interactive dev packages
        "pytest",  # Search for package
        "0",
        "",
        "",
        "\n",  # Generate
    ]
    tester.execute(inputs="\n".join(inputs))

    expected = """\
[tool.poetry]
name = "my-package"
version = "1.2.3"
description = "This is a description"
authors = ["Your Name <you@example.com>"]
license = "MIT"

[tool.poetry.dependencies]
python = "~2.7 || ^3.6"
demo = {path = "../../fixtures/git/github.com/demo/demo"}

[tool.poetry.dev-dependencies]
pytest = "^3.6.0"
"""

    assert expected in tester.io.fetch_output()


def test_interactive_with_directory_dependency_and_other_name(tester, repo):
    repo.add_package(get_package("pendulum", "2.0.0"))
    repo.add_package(get_package("pytest", "3.6.0"))

    inputs = [
        "my-package",  # Package name
        "1.2.3",  # Version
        "This is a description",  # Description
        "n",  # Author
        "MIT",  # License
        "~2.7 || ^3.6",  # Python
        "",  # Interactive packages
        "../../fixtures/git/github.com/demo/pyproject-demo",  # Search for package
        "",  # Stop searching for packages
        "",  # Interactive dev packages
        "pytest",  # Search for package
        "0",
        "",
        "",
        "\n",  # Generate
    ]
    tester.execute(inputs="\n".join(inputs))

    expected = """\
[tool.poetry]
name = "my-package"
version = "1.2.3"
description = "This is a description"
authors = ["Your Name <you@example.com>"]
license = "MIT"

[tool.poetry.dependencies]
python = "~2.7 || ^3.6"
demo = {path = "../../fixtures/git/github.com/demo/pyproject-demo"}

[tool.poetry.dev-dependencies]
pytest = "^3.6.0"
"""

    assert expected in tester.io.fetch_output()


def test_interactive_with_file_dependency(tester, repo):
    repo.add_package(get_package("pendulum", "2.0.0"))
    repo.add_package(get_package("pytest", "3.6.0"))

    inputs = [
        "my-package",  # Package name
        "1.2.3",  # Version
        "This is a description",  # Description
        "n",  # Author
        "MIT",  # License
        "~2.7 || ^3.6",  # Python
        "",  # Interactive packages
        "../../fixtures/distributions/demo-0.1.0-py2.py3-none-any.whl",  # Search for package
        "",  # Stop searching for packages
        "",  # Interactive dev packages
        "pytest",  # Search for package
        "0",
        "",
        "",
        "\n",  # Generate
    ]
    tester.execute(inputs="\n".join(inputs))

    expected = """\
[tool.poetry]
name = "my-package"
version = "1.2.3"
description = "This is a description"
authors = ["Your Name <you@example.com>"]
license = "MIT"

[tool.poetry.dependencies]
python = "~2.7 || ^3.6"
demo = {path = "../../fixtures/distributions/demo-0.1.0-py2.py3-none-any.whl"}

[tool.poetry.dev-dependencies]
pytest = "^3.6.0"
"""

    assert expected in tester.io.fetch_output()


def test_python_option(tester):
    inputs = [
        "my-package",  # Package name
        "1.2.3",  # Version
        "This is a description",  # Description
        "n",  # Author
        "MIT",  # License
        "n",  # Interactive packages
        "n",  # Interactive dev packages
        "\n",  # Generate
    ]
    tester.execute("--python '~2.7 || ^3.6'", inputs="\n".join(inputs))

    expected = """\
[tool.poetry]
name = "my-package"
version = "1.2.3"
description = "This is a description"
authors = ["Your Name <you@example.com>"]
license = "MIT"

[tool.poetry.dependencies]
python = "~2.7 || ^3.6"

[tool.poetry.dev-dependencies]
"""

    assert expected in tester.io.fetch_output()


def test_predefined_dependency(tester, repo):
    repo.add_package(get_package("pendulum", "2.0.0"))

    inputs = [
        "my-package",  # Package name
        "1.2.3",  # Version
        "This is a description",  # Description
        "n",  # Author
        "MIT",  # License
        "~2.7 || ^3.6",  # Python
        "n",  # Interactive packages
        "n",  # Interactive dev packages
        "\n",  # Generate
    ]
    tester.execute("--dependency pendulum", inputs="\n".join(inputs))

    expected = """\
[tool.poetry]
name = "my-package"
version = "1.2.3"
description = "This is a description"
authors = ["Your Name <you@example.com>"]
license = "MIT"

[tool.poetry.dependencies]
python = "~2.7 || ^3.6"
pendulum = "^2.0.0"

[tool.poetry.dev-dependencies]
"""

    assert expected in tester.io.fetch_output()


def test_predefined_and_interactive_dependencies(tester, repo):
    repo.add_package(get_package("pendulum", "2.0.0"))
    repo.add_package(get_package("pyramid", "1.10"))

    inputs = [
        "my-package",  # Package name
        "1.2.3",  # Version
        "This is a description",  # Description
        "n",  # Author
        "MIT",  # License
        "~2.7 || ^3.6",  # Python
        "",  # Interactive packages
        "pyramid",  # Search for package
        "0",  # First option
        "",  # Do not set constraint
        "",  # Stop searching for packages
        "n",  # Interactive dev packages
        "\n",  # Generate
    ]

    tester.execute("--dependency pendulum", inputs="\n".join(inputs))

    expected = """\
[tool.poetry]
name = "my-package"
version = "1.2.3"
description = "This is a description"
authors = ["Your Name <you@example.com>"]
license = "MIT"

[tool.poetry.dependencies]
python = "~2.7 || ^3.6"
"""
    output = tester.io.fetch_output()
    assert expected in output
    assert 'pendulum = "^2.0.0"' in output
    assert 'pyramid = "^1.10"' in output


def test_predefined_dev_dependency(tester, repo):
    repo.add_package(get_package("pytest", "3.6.0"))

    inputs = [
        "my-package",  # Package name
        "1.2.3",  # Version
        "This is a description",  # Description
        "n",  # Author
        "MIT",  # License
        "~2.7 || ^3.6",  # Python
        "n",  # Interactive packages
        "n",  # Interactive dev packages
        "\n",  # Generate
    ]

    tester.execute("--dev-dependency pytest", inputs="\n".join(inputs))

    expected = """\
[tool.poetry]
name = "my-package"
version = "1.2.3"
description = "This is a description"
authors = ["Your Name <you@example.com>"]
license = "MIT"

[tool.poetry.dependencies]
python = "~2.7 || ^3.6"

[tool.poetry.dev-dependencies]
pytest = "^3.6.0"
"""

    assert expected in tester.io.fetch_output()


def test_predefined_and_interactive_dev_dependencies(tester, repo):
    repo.add_package(get_package("pytest", "3.6.0"))
    repo.add_package(get_package("pytest-requests", "0.2.0"))

    inputs = [
        "my-package",  # Package name
        "1.2.3",  # Version
        "This is a description",  # Description
        "n",  # Author
        "MIT",  # License
        "~2.7 || ^3.6",  # Python
        "n",  # Interactive packages
        "",  # Interactive dev packages
        "pytest-requests",  # Search for package
        "0",  # Select first option
        "",  # Do not set constraint
        "",  # Stop searching for dev packages
        "\n",  # Generate
    ]

    tester.execute("--dev-dependency pytest", inputs="\n".join(inputs))

    expected = """\
[tool.poetry]
name = "my-package"
version = "1.2.3"
description = "This is a description"
authors = ["Your Name <you@example.com>"]
license = "MIT"

[tool.poetry.dependencies]
python = "~2.7 || ^3.6"

[tool.poetry.dev-dependencies]
"""

    output = tester.io.fetch_output()
    assert expected in output
    assert 'pytest-requests = "^0.2.0"' in output
    assert 'pytest = "^3.6.0"' in output


def test_add_package_with_extras_and_whitespace(tester):
    result = tester._command._parse_requirements(["databases[postgresql, sqlite]"])

    assert result[0]["name"] == "databases"
    assert len(result[0]["extras"]) == 2
    assert "postgresql" in result[0]["extras"]
    assert "sqlite" in result[0]["extras"]


def test_init_existing_pyproject_simple(
    tester, source_dir, init_basic_inputs, init_basic_toml
):
    pyproject_file = source_dir / "pyproject.toml"
    existing_section = """
[tool.black]
line-length = 88
"""
    pyproject_file.write_text(decode(existing_section))
    tester.execute(inputs=init_basic_inputs)
    assert (
        "{}\n{}".format(existing_section, init_basic_toml) in pyproject_file.read_text()
    )


def test_init_existing_pyproject_with_build_system_fails(
    tester, source_dir, init_basic_inputs
):
    pyproject_file = source_dir / "pyproject.toml"
    existing_section = """
[build-system]
requires = ["setuptools >= 40.6.0", "wheel"]
build-backend = "setuptools.build_meta"
"""
    pyproject_file.write_text(decode(existing_section))
    tester.execute(inputs=init_basic_inputs)
    assert (
        tester.io.fetch_output().strip()
        == "A pyproject.toml file with a defined build-system already exists."
    )
    assert "{}".format(existing_section) in pyproject_file.read_text()
