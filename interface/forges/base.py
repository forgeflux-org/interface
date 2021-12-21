"""
Forge behavior base class
"""
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

import datetime
from urllib.parse import urlparse, urlunparse

from interface.forges.notifications import NotificationResp, Notification
from interface.forges.payload import RepositoryInfo, CreatePullrequest, CreateIssue
from interface.forges.utils import clean_url
from interface.ns import NameService
from interface.error import Error


class Forge:
    def __init__(self, host):  # self, base_url: str, admin_user: str, admin_email):
        self.host = urlparse(clean_url(host))
        if all([self.host.scheme != "http", self.host.scheme != "https"]):
            print(self.host.scheme)
            raise Exception("scheme should be either http or https")
        self.ns = NameService(self.get_forge_url())

    def get_fetch_remote(self, url: str) -> str:
        """Get fetch remote for possible forge URL"""
        parsed = urlparse(url)
        if all([parsed.scheme != "http", parsed.scheme != "https"]):
            raise Exception("scheme should be either http or https")
        if parsed.netloc != self.host.netloc:
            raise Exception("Unsupported forge")
        repo = parsed.path.split("/")[1:3]
        path = format("/%s/%s" % (repo[0], repo[1]))
        return urlunparse((self.host.scheme, self.host.netloc, path, "", "", ""))

    def get_owner_repo_from_url(self, url: str) -> (str, str):
        """Get (owner, repo) from repository URL"""
        raise NotImplementedError

    def get_forge_url(self) -> str:
        """get URL of software for that this interface is servicing"""
        raise NotImplementedError

    def get_local_html_url(self, repo: str) -> str:
        """get local repository's HTML url"""
        raise NotImplementedError

    def get_local_push_url(self, repo: str) -> str:
        raise NotImplementedError

    """ Forge characteristics. All interfaces must implement this class"""

    def get_issues(
        self, owner: str, repo: str, since: datetime.datetime = None, *args, **kwargs
    ):
        """Get issues on a repository. Supports pagination via 'page' optional param"""
        raise NotImplementedError

    def create_issue(self, owner: str, repo: str, issue: CreateIssue) -> str:
        """Creates issue on a repository. reurns html url of the newly created issue"""
        raise NotImplementedError

    def get_repository(self, owner: str, repo: str) -> RepositoryInfo:
        """Get repository details"""
        raise NotImplementedError

    def create_repository(self, repo: str, description: str):
        """Create new repository"""
        raise NotImplementedError

    def subscribe(self, owner: str, repo: str):
        """subscribe to events in repository"""
        raise NotImplementedError

    def get_notifications(self, since: datetime.datetime) -> NotificationResp:
        """subscribe to events in repository"""
        raise NotImplementedError

    def create_pull_request(self, pr: CreatePullrequest) -> str:
        """
        create pull request
        return value is the URL(HTML page) of the newely created PR
        """
        raise NotImplementedError

    def fork(self, owner: str, repo: str):
        """Fork a repository"""
        raise NotImplementedError

    def close_pr(self, owner: str, repo: str):
        """Fork a repository"""
        raise NotImplementedError

    def get_notification(self, id_: str) -> Notification:
        """Get notification by Id"""
        raise NotImplementedError

    def comment_on_issue(self, owner: str, repo: str, issue_url: str, body: str):
        """Add comment on an existing issue"""
        raise NotImplementedError


F_D_REPOSITORY_NOT_FOUND = Error(
    errcode="F_D_REPOSITORY_NOT_FOUND",
    error="Repository not found",
    status=404,
)

F_D_FORGE_FORBIDDEN_OPERATION = Error(
    errcode="F_D_FORGE_FORBIDDEN_OPERATION",
    error="Forge reports operation is forbidden",
    status=403,
)

F_D_REPOSITORY_EXISTS = Error(
    errcode="F_D_REPOSITORY_EXISTS",
    error="Forge reports repository with the same name already exists",
    status=409,
)

F_D_INVALID_ISSUE_URL = Error(
    errcode="F_D_INVALID_ISSUE_URL",
    error="Issue URL provided is not valid",
    status=400,
)
