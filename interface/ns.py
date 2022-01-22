"""
Name service: find interfaces that can work with forges
"""
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
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from urllib.parse import urlunparse, urlparse
from functools import lru_cache

import requests

from dynaconf import settings
from interface.utils import clean_url, since_epoch, trim_url
from interface.error import Error


class NameService:
    __CACHE_TTL = settings.SYSTEM.cache_ttl  # in seconds
    __CACHE_TTL = __CACHE_TTL if __CACHE_TTL is not None else 3660  # in seconds

    @classmethod
    def get_cache_ttl(cls) -> int:
        return cls.__CACHE_TTL

    def __init__(self, forge_url: str):
        self.ns = urlparse(clean_url(settings.SYSTEM.northstar))
        self.forge_url = clean_url(forge_url)
        self._register()

    def _get_url(self, path: str) -> str:
        prefix = "/api/v1/"
        path = f"{prefix}{trim_url(path)}"
        url = urlunparse((self.ns.scheme, self.ns.netloc, path, "", "", ""))
        return url

    def _register(self):
        url = "interface/register"
        url = self._get_url(url)
        payload = {
            "interface_url": settings.SERVER.url,
            "forge_url": [self.forge_url],
        }
        resp = requests.post(url, json=payload)
        if resp.status_code == 200:
            print("registered interface")

    @lru_cache(maxsize=30)
    def __query_wrapped(self, forge_url: str) -> ([str], int):
        url = "forge/interfaces"
        url = self._get_url(url)
        payload = {"forge_url": forge_url}
        resp = requests.post(url, json=payload)
        interfaces = resp.json()
        return (interfaces, since_epoch())

    def query(self, forge_url: str) -> [str]:
        """Get interfaces that service a forge"""
        (interfaces, created_at) = self.__query_wrapped(forge_url)
        if since_epoch() - created_at > self.__CACHE_TTL:
            self.__query_wrapped.cache_clear()
            print("purging cache")
            (interfaces, _) = self.__query_wrapped(forge_url)

        return interfaces
