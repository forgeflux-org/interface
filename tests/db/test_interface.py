# Bridges software forges to create a distributed software development environment
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
from interface.settings import settings

from interface.db.interfaces import DBInterfaces
from interface.app import app


def cmp_interface(lhs: DBInterfaces, rhs: DBInterfaces) -> bool:
    """Compare two DBInterfaces objects"""
    return all([lhs.url == rhs.url])


def test_interface(client):
    """Test DBInterfaces database class"""

    url = "https://test_interface.example.com"
    data = DBInterfaces(url=url)

    assert DBInterfaces.load_from_url(url) is None
    assert DBInterfaces.load_from_database_id(11) is None

    data.save()
    from_url = DBInterfaces.load_from_url(url)

    with_id = DBInterfaces.load_from_database_id(from_url.id)

    assert cmp_interface(from_url, data) is True
    assert cmp_interface(from_url, with_id) is True


def test_interface_self_resgistration(app, client, requests_mock):
    from_db = DBInterfaces.load_from_url(settings.SERVER.url)
    assert from_db is not None
