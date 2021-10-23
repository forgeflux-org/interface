# Bridges software forges to create a distributed software development environment
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
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from urllib.parse import urlparse, urlunparse
import requests

from libgit import Repo, InterfaceAdmin, Patch

BASE_DIR = "/tmp/"

def get_patch(url: str) -> str:
    """ Get patch from pull request"""
    if url.endswith('/'):
        url = url[0:-1] + ".patch"
    else:
        url += ".patch"
    resp = requests.get(url)
    if resp.status_code == 200:
        return resp.text

def clean_url(url: str):
    """Remove paths and tracking elements from URL"""
    parsed = urlparse(url)
    cleaned = urlunparse((parsed.scheme, parsed.netloc, "", "", "", ""))
    return cleaned

def get_branch_name(pull_request_url: str) -> str:
    """ Get branch name from pull request URL """
    parsed = urlparse(pull_request_url)
    return format("%s%s" % (parsed.netloc, parsed.path.replace("/", "-")))


class Forge:
    def __init__(self, base_url: str, admin_user: str, admin_email):
        self.base_url = urlparse(clean_url(base_url))
        if all([self.base_url.scheme != "http", self.base_url.scheme != "https"]):
            print(self.base_url.scheme)
            raise Exception("scheme should be wither http or https")
        self.admin = InterfaceAdmin(admin_email, admin_user)

    def get_fetch_remote(self, url: str) -> str:
        """Get fetch remote for possible forge URL"""
        parsed = urlparse(url)
        if all([parsed.scheme != "http", parsed.scheme != "https"]):
            raise Exception("scheme should be wither http or https")

        if parsed.netloc != self.base_url.netloc:
            raise Exception("Unsupported forge")

        repo = parsed.path.split('/')[1:3]
        path = format("/%s/%s" % (repo[0], repo[1]))
        return urlunparse((self.base_url.scheme, self.base_url.netloc, path, "", "", ""))

    def process_patch(self, patch: Patch, local_url: str, upstream_url, branch_name) -> str:
        repo = Repo(BASE_DIR, local_url, upstream_url)
        repo.fetch_upstream()
        repo.apply_patch(patch, self.admin, branch_name)
