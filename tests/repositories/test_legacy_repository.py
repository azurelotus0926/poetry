import pytest
import shutil

try:
    import urllib.parse as urlparse
except ImportError:
    import urlparse

from poetry.packages import Dependency
from poetry.repositories.exceptions import PackageNotFound
from poetry.repositories.legacy_repository import LegacyRepository
from poetry.repositories.legacy_repository import Page
from poetry.utils._compat import Path


class MockRepository(LegacyRepository):

    FIXTURES = Path(__file__).parent / "fixtures" / "legacy"

    def __init__(self):
        super(MockRepository, self).__init__(
            "legacy", url="http://foo.bar", disable_cache=True
        )

    def _get(self, endpoint):
        parts = endpoint.split("/")
        name = parts[1]

        fixture = self.FIXTURES / (name + ".html")

        with fixture.open() as f:
            return Page(self._url + endpoint, f.read(), {})

    def _download(self, url, dest):
        filename = urlparse.urlparse(url).path.rsplit("/")[-1]
        filepath = self.FIXTURES.parent / "pypi.org" / "dists" / filename

        shutil.copyfile(str(filepath), dest)


def test_page_relative_links_path_are_correct():
    repo = MockRepository()

    page = repo._get("/relative")

    for link in page.links:
        assert link.netloc == "foo.bar"
        assert link.path.startswith("/relative/poetry")


def test_page_absolute_links_path_are_correct():
    repo = MockRepository()

    page = repo._get("/absolute")

    for link in page.links:
        assert link.netloc == "files.pythonhosted.org"
        assert link.path.startswith("/packages/")


def test_sdist_format_support():
    repo = MockRepository()
    page = repo._get("/relative")
    bz2_links = list(filter(lambda link: link.ext == ".tar.bz2", page.links))
    assert len(bz2_links) == 1
    assert bz2_links[0].filename == "poetry-0.1.1.tar.bz2"


def test_missing_version(mocker):
    repo = MockRepository()

    with pytest.raises(PackageNotFound):
        repo._get_release_info("missing_version", "1.1.0")


def test_get_package_information_fallback_read_setup():
    repo = MockRepository()

    package = repo.package("jupyter", "1.0.0")

    assert package.name == "jupyter"
    assert package.version.text == "1.0.0"
    assert (
        package.description
        == "Jupyter metapackage. Install all the Jupyter components in one go."
    )
    assert package.requires == [
        Dependency("notebook", "*"),
        Dependency("qtconsole", "*"),
        Dependency("jupyter-console", "*"),
        Dependency("nbconvert", "*"),
        Dependency("ipykernel", "*"),
        Dependency("ipywidgets", "*"),
    ]
