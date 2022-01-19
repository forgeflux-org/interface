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
from urllib.parse import urlparse, urlunparse
from dateutil.parser import parse

from dynaconf import settings
import pytest

from interface.utils import get_rand

# from interface.client import GET_REPOSITORY, GET_REPOSITORY_INFO
from interface.forges.payload import (
    CreateIssue,
    Author,
    RepositoryInfo,
    MetaData,
)
from interface.forges.utils import clean_url
from interface.git import Git, get_forge, get_user, get_repo_from_actor_name, get_repo
from interface.forges.base import (
    F_D_REPOSITORY_NOT_FOUND,
    F_D_FORGE_FORBIDDEN_OPERATION,
    F_D_REPOSITORY_EXISTS,
    F_D_INVALID_ISSUE_URL,
)
from interface.error import F_D_FORGE_UNKNOWN_ERROR, Error
from interface.forges.gitea import Gitea, HTMLClient
from interface.forges.gitea.responses import GiteaComment
from interface.forges.gitea.utils import get_issue_index, get_owner_repo_from_url

from tests.test_utils import register_ns
from tests.test_errors import expect_error, pytest_expect_errror
from tests.forges.gitea.test_utils import (
    GITEA_HOST,
    register_gitea,
    REPOSITORY_URL,
    REPOSITORY_NAME,
    REPOSITORY_DESCRIPTION,
    REPOSITORY_OWNER,
    NON_EXISTENT,
    FORGE_ERROR,
    register_get_issues_since,
    # Create issue
    CREATE_ISSUE,
    CREATE_ISSUE_BODY,
    CREATE_ISSUE_HTML_URL,
    CREATE_ISSUE_TITLE,
    FORGE_FORBIDDEN_ERROR,
    # Create repo
    CREATE_REPO_DESCRIPTION,
    CREATE_REPO_NAME,
    CREATE_REPO_DUPLICATE_NAME,
    CREATE_REPO_FORGE_UNKNOWN_ERROR_NAME,
    # Fork
    FORK_REPO_NAME,
    CSRF_FORK_REPO_ID,
    CSRF_FORK_REPO_NAME,
    CSRF_UID,
    CSRF_SUCCESSFUL_REDIRECTION,
    FORK_OWNER,
    USER_INFO,
    ISSUE_URL,
    ISSUE_HTML_URL,
    SINGLE_ISSUE,
    COMMENTS,
    GET_COMMENTS_URL,
)


def test_get_repository(client, requests_mock):
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

    g = Gitea()

    (owner, repo) = g.get_owner_repo_from_url(REPOSITORY_URL)
    resp = g.get_repository(owner, repo)
    assert resp.description == REPOSITORY_DESCRIPTION
    assert resp.owner == REPOSITORY_OWNER
    assert resp.name == REPOSITORY_NAME

    (owner, repo) = g.get_owner_repo_from_url(NON_EXISTENT["repo_url"])
    with pytest.raises(Error) as error:
        g.get_repository(owner, repo)
    assert pytest_expect_errror(error, F_D_REPOSITORY_NOT_FOUND)

    (owner, repo) = g.get_owner_repo_from_url(FORGE_ERROR["repo_url"])
    with pytest.raises(Error) as error:
        g.get_repository(owner, repo)
    assert pytest_expect_errror(error, F_D_FORGE_UNKNOWN_ERROR)


def test_get_issues(requests_mock):

    g = Gitea()

    data = g.get_issues(REPOSITORY_OWNER, REPOSITORY_NAME)
    assert len(data) == 2
    assert data[0]["id"] == 5
    assert data[1]["id"] == 4

    with pytest.raises(Error) as error:
        g.get_issues(NON_EXISTENT["owner"], NON_EXISTENT["repo"])
    assert pytest_expect_errror(error, F_D_REPOSITORY_NOT_FOUND)

    with pytest.raises(Error) as error:
        g.get_issues(FORGE_ERROR["owner"], FORGE_ERROR["repo"])
    assert pytest_expect_errror(error, F_D_FORGE_UNKNOWN_ERROR)

    signle_issue = g.get_issue(
        owner=SINGLE_ISSUE["repository"]["owner"],
        repo=SINGLE_ISSUE["repository"]["name"],
        issue_id=SINGLE_ISSUE["number"],
    )
    assert signle_issue.url == ISSUE_URL
    assert signle_issue.id == SINGLE_ISSUE["id"]
    signle_issue.get_created_epoch()
    signle_issue.get_updated_epoch()
    signle_issue.repo_scope_id()


def test_get_comments(requests_mock):
    g = Gitea()

    comments = g.get_comments(ISSUE_HTML_URL)
    assert len(comments) == 3
    assert comments[2].id == 29
    assert comments[2].user.id == USER_INFO["id"]
    signle_issue = g.get_issue(
        owner=SINGLE_ISSUE["repository"]["owner"],
        repo=SINGLE_ISSUE["repository"]["name"],
        issue_id=SINGLE_ISSUE["number"],
    )
    assert GiteaComment.from_issue(signle_issue) == comments


def test_create_issues(requests_mock):

    g = Gitea()
    author = Author(
        name="Author",
        fqdn_username="author@example.com",
        profile_url="https://example.com",
    )
    meta = MetaData(html_url="", author=author, interface_url="")
    repo = RepositoryInfo(
        name=REPOSITORY_NAME,
        owner=REPOSITORY_OWNER,
        description="",
        html_url=author.profile_url,
    )

    payload = CreateIssue(
        title=CREATE_ISSUE_TITLE, repository=repo, body=CREATE_ISSUE_BODY, meta=meta
    )
    html_url = g.create_issue(REPOSITORY_OWNER, REPOSITORY_NAME, payload)
    assert html_url == CREATE_ISSUE_HTML_URL

    with pytest.raises(Error) as error:
        payload.repository.owner = NON_EXISTENT["owner"]
        payload.repository.name = NON_EXISTENT["repo"]
        g.create_issue(NON_EXISTENT["owner"], NON_EXISTENT["repo"], payload)

    assert pytest_expect_errror(error, F_D_REPOSITORY_NOT_FOUND)

    with pytest.raises(Error) as error:
        payload.repository.owner = FORGE_ERROR["owner"]
        payload.repository.name = FORGE_ERROR["repo"]
        g.create_issue(FORGE_ERROR["owner"], FORGE_ERROR["repo"], payload)
    assert pytest_expect_errror(error, F_D_FORGE_UNKNOWN_ERROR)

    with pytest.raises(Error) as error:
        payload.repository.owner = FORGE_FORBIDDEN_ERROR["owner"]
        payload.repository.name = FORGE_FORBIDDEN_ERROR["repo"]
        g.create_issue(
            FORGE_FORBIDDEN_ERROR["owner"], FORGE_FORBIDDEN_ERROR["repo"], payload
        )
    assert pytest_expect_errror(error, F_D_FORGE_FORBIDDEN_OPERATION)


def test_create_repository(requests_mock):

    g = Gitea()

    g.create_repository(CREATE_REPO_NAME, CREATE_REPO_DESCRIPTION)

    with pytest.raises(Error) as error:
        g.create_repository(CREATE_REPO_DUPLICATE_NAME, CREATE_REPO_DESCRIPTION)
    assert pytest_expect_errror(error, F_D_REPOSITORY_EXISTS)

    with pytest.raises(Error) as error:
        g.create_repository(
            CREATE_REPO_FORGE_UNKNOWN_ERROR_NAME, CREATE_REPO_DESCRIPTION
        )
    assert pytest_expect_errror(error, F_D_FORGE_UNKNOWN_ERROR)


def test_get_local_push_and_html_url(requests_mock):

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


def test_subscribe(requests_mock):

    g = Gitea()

    g.subscribe(REPOSITORY_OWNER, REPOSITORY_NAME)

    with pytest.raises(Error) as error:
        g.subscribe(NON_EXISTENT["owner"], NON_EXISTENT["repo"])
    assert pytest_expect_errror(error, F_D_REPOSITORY_NOT_FOUND)

    with pytest.raises(Error) as error:
        g.get_issues(FORGE_ERROR["owner"], FORGE_ERROR["repo"])
    assert pytest_expect_errror(error, F_D_FORGE_UNKNOWN_ERROR)


def test_html_web_client(requests_mock):

    html_client = HTMLClient()
    resp = html_client.fork(
        CSRF_FORK_REPO_ID, f"{CSRF_FORK_REPO_NAME}-{get_rand(10)}", CSRF_UID
    )
    assert CSRF_SUCCESSFUL_REDIRECTION in urlparse(resp).path


def test_fork(app, requests_mock):
    g = get_forge()
    cached_random_name = g.fork(FORK_OWNER, CSRF_FORK_REPO_NAME)
    cached_random_name != CSRF_FORK_REPO_NAME
    assert cached_random_name == g.fork(FORK_OWNER, CSRF_FORK_REPO_NAME)
    assert g.fork(FORK_OWNER, FORK_REPO_NAME) == FORK_REPO_NAME
    assert g.fork(FORK_OWNER, FORK_REPO_NAME) == FORK_REPO_NAME


def test_user(app, requests_mock):
    g = get_forge()
    data = g.forge.get_user(USER_INFO["username"])
    assert data.user_id == USER_INFO["username"]


def test_git_cache_get_user(app, requests_mock):
    data = get_user(USER_INFO["username"])
    assert data.user_id == USER_INFO["username"]


def test_git_cache_get_repo(app, requests_mock):
    g = get_forge()
    data = get_user(USER_INFO["username"])
    assert data.user_id == USER_INFO["username"]

    (owner, repo) = g.forge.get_owner_repo_from_url(REPOSITORY_URL)
    resp = get_repo(owner, repo)
    assert resp.description == REPOSITORY_DESCRIPTION
    assert resp.owner.user_id == REPOSITORY_OWNER
    assert resp.name == REPOSITORY_NAME


def test_git_cache_get_repo_from_actor_url(app, requests_mock):
    g = get_forge()
    data = get_user(USER_INFO["username"])
    assert data.user_id == USER_INFO["username"]

    (owner, repo) = g.forge.get_owner_repo_from_url(REPOSITORY_URL)
    resp = get_repo(owner, repo)
    assert resp.description == REPOSITORY_DESCRIPTION
    assert resp.owner.user_id == REPOSITORY_OWNER
    assert resp.name == REPOSITORY_NAME


def test_get_issue_url(app, requests_mock):
    g = get_forge()
    (owner, repo) = g.forge.get_owner_repo_from_url(ISSUE_HTML_URL)
    issue_id = g.forge.get_issue_index(ISSUE_HTML_URL)
    assert g.forge.get_issue_html_url(owner=owner, repo=repo, issue_id=issue_id)
