"""
Utility functions to work with forges
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
from urllib.parse import urlparse
import requests

from interface.utils import clean_url, trim_url


def get_patch(url: str) -> str:
    """Get patch from pull request"""
    url = f"{trim_url(url)}.patch"
    resp = requests.get(url)
    if resp.status_code == 200:
        return resp.text


def get_branch_name(pull_request_url: str) -> str:
    """Get branch name from pull request URL"""
    parsed = urlparse(pull_request_url)

    path = trim_url(parsed.path)
    if path.startswith("/"):
        path = path[1:]

    return format("%s-%s" % (parsed.netloc, path.replace("/", "-")))


def get_local_repository_from_foreign_repo(repo_url: str) -> str:
    if repo_url.endswith("/"):
        repo_url = repo_url[0:-1]
    return get_branch_name(repo_url)
