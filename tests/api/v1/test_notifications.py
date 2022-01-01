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
from interface.db import get_db, DBSubscribe, DBRepo
from interface.client import SUBSCRIBE
from interface.meta import VERSIONS
from interface.error import F_D_INTERFACE_UNREACHABLE, F_D_FORGE_UNKNOWN_ERROR
from interface.forges.base import F_D_REPOSITORY_NOT_FOUND
from interface.utils import clean_url
from interface.git import get_forge

from tests.test_utils import register_ns
from tests.test_errors import expect_error
from tests.forges.gitea.test_utils import (
    register_gitea,
    REPOSITORY_URL,
    NON_EXISTENT,
    FORGE_ERROR,
)

from tests.meta_utils import INTERFACE_VERSION_URL


def test_subscribe(app, client, requests_mock):
    """Test subscribe route"""
    data = {"repository_url": REPOSITORY_URL, "interface_url": INTERFACE_VERSION_URL}
    res = client.post(f"/api/v1/notifications{SUBSCRIBE}", json=data)
    assert res.status == "200 OK"
    assert res.json == {}

    interface_url = clean_url(INTERFACE_VERSION_URL)

    git = get_forge()
    repository_url = git.forge.get_fetch_remote(data["repository_url"])

    (owner, name) = git.forge.get_owner_repo_from_url(repository_url)

    repo = DBRepo.load(name=name, owner=owner)
    assert repo is not None

    subscribers = DBSubscribe.load(repository=repo)
    assert subscribers is not None
    print(subscribers)
    assert subscribers.pop().subscriber.url == interface_url

    # Test forge errors
    data["repository_url"] = NON_EXISTENT["repo_url"]
    res = client.post(f"/api/v1/notifications{SUBSCRIBE}", json=data)
    expect_error(res, F_D_REPOSITORY_NOT_FOUND)

    data["repository_url"] = FORGE_ERROR["repo_url"]
    res = client.post(f"/api/v1/notifications{SUBSCRIBE}", json=data)
    expect_error(res, F_D_FORGE_UNKNOWN_ERROR)


def test_subscribe_interface_unreachable(client):
    interface_url = "https://nonexistent.example.com"
    data = {"repository_url": REPOSITORY_URL, "interface_url": interface_url}
    res = client.post(f"/api/v1/notifications{SUBSCRIBE}", json=data)
    assert expect_error(res, F_D_INTERFACE_UNREACHABLE)
