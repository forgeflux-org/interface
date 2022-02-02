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
from interface.db import DBUser, DBComment, DBActivity, INTERFACE_BASE_URL


def test_nodeinfo(client):
    """Test nodeinfo routes"""

    resp = client.get("/.well-known/nodeinfo")
    assert resp.status_code == 200
    data = resp.json
    assert (
        data["links"][0]["href"]
        == f"{INTERFACE_BASE_URL}/.well-known/nodeinfo/2.0.json"
    )

    resp = client.get("/.well-known/nodeinfo/2.0.json")
    assert resp.status_code == 200
    data = resp.json
    assert "interface.forgeflux.org" in data["metadata"]["forgeflux-protocols"]
    usage = data["usage"]
    assert usage["localPosts"] == DBActivity.count.count()
    assert usage["localComments"] == DBComment.count.count()
    assert usage["users"]["total"] == DBUser.count.count()
    assert usage["users"]["activeMonth"] == DBActivity.monthly_active_users.count()
    assert usage["users"]["activeHalfyear"] == DBActivity.six_month_active_users.count()
