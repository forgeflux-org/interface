""" Test interface handlers"""
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
from urllib.parse import urlparse, urlunparse
from dynaconf import settings

from interface.app import create_app
from interface.utils import clean_url, trim_url, verify_interface_online
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
    interface_url = clean_url(settings.SERVER.domain)

    requests_mock.post(register, json={})
    requests_mock.post(query, json=[interface_url])


def test_verify_instance_online(client, requests_mock):
    interface_url = "https://interfac9.example.com/_ff/interface/versions"
    version = "1"
    resp = {"versions": [version]}
    requests_mock.get(interface_url, json=resp)
    assert verify_interface_online(clean_url(interface_url), version) is True
    assert verify_interface_online(clean_url(interface_url), str(2)) is False


def test_verify_instance_interface_unreachable():
    interface_url = "https://nonexistent.example.com"
    assert verify_interface_online(clean_url(interface_url), "1") is False
