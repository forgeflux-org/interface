""" Utilities for Gitea functionality"""
# Interface ---  API-space federation for software forges
# Copyright © 2022 Aravinth Manivannan <realaravinth@batsense.net>
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
import re
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from requests import Request
from requests_mock import CookieJar
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


CSRF_FORK_REPO_NAME = "csrf"
CSRF_FORK_REPO_ID = 20
CSRF_FORK_REPO_LOGOUT_ID = 20
CSRF_UID = ""
CSRF_SUCCESSFUL_REDIRECTION = f"/{settings.GITEA.username}/csrf"
FORK_REPO_NAME = ""
FORK_REPO_BODY = ""
FORK_REPO = {}
FORK_REPO_DESCRIPTION = ""
FORK_REPO_HTML_URL = ""

CREATE_REPO_DUPLICATE_NAME = "duplicate-repo-name"
CREATE_REPO_FORGE_UNKNOWN_ERROR_NAME = "forge-unknown-error-repo-name"


CSRF_TOKEN = "foo"
CSRF_TOKEN_2 = "bar"


def get_page(inner: str) -> str:
    page = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
          <meta charset="UTF-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <title>Document</title>
        </head>
        <body>
          <form action="">
          {inner}
          </form>
        </body>
        </html>
    """
    return page


PAGE1 = f"""
    <input type="hidden" name="_csrf" value={CSRF_TOKEN}>
    <input type="hidden" name="_csrf" value={CSRF_TOKEN_2}>
"""

PAGE2 = f"""
    <p class="foobar">foobarbaz</p>
    <input type="hidden" value={CSRF_TOKEN} name="_csrf" value={CSRF_TOKEN_2}>
"""

file = Path(__file__).parent / "./fork-successful.json"
with file.open() as f:
    fork_repo = json.load(f)
    FORK_REPO_NAME = fork_repo["name"]
    FORK_REPO_DESCRIPTION = fork_repo["description"]
    FORK_REPO_HTML_URL = fork_repo["html_url"]
    FORK_REPO = fork_repo
    FORK_OWNER = fork_repo["parent"]["owner"]["login"]
    CSRF_UID = fork_repo["owner"]["id"]


GITEA_LOGIN_COOKIE = {"k": "auth", "v": "loggedin"}


def register_create_fork(requests_mock):
    json_path = f"{GITEA_HOST}/api/v1/repos/{FORK_OWNER}/{FORK_REPO_NAME}/forks"
    json_path_custom_name = (
        f"{GITEA_HOST}/api/v1/repos/{FORK_OWNER}/{CSRF_FORK_REPO_NAME}/forks"
    )
    web_path = f"{GITEA_HOST}/repo/fork/{CSRF_FORK_REPO_ID}"
    login_url = f"{GITEA_HOST}/user/login"

    domain = urlparse(GITEA_HOST).netloc

    pattern = f"{GITEA_HOST}/api/v1/repos/{FORK_OWNER}/{CSRF_FORK_REPO_NAME}-*"
    csrf_repo_info_matcher = re.compile(pattern)
    requests_mock.get(csrf_repo_info_matcher, json={}, status_code=404)
    print(f"Registered mock for pattern GET {pattern}")

    def login_cb(r: Request, ctx):
        url = r.url
        data = parse_qs(r.text)

        if all(
            [
                url == login_url,
                data["_csrf"][0] == CSRF_TOKEN,
                data["user_name"][0] == settings.GITEA.username,
                data["password"][0] == settings.GITEA.password,
            ]
        ):
            ctx.status_code = 302
            # jar = CookieJar() jar.set(GITEA_LOGIN_COOKIE["k"], GITEA_LOGIN_COOKIE["v"], domain=domain, path="/") print(jar)
            # ctx.cookies = jar
            cookie = f"{GITEA_LOGIN_COOKIE['k']}={GITEA_LOGIN_COOKIE['v']}; Path=/; domain={domain};"
            print(cookie)
            ctx.headers = {
                "location": CSRF_SUCCESSFUL_REDIRECTION,
                # Cookiejar doesn't work https://github.com/jamielennox/requests-mock/issues/17
                "Set-Cookie": cookie,
            }
            return ""

    requests_mock.get(
        login_url,
        text=PAGE1,
    )
    print(f"Registered fork CSRF GET LOGIN route {login_url}")

    requests_mock.post(
        login_url,
        text=login_cb,
    )
    print(f"Registered fork CSRF POST LOGIN route {login_url}")

    def cb_name_exists(r: Request, ctx):
        resp = {"message": "repository is already exists by user"}
        ctx.status_code = 500
        return resp

    def cb(r: Request, ctx):
        data = parse_qs(r.text)
        print(f"test util: {data}")
        #        print("printing ocokies in test util")
        #        print(f"headers: {r.headers}")
        #        print(r.cookies)

        print(data["_csrf"][0] == CSRF_TOKEN)
        print(data["repo_name"][0] != CSRF_FORK_REPO_NAME)
        print(data["uid"][0] == str(CSRF_UID))
        print(f'{data["uid"][0]} {str(CSRF_UID)}')
        print("&description=" in r.text)

        if all(
            [
                data["_csrf"][0] == CSRF_TOKEN,
                data["repo_name"][0] != CSRF_FORK_REPO_NAME,
                data["uid"][0] == str(CSRF_UID),
                "&description=" in r.text,
            ]
        ):
            #            #if r.cookies == GITEA_LOGIN_COOKIE:
            print("user logged in")
            ctx.status_code = 302
            ctx.headers = {
                "location": CSRF_SUCCESSFUL_REDIRECTION,
            }
            ctx.cookies = CookieJar()
            print("logging user out")
            # return '<a href="/user/sign_up">Need an account? Register now.</a>'
            return ""

        ctx.status_code = 500
        return ""

    requests_mock.post(
        json_path_custom_name,
        json=cb_name_exists,
    )
    print(f"Registered fork CSRF JSON route {json_path_custom_name}")

    requests_mock.get(
        web_path,
        text=PAGE1,
    )
    print(f"Registered fork CSRF GET form route {web_path}")

    requests_mock.post(
        web_path,
        text=cb,
    )
    print(f"Registered fork CSRF POST form route {web_path}")

    requests_mock.post(json_path, json=FORK_REPO, status_code=202)
    print(f"Registered fork json route {json_path}")

    def _get_path(owner: str, repo: str) -> str:
        return f"{GITEA_HOST}/api/v1/repos/{owner}/{repo}"

    requests_mock.get(
        _get_path(FORK_OWNER, CSRF_FORK_REPO_NAME), json={"id": CSRF_FORK_REPO_ID}
    )


USER_INFO = {}

file = Path(__file__).parent / "./user-info.json"
with file.open() as f:
    USER_INFO = json.load(f)


def register_gitea_user_info(requests_mock):
    requests_mock.get("/api/v1/user", json=USER_INFO)


def register_gitea(requests_mock):
    register_get_repository(requests_mock)
    register_subscribe(requests_mock)
    register_get_issues(requests_mock)
    register_create_issues(requests_mock)
    register_create_repository(requests_mock)
    register_create_fork(requests_mock)
    register_gitea_user_info(requests_mock)
