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
from dataclasses import asdict

from interface.meta import VERSIONS
from interface.auth import KeyPair, PublicKey


INTERFACE_VERSION_URL = "https://interfac9.example.com/_ff/interface/versions"
INTERFACE_KEY_URL = "https://interfac9.example.com/_ff/interface/key"


def mock_version(requests_mock):
    resp = {"versions": VERSIONS}
    requests_mock.get(INTERFACE_VERSION_URL, json=resp)
    print(f"Registered version route {INTERFACE_VERSION_URL}")


KEY = KeyPair()
public_key = PublicKey(key=KEY.to_base64_public())


def mock_key(requests_mock):
    resp = asdict(public_key)
    requests_mock.get(INTERFACE_KEY_URL, json=resp)
    print(f"Registered version route {INTERFACE_KEY_URL}")
