from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any

from packaging.utils import canonicalize_name
from poetry.core.packages.package import Package
from poetry.core.semver.version import Version

from poetry.inspection.info import PackageInfo
from poetry.repositories.exceptions import PackageNotFound
from poetry.repositories.http import HTTPRepository
from poetry.repositories.link_sources.html import SimpleRepositoryPage


if TYPE_CHECKING:
    from packaging.utils import NormalizedName
    from poetry.core.packages.utils.link import Link
    from poetry.core.semver.version_constraint import VersionConstraint

    from poetry.config.config import Config


class LegacyRepository(HTTPRepository):
    def __init__(
        self,
        name: str,
        url: str,
        config: Config | None = None,
        disable_cache: bool = False,
    ) -> None:
        if name == "pypi":
            raise ValueError("The name [pypi] is reserved for repositories")

        super().__init__(name, url.rstrip("/"), config, disable_cache)

    def package(
        self, name: str, version: str, extras: list[str] | None = None
    ) -> Package:
        """
        Retrieve the release information.

        This is a heavy task which takes time.
        We have to download a package to get the dependencies.
        We also need to download every file matching this release
        to get the various hashes.

        Note that this will be cached so the subsequent operations
        should be much faster.
        """
        try:
            index = self._packages.index(Package(name, version, version))

            return self._packages[index]
        except ValueError:
            package = super().package(name, version, extras)
            package._source_type = "legacy"
            package._source_url = self._url
            package._source_reference = self.name

            return package

    def find_links_for_package(self, package: Package) -> list[Link]:
        page = self._get_page(f"/{package.name}/")
        if page is None:
            return []

        return list(page.links_for_version(package.name, package.version))

    def _find_packages(
        self, name: NormalizedName, constraint: VersionConstraint
    ) -> list[Package]:
        """
        Find packages on the remote server.
        """
        versions: list[Version]

        key: str = name
        if not constraint.is_any():
            key = f"{key}:{constraint!s}"

        if self._cache.store("matches").has(key):
            versions = self._cache.store("matches").get(key)
        else:
            page = self._get_page(f"/{name}/")
            if page is None:
                self._log(
                    f"No packages found for {name}",
                    level="debug",
                )
                return []

            versions = [
                version for version in page.versions(name) if constraint.allows(version)
            ]
            self._cache.store("matches").put(key, versions, 5)

        return [
            Package(
                name,
                version,
                source_type="legacy",
                source_reference=self.name,
                source_url=self._url,
            )
            for version in versions
        ]

    def _get_release_info(self, name: str, version: str) -> dict[str, Any]:
        page = self._get_page(f"/{canonicalize_name(name)}/")
        if page is None:
            raise PackageNotFound(f'No package named "{name}"')

        links = list(page.links_for_version(name, Version.parse(version)))

        return self._links_to_data(
            links,
            PackageInfo(
                name=name,
                version=version,
                summary="",
                platform=None,
                requires_dist=[],
                requires_python=None,
                files=[],
                cache_version=str(self.CACHE_VERSION),
            ),
        )

    def _get_page(self, endpoint: str) -> SimpleRepositoryPage | None:
        response = self._get_response(endpoint)
        if not response:
            return None
        return SimpleRepositoryPage(response.url, response.text)
