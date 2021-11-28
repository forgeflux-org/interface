""" Utilities for Gitea functionality"""
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
import json
from pathlib import Path

from requests_mock import request
from dynaconf import settings

from interface.client import GET_REPOSITORY_INFO
from interface.utils import trim_url

GITEA_HOST = settings.GITEA.host

REPOSITORY_URL = ""
REPOSITORY_NAME = ""
REPOSITORY_OWNER = ""
REPOSITORY_DESCRIPTION = ""
data = {}

path = Path(__file__).parent / "get_repository.json"
with path.open() as f:
    data = json.load(f)
    REPOSITORY_URL = trim_url(data["html_url"])
    REPOSITORY_NAME = data["name"]
    REPOSITORY_OWNER = data["owner"]["login"]
    REPOSITORY_DESCRIPTION = data["description"]


def register_get_repository(requests_mock):
    path = f"{GITEA_HOST}/api/v1/repos/{REPOSITORY_OWNER}/{REPOSITORY_NAME}"
    requests_mock.get(
        path,
        json=data,
    )
    print(f"registered get repository: {path}")


def register_subscribe(requests_mock):
    path = (
        f"{GITEA_HOST}/api/v1/repos/{REPOSITORY_OWNER}/{REPOSITORY_NAME}/subscription"
    )
    requests_mock.put(
        path,
        json={},
    )
    print(f"registered repository subscription: {path}")


def register_gitea(requests_mock):
    register_get_repository(requests_mock)
    register_subscribe(requests_mock)
