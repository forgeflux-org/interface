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

from interface.client import GET_REPOSITORY, GET_REPOSITORY_INFO
from interface.forges.payload import RepositoryInfo
from interface.forges.base import F_D_REPOSITORY_NOT_FOUND
from interface.error import F_D_FORGE_UNKNOWN_ERROR

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


def test_get_repository(client, requests_mock):
    """Test version meta route"""
    register_ns(requests_mock)
    register_gitea(requests_mock)

    host = settings.GITEA.host

    repo_url = f"{host}/foo/bar"

    urls = [
        "foo/bar",
        "foo/bar/",
        "foo/bar/baz",
        "foo/bar/baz/",
        "foo/bar/baz?auth=true",
    ]

    payload = {"url": ""}

    for url in urls:
        payload["url"] = f"{host}/{url}"
        resp = client.post(f"/api/v1/repository{GET_REPOSITORY}", json=payload)
        data = resp.json
        assert data["repository_url"] == repo_url


def test_get_repository_info(client, requests_mock):
    register_ns(requests_mock)
    register_gitea(requests_mock)

    print(REPOSITORY_URL)
    payload = {"repository_url": REPOSITORY_URL}
    resp = client.post(f"/api/v1/repository{GET_REPOSITORY_INFO}", json=payload)
    data = RepositoryInfo(**resp.json)
    assert data.description == REPOSITORY_DESCRIPTION
    assert data.owner == REPOSITORY_OWNER
    assert data.name == REPOSITORY_NAME

    payload = {"repository_url": NON_EXISTENT["repo_url"]}
    resp = client.post(f"/api/v1/repository{GET_REPOSITORY_INFO}", json=payload)
    expect_error(resp, F_D_REPOSITORY_NOT_FOUND)

    payload = {"repository_url": FORGE_ERROR["repo_url"]}
    resp = client.post(f"/api/v1/repository{GET_REPOSITORY_INFO}", json=payload)
    expect_error(resp, F_D_FORGE_UNKNOWN_ERROR)
