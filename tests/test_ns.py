# North Star ---  A lookup service for forged fed ecosystem
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
from interface.app import create_app
from interface.ns import NameService
from interface.git import get_forge
from interface.utils import clean_url
from interface.local_settings import INTERFACE_URL, PORT


def test_ns(app):
    """Test ns"""
    forge = get_forge().forge.get_forge_url()

    print(forge)
    ns = NameService(forge)
    interface_url = ns.query(forge)
    assert clean_url(f"http://{INTERFACE_URL}:{PORT}") in interface_url
    assert clean_url(f"http://{INTERFACE_URL}:{PORT}") in interface_url
