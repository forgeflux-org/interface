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
from urllib.parse import urlparse, urlunparse
from dataclasses import asdict

from flask import g
import requests

from interface.forges.base import Forge
from interface.forges.notifications import Notification
from interface.db import get_db

GET_REPOSITORY = "/fetch"
GET_REPOSITORY_INFO = "/info"
FORK_LOCAL = "/fork/local"
FORK_FOREIGN = "/fork/foreign"
SUBSCRIBE = "/subscribe"
EVENTS = "/events"
COMMENT_ON_ISSUE = "/issues/comment"
CREATE_ISSUE = "/issue/create"
CREATE_PULL_REQUEST = "/pull/create"


class ForgeClient:
    def __init__(self, forge: Forge):
        self.forge = forge
        self.interfaces = [
            {
                "forge": "https://github.com",
                "interface": "https://github-interface.shuttlecraft.io",
            },
            {
                "forge": "https://git.batsense.net",
                "interface": "https://gitea-interface.shuttlecraft.io",
            },
        ]

    def _construct_url(self, interface_url: str, path: str) -> str:
        """Get interface API routes"""
        prefix = "/api/v1/"
        if path.startswith("/"):
            path = path[1:]

        path = format("%s%s" % (prefix, path))
        parsed = urlparse(interface_url)
        url = urlunparse((parsed.scheme, parsed.netloc, path, "", "", ""))
        return url

    def find_interface(self, url: str):
        parsed = urlparse(url)
        for interface in self.interfaces:
            if urlparse(interface["forge"]).netloc == parsed.netloc:
                return interface["interface"]

    def get_repository(self, repo_url: str):
        """Get foreign repository url"""
        interface_url = self.forge.find_interface(repo_url)
        interface_api_url = self._construct_url(
            interface_url=interface_url, path=GET_REPOSITORY
        )

        payload = {"url": repo_url}
        response = requests.request("POST", interface_api_url, json=payload)
        data = response.json()
        return data["repository_url"]

    def get_repository_info(self, repo_url: str):
        """Get foreign repository url"""
        interface_url = self.forge.find_interface(repo_url)
        interface_api_url = self._construct_url(
            interface_url=interface_url, path=GET_REPOSITORY_INFO
        )

        payload = {"repository_url": repo_url}
        response = requests.request("POST", interface_api_url, json=payload)
        data = response.json()
        return data

    def send_notification(self, notification: Notification, interface_url: str):
        """send notification to subscribed interface"""
        interface_api_url = self._construct_url(
            interface_url=interface_url, path=EVENTS
        )
        _response = requests.request(
            "POST", interface_api_url, json=asdict(notification)
        )


#    def send_contributions(self, patch, upstream, pr_url, message):
#        interface_url = self.forge.find_interface(upstream)
#        interface_api_url = self._construct_url(interface_url=interface_url, path=GET_REPOSITORY)
#        payload  = {
#           "repository_url": upstream,
#            "pr_url": pr_url
#            "message": string
#            "head": "master"
#            "base" string
#            "title": string
#            "patch": string
#            "author_name": string
#            "author_email": string
#


def get_client() -> ForgeClient:
    if "client" not in g:
        g.client = ForgeClient(get_forge())
    return g.client
