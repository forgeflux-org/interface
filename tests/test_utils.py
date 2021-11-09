""" Test interface handlers"""
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
from urllib.parse import urlparse, urlunparse

from interface.app import create_app
from interface.utils import clean_url
from interface.db import get_db

def test_clean_url(client):
    """Test clean_url works"""
    urls = [
        "https://example.com/foo",
        "https://example.com/foo?q=sdf",
        "https://example.com",
    ]
    for url in urls:
        cleaned = urlparse(clean_url(url))
        assert cleaned.scheme == "https"
        assert cleaned.netloc == "example.com"
        assert cleaned.path == ""
        assert cleaned.query == ""
