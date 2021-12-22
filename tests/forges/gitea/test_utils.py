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
from interface.forges.payload import CreateIssue

GITEA_HOST = settings.GITEA.host

REPOSITORY_URL = ""
REPOSITORY_NAME = ""
REPOSITORY_OWNER = ""
REPOSITORY_DESCRIPTION = ""
REPOSITORY_INFO = {}

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

FORGE_FORBIDDEN_ERROR = {
    "owner": "nonexistent",
    "repo": "forbiddenerror",
}

FORGE_FORBIDDEN_ERROR[
    "repo_url"
] = f"{GITEA_HOST}/{FORGE_ERROR['owner']}/{FORGE_ERROR['repo']}"

path = Path(__file__).parent / "get_repository.json"
with path.open() as f:
    REPOSITORY_INFO = json.load(f)
    REPOSITORY_URL = trim_url(REPOSITORY_INFO["html_url"])
    REPOSITORY_NAME = REPOSITORY_INFO["name"]
    REPOSITORY_OWNER = REPOSITORY_INFO["owner"]["login"]
    REPOSITORY_DESCRIPTION = REPOSITORY_INFO["description"]


def register_get_repository(requests_mock):
    def _get_path(owner: str, repo: str) -> str:
        return f"{GITEA_HOST}/api/v1/repos/{owner}/{repo}"

    requests_mock.get(
        _get_path(REPOSITORY_OWNER, REPOSITORY_NAME),
        json=REPOSITORY_INFO,
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
    def _get_path(owner: str, repo: str) -> str:
        return f"{GITEA_HOST}/api/v1/repos/{owner}/{repo}/subscription"

    path = _get_path(REPOSITORY_OWNER, REPOSITORY_NAME)
    requests_mock.put(
        path,
        json={},
    )
    print(f"registered repository subscription: {path}")

    path = _get_path(NON_EXISTENT["owner"], NON_EXISTENT["repo"])
    print(path)
    requests_mock.put(
        path,
        json={},
        status_code=404,
    )
    print(f"registered repository subscription: {path}")

    path = _get_path(FORGE_ERROR["owner"], FORGE_ERROR["repo"])
    requests_mock.put(
        path,
        json={},
        status_code=500,
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


CREATE_ISSUE_TITLE = ""
CREATE_ISSUE_BODY = ""
CREATE_ISSUE = {}
CREATE_ISSUE_HTML_URL = ""

file = Path(__file__).parent / "create-issue.json"
with file.open() as f:
    create_issue = json.load(f)
    CREATE_ISSUE_TITLE = create_issue["title"]
    CREATE_ISSUE_BODY = create_issue["body"]
    CREATE_ISSUE_HTML_URL = create_issue["html_url"]
    CREATE_ISSUE = create_issue


def register_create_issues(requests_mock):
    def _get_path(owner: str, repo: str) -> str:
        return f"{GITEA_HOST}/api/v1/repos/{owner}/{repo}/issues"

    def cb(r: Request, ctx):
        print("Request json payload: \n\n\n\n\n")
        print(r.json())
        payload = CreateIssue(**r.json())
        if all(
            [payload.title == CREATE_ISSUE_TITLE, payload.body == CREATE_ISSUE_BODY]
        ):
            ctx.status_code = 201
            return CREATE_ISSUE
        else:
            ctx.status_code = 500
            return {}

    path = f"{GITEA_HOST}/api/v1/repos/realaravinth/tmp/issues"
    requests_mock.post(
        path,
        json=cb,
    )

    requests_mock.post(
        _get_path(NON_EXISTENT["owner"], NON_EXISTENT["repo"]),
        json={},
        status_code=404,
    )

    requests_mock.post(
        _get_path(FORGE_ERROR["owner"], FORGE_ERROR["repo"]),
        json={},
        status_code=500,
    )

    requests_mock.post(
        _get_path(FORGE_FORBIDDEN_ERROR["owner"], FORGE_FORBIDDEN_ERROR["repo"]),
        json={},
        status_code=403,
    )

    print("Registered get issues")


CREATE_REPO_NAME = ""
CREATE_REPO_BODY = ""
CREATE_REPO = {}
CREATE_REPO_DESCRIPTION = ""
CREATE_REPO_HTML_URL = ""

CREATE_REPO_DUPLICATE_NAME = "duplicate-repo-name"
CREATE_REPO_FORGE_UNKNOWN_ERROR_NAME = "forge-unknown-error-repo-name"

file = Path(__file__).parent / "./create-repository.json"
with file.open() as f:
    create_repo = json.load(f)
    CREATE_REPO_NAME = create_repo["name"]
    CREATE_REPO_DESCRIPTION = create_repo["description"]
    CREATE_REPO_HTML_URL = create_repo["html_url"]
    CREATE_REPO = create_repo


def register_create_repository(requests_mock):
    def cb(r: Request, ctx):
        print("Request json payload: \n\n\n\n\n")
        print(r.json())
        json = r.json()
        if all(
            [
                json["name"] == CREATE_REPO_NAME,
                json["description"] == CREATE_REPO_DESCRIPTION,
            ]
        ):
            ctx.status_code = 201
            return CREATE_REPO
        elif json["name"] == CREATE_REPO_DUPLICATE_NAME:
            # Duplicate name
            ctx.status_code = 409
            return {}
        elif json["name"] == CREATE_REPO_FORGE_UNKNOWN_ERROR_NAME:
            ctx.status_code = 300
            return {}
        else:
            ctx.status_code = 500
            return {}

    path = f"{GITEA_HOST}/api/v1/user/repos"
    requests_mock.post(
        path,
        json=cb,
    )
    print(f"Registered create repo mocking at {path}")


def register_gitea(requests_mock):
    register_get_repository(requests_mock)
    register_subscribe(requests_mock)
    register_get_issues(requests_mock)
    register_create_issues(requests_mock)
    register_create_repository(requests_mock)
