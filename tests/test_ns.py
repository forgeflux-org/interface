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
import time

from interface.settings import settings
from interface.ns import NameService
from interface.git import get_forge
from interface.utils import clean_url

from tests.test_utils import register_ns


def test_ns(app, requests_mock):
    """Test ns"""
    clean_interface_url = clean_url(settings.SERVER.url)
    forge = get_forge().forge.get_forge_url()
    ns = NameService(forge)
    assert clean_interface_url in ns.query(forge)
    time.sleep(ns.get_cache_ttl() * 2)
    assert clean_interface_url in ns.query(forge)
