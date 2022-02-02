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
from urllib.parse import urlparse

from interface.db import INTERFACE_DOMAIN, DBUser, get_db
from interface.git import get_user
from interface.utils import CONTENT_TYPE_ACTIVITY_JSON

from .forges.gitea.test_utils import REPOSITORY_OWNER


def test_user_actor(client, requests_mock):
    """Test user actor info route"""
    assert INTERFACE_DOMAIN != "example.com"  # Please change domain settings

    user = get_user(REPOSITORY_OWNER)

    item = [
        item
        for item in user.webfinger()["links"]
        if item["type"] == CONTENT_TYPE_ACTIVITY_JSON
    ][0]
    path = urlparse(item["href"]).path
    print(path)
    headers = {
        "Accept": CONTENT_TYPE_ACTIVITY_JSON,
    }
    resp = client.get(path, headers=headers)
    assert resp.status_code == 200
    assert resp.json == user.to_actor()
    client.allow_subdomain_redirects = False
    resp = client.get(path, follow_redirects=False, headers={})
    assert resp.status_code == 302
    assert resp.headers["Location"] == user.profile_url
