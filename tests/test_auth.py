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
import sqlite3

import pytest
from dynaconf import settings


from interface.auth import loadkey


def test_auth_key_load_successful(app, requests_mock):
    with app.app_context():
        loadkey()


def test_auth_key_load_failure(app, requests_mock):
    settings.PRIVATE_KEY = "foobar"
    with app.app_context():
        with pytest.raises(Exception):
            loadkey()
