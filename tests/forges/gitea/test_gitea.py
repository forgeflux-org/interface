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
from urllib.parse import urlparse, urlunparse
from dateutil.parser import parse

from dynaconf import settings
import pytest

from interface.client import GET_REPOSITORY, GET_REPOSITORY_INFO
from interface.forges.payload import RepositoryInfo, CreateIssue
from interface.forges.utils import clean_url
from interface.forges.base import (
    F_D_REPOSITORY_NOT_FOUND,
    F_D_FORGE_FORBIDDEN_OPERATION,
    F_D_REPOSITORY_EXISTS,
)
from interface.error import F_D_FORGE_UNKNOWN_ERROR, Error
from interface.forges.gitea import Gitea

from tests.test_utils import register_ns
from tests.test_errors import expect_error
from tests.forges.gitea.test_utils import (
    register_gitea,
    REPOSITORY_URL,
    REPOSITORY_NAME,
    REPOSITORY_DESCRIPTION,
    REPOSITORY_OWNER,
    NON_EXISTENT,
    FORGE_ERROR,
    register_get_issues_since,
    CREATE_ISSUE,
    CREATE_ISSUE_BODY,
    CREATE_ISSUE_HTML_URL,
    CREATE_ISSUE_TITLE,
    FORGE_FORBIDDEN_ERROR,
    CREATE_REPO_DESCRIPTION,
    CREATE_REPO_NAME,
    CREATE_REPO_DUPLICATE_NAME,
    CREATE_REPO_FORGE_UNKNOWN_ERROR_NAME,
)


def test_get_repository(client):
    """Test version meta route"""
    g = Gitea()
    host = settings.GITEA.host
    repo_url = f"{host}/foo/bar"
    urls = [
        "foo/bar",
        "foo/bar/",
        "foo/bar/baz",
        "foo/bar/baz/",
        "foo/bar/baz?auth=true",
    ]
    for url in urls:
        assert g.get_fetch_remote(f"{host}/{url}") == repo_url


def test_get_repository_info(client, requests_mock):
    register_ns(requests_mock)
    register_gitea(requests_mock)

    g = Gitea()

    (owner, repo) = g.get_owner_repo_from_url(REPOSITORY_URL)
    resp = g.get_repository(owner, repo)
    assert resp.description == REPOSITORY_DESCRIPTION
    assert resp.owner == REPOSITORY_OWNER
    assert resp.name == REPOSITORY_NAME

    (owner, repo) = g.get_owner_repo_from_url(NON_EXISTENT["repo_url"])
    try:
        g.get_repository(owner, repo)
        assert True is False
    except Error as e:
        e.status = F_D_FORGE_UNKNOWN_ERROR.status

    (owner, repo) = g.get_owner_repo_from_url(FORGE_ERROR["repo_url"])
    try:
        g.get_repository(owner, repo)
        assert True is False
    except Error as e:
        e.status = F_D_FORGE_UNKNOWN_ERROR.status


def test_get_issues(requests_mock):
    register_ns(requests_mock)
    register_gitea(requests_mock)
    g = Gitea()

    data = g.get_issues(REPOSITORY_OWNER, REPOSITORY_NAME)
    assert len(data) == 2
    assert data[0]["id"] == 5
    assert data[1]["id"] == 4

    try:
        g.get_issues(NON_EXISTENT["owner"], NON_EXISTENT["repo"])
        assert True is False
    except Error as e:
        e.status = F_D_FORGE_UNKNOWN_ERROR.status

    try:
        g.get_issues(FORGE_ERROR["owner"], FORGE_ERROR["repo"])
        assert True is False
    except Error as e:
        e.status = F_D_FORGE_UNKNOWN_ERROR.status


def test_create_issues(requests_mock):
    register_ns(requests_mock)
    register_gitea(requests_mock)
    g = Gitea()

    payload = CreateIssue(title=CREATE_ISSUE_TITLE, body=CREATE_ISSUE_BODY)
    html_url = g.create_issue(REPOSITORY_OWNER, REPOSITORY_NAME, payload)
    assert html_url == CREATE_ISSUE_HTML_URL

    try:
        g.create_issue(NON_EXISTENT["owner"], NON_EXISTENT["repo"], payload)
        assert True is False
    except Error as e:
        e.status = F_D_FORGE_UNKNOWN_ERROR.status

    try:
        g.create_issue(FORGE_ERROR["owner"], FORGE_ERROR["repo"], payload)
        assert True is False
    except Error as e:
        e.status = F_D_FORGE_UNKNOWN_ERROR.status

    try:
        g.create_issue(
            FORGE_FORBIDDEN_ERROR["owner"], FORGE_FORBIDDEN_ERROR["repo"], payload
        )
        assert True is False
    except Error as e:
        e.status = F_D_FORGE_FORBIDDEN_OPERATION.status


def test_create_repository(requests_mock):
    register_ns(requests_mock)
    register_gitea(requests_mock)
    g = Gitea()

    g.create_repository(CREATE_REPO_NAME, CREATE_REPO_DESCRIPTION)

    try:
        g.create_repository(CREATE_REPO_DUPLICATE_NAME, CREATE_REPO_DESCRIPTION)
        assert True is False
    except Error as e:
        e.status = F_D_REPOSITORY_EXISTS.status

    try:
        g.create_repository(
            CREATE_REPO_FORGE_UNKNOWN_ERROR_NAME, CREATE_REPO_DESCRIPTION
        )
        assert True is False
    except Error as e:
        e.status = F_D_FORGE_UNKNOWN_ERROR.status


def test_get_local_push_and_html_url(requests_mock):
    register_ns(requests_mock)
    g = Gitea()
    host = settings.GITEA.host
    host = urlparse(clean_url(host))

    repos = [
        "foo",
        "bar",
        "baz",
    ]
    for repo in repos:
        assert (
            g.get_local_push_url(repo)
            == f"git@{host.netloc}:{settings.GITEA.username}/{repo}.git"
        )
        path = f"/{settings.GITEA.username}/{repo}"
        assert g.get_local_html_url(repo) == urlunparse(
            (host.scheme, host.netloc, path, "", "", "")
        )
