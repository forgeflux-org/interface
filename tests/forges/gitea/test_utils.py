""" Utilities for Gitea functionality"""
# Interface ---  API-space federation for software forges
# Copyright © 2021 Aravinth Manivannan <realaravinth@batsense.net>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import json
from pathlib import Path

from requests import Request
from dynaconf import settings

from interface.client import GET_REPOSITORY_INFO
from interface.utils import trim_url

GITEA_HOST = settings.GITEA.host

REPOSITORY_URL = ""
REPOSITORY_NAME = ""
REPOSITORY_OWNER = ""
REPOSITORY_DESCRIPTION = ""
data = {}

NON_EXISTENT = {
    "owner": "nonexistent",
    "repo": "nonexistent",
}

NON_EXISTENT[
    "repo_url"
] = f"{GITEA_HOST}/{NON_EXISTENT['owner']}/{NON_EXISTENT['repo']}"

FORGE_ERROR = {
    "owner": "nonexistent",
    "repo": "forgeerror",
}

FORGE_ERROR["repo_url"] = f"{GITEA_HOST}/{FORGE_ERROR['owner']}/{FORGE_ERROR['repo']}"


path = Path(__file__).parent / "get_repository.json"
with path.open() as f:
    data = json.load(f)
    REPOSITORY_URL = trim_url(data["html_url"])
    REPOSITORY_NAME = data["name"]
    REPOSITORY_OWNER = data["owner"]["login"]
    REPOSITORY_DESCRIPTION = data["description"]


def register_get_repository(requests_mock):
    def _get_path(owner: str, repo: str) -> str:
        return f"{GITEA_HOST}/api/v1/repos/{owner}/{repo}"

    requests_mock.get(
        _get_path(REPOSITORY_OWNER, REPOSITORY_NAME),
        json=data,
    )

    requests_mock.get(
        _get_path(NON_EXISTENT["owner"], NON_EXISTENT["repo"]),
        json={},
        status_code=404,
    )

    requests_mock.get(
        _get_path(FORGE_ERROR["owner"], FORGE_ERROR["repo"]),
        json={},
        status_code=500,
    )

    print(f"registered get repository: {path}")


def register_subscribe(requests_mock):
    path = (
        f"{GITEA_HOST}/api/v1/repos/{REPOSITORY_OWNER}/{REPOSITORY_NAME}/subscription"
    )
    requests_mock.put(
        path,
        json={},
    )
    print(f"registered repository subscription: {path}")


def register_get_issues_since(requests_mock):
    file = Path(__file__).parent / "get_issiues_since_2021-10-23T16-31-07+05-30.json"
    with file.open() as f:
        data = json.load(f)
        path = f"{GITEA_HOST}/api/v1/repos/realaravinth/tmp/issues?since=2021-10-23T17%3A06%3A02%2B05%3A30"
        requests_mock.get(
            path,
            json=data,
        )
        print(f"Registered get issues: {path}")


def register_get_issues(requests_mock):
    def _get_path(owner: str, repo: str) -> str:
        return f"{GITEA_HOST}/api/v1/repos/{owner}/{repo}/issues"

    file = Path(__file__).parent / "get_issues.json"
    with file.open() as f:
        data = json.load(f)
        path = f"{GITEA_HOST}/api/v1/repos/realaravinth/tmp/issues"
        requests_mock.get(
            path,
            json=data,
        )

    requests_mock.get(
        _get_path(NON_EXISTENT["owner"], NON_EXISTENT["repo"]),
        json={},
        status_code=404,
    )

    requests_mock.get(
        _get_path(FORGE_ERROR["owner"], FORGE_ERROR["repo"]),
        json={},
        status_code=500,
    )

    print("Registered get issues")


def register_gitea(requests_mock):
    register_get_repository(requests_mock)
    register_subscribe(requests_mock)
    register_get_issues(requests_mock)
