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
import requests
from urllib.parse import urlunparse, urlparse

from dynaconf import settings
from interface.utils import clean_url
from interface.error import Error


class NSCache:
    # TODO implement clean up routine to invalidate cache after certain TTL
    def __init__(self):
        self.__cache = {}

    def search(self, forge_url: str) -> [str]:
        forge_url = clean_url(forge_url)
        if forge_url in self.__cache:
            return self.__cache["forge_url"]
        return None

    def add(self, forge_url: str, interfaces: [str]):
        forge_url = clean_url(forge_url)
        cleaned_interfaces = []
        for i in interfaces:
            cleaned_interfaces.append(clean_url(i))

        if forge_url not in self.__cache:
            self.__cache[forge_url] = cleaned_interfaces
        else:
            interfaces: [str] = self.__cache[forge_url]
            for ci in cleaned_interfaces:
                if ci not in interfaces:
                    interfaces.append(ci)
            self.__cache[forge_url] = interfaces


class NameService:
    def __init__(self, forge_url: str):
        self.ns = urlparse(clean_url(settings.SYSTEM.northstar))
        self.forge_url = clean_url(forge_url)
        self._register()
        self.cache = NSCache()

    def _get_url(self, path: str) -> str:
        prefix = "/api/v1/"
        if path.startswith("/"):
            path = path[1:]

        path = f"{prefix}{path}"
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

    def query(self, forge_url: str) -> [str]:
        """Get interfaces that service a forge"""
        url = "forge/interfaces"
        url = self._get_url(url)

        cached = self.cache.search(forge_url)
        if cached is None:
            payload = {"forge_url": forge_url}
            resp = requests.post(url, json=payload)
            interfaces = resp.json()
            self.cache.add(forge_url, interfaces)
            return interfaces
        return cached
