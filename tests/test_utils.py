""" Test interface handlers"""
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
from urllib.parse import urlparse, urlunparse
from datetime import datetime, timezone
from interface.settings import settings

from interface.app import create_app
from interface.utils import clean_url, trim_url, since_epoch, from_epoch
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


def test_trim_url():
    """Test trim_url"""

    url = "https://example.com"
    assert trim_url(url) == url
    assert trim_url(f"{url}/") == url

    path = "/foo/bar"
    assert trim_url(path) == path
    assert trim_url(f"{path}/") == path


def register_ns(requests_mock):
    ns = clean_url(settings.SYSTEM.northstar)
    query = f"{ns}/api/v1/forge/interfaces"
    register = f"{ns}/api/v1/interface/register"
    interface_url = clean_url(settings.SERVER.url)

    requests_mock.post(register, json={})
    requests_mock.post(query, json=[interface_url])


def test_utils():
    date = datetime(2022, 1, 18, 16, 27, 18, tzinfo=timezone.utc)
    epoch = since_epoch(date=date)
    assert from_epoch(epoch) == date
    assert from_epoch(since_epoch()) > date
