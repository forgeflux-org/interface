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
from dynaconf import settings
import pytest

from interface.client import GET_REPOSITORY, GET_REPOSITORY_INFO
from interface.forges.payload import RepositoryInfo
from interface.forges.base import F_D_REPOSITORY_NOT_FOUND
from interface.error import F_D_UNKNOWN_FORGE_ERROR, Error
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
        e.status = F_D_UNKNOWN_FORGE_ERROR.status

    (owner, repo) = g.get_owner_repo_from_url(FORGE_ERROR["repo_url"])
    try:
        g.get_repository(owner, repo)
        assert True is False
    except Error as e:
        e.status = F_D_UNKNOWN_FORGE_ERROR.status
