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
from interface.db import get_db
from interface.client import SUBSCRIBE
from interface.meta import VERSIONS
from interface.error import F_D_INTERFACE_UNREACHABLE, F_D_FORGE_UNKNOWN_ERROR
from interface.forges.base import F_D_REPOSITORY_NOT_FOUND
from interface.utils import clean_url

from tests.test_utils import register_ns
from tests.test_errors import expect_error
from tests.forges.gitea.test_utils import (
    register_gitea,
    REPOSITORY_URL,
    NON_EXISTENT,
    FORGE_ERROR,
)


def test_subscribe(client, requests_mock):
    """Test subscribe route"""
    register_ns(requests_mock)
    register_gitea(requests_mock)

    interface_url = "https://interfac9.example.com/_ff/interface/versions"
    resp = {"versions": VERSIONS}
    requests_mock.get(interface_url, json=resp)

    data = {"repository_url": REPOSITORY_URL, "interface_url": interface_url}
    res = client.post(f"/api/v1/notifications{SUBSCRIBE}", json=data)
    assert res.status == "200 OK"
    assert res.json == {}

    conn = get_db()
    cur = conn.cursor()
    interface_id = cur.execute(
        "SELECT ID from interface_interfaces WHERE url = ?",
        (clean_url(interface_url),),
    ).fetchone()[0]

    repository_id = cur.execute(
        "SELECT ID from interface_local_repositories WHERE html_url = ?",
        (REPOSITORY_URL,),
    ).fetchone()[0]

    res = cur.execute(
        """
        SELECT EXISTS (
            SELECT 1 FROM interface_event_subscriptsions
            WHERE repository_id = ? AND interface_id = ?
            );""",
        (repository_id, interface_id),
    ).fetchone()[0]
    assert res is 1

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
