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
from dynaconf import settings

from interface.app import create_app
from interface.meta import VERSIONS

from interface.auth import PublicKey


def test_supported_version(client):
    """Test version meta route"""

    resp = client.get("/_ff/interface/versions")
    data = resp.json
    assert data["versions"] == VERSIONS


def test_public_key_route(client):
    """Test get private key route"""

    resp = client.get("/_ff/interface/key")
    data = PublicKey(**resp.json)
    assert data.key == settings.PRIVATE_KEY
