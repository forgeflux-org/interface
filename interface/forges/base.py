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

from .notifications import NotificationResp
from .payload import RepositoryInfo, CreatePullrequest, CreateIssue
from .utils import clean_url


class Forge:
    def __init__(self, base_url: str, admin_user: str, admin_email):
        self.base_url = urlparse(clean_url(base_url))
        if all([self.base_url.scheme != "http", self.base_url.scheme != "https"]):
            print(self.base_url.scheme)
            raise Exception("scheme should be either http or https")
        self.admin = InterfaceAdmin(admin_email, admin_user)

    def _lock_repo(self, local_url):
        conn = get_db()
        cur = conn.cursor()

        res = cur.execute(
            "SELECT ID, is_locked from interface_repositories WHERE html_url = ?",
            (local_url,),
        ).fetch_one()

        now = rfc3339.rfc3339(datetime.datetime.now())
        if len(res) == 0:
            cur.execute(
                "INSERT OR IGNORE INTO interface_repositories (html_url, is_locked) VALUES (?);",
                (local_url, now),
            )
            conn.commit()
            return True
        else:
            if res[0]["is_locked"] is None:
                cur.execute(
                    "UPDATE interface_repositories is_locked = ? WHERE html_url = ?;",
                    (now, local_url),
                )
                conn.commit()
                cur.execute(
                    "UPDATE interface_repositories is_locked = ? WHERE html_url = ?;",
                    (None, local_url),
                )
                conn.commit()
                return True
            return False

    def _unlock_repo(self, local_url):
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "UPDATE interface_repositories is_locked = ? WHERE html_url = ?;",
            (None, local_url),
        )
        conn.commit()

    def git_clone(self, upstream_url: str, local_name: str):
        local_url = self.get_local_html_url(local_name)
        local_push_url = self.get_local_push_url(local_name)

        if self._lock_repo(local_url):
            repo = Repo(local_settings.BASE_DIR, local_push_url, upstream_url)
            default_branch = repo.default_branch()
            repo.push_local(default_branch)
            self._unlock_repo(local_url)
>>>>>>> a284569 (fix typos)

    def get_fetch_remote(self, url: str) -> str:
        """Get fetch remote for possible forge URL"""
        parsed = urlparse(url)
        if all([parsed.scheme != "http", parsed.scheme != "https"]):
            raise Exception("scheme should be wither http or https")
        if parsed.netloc != self.host.netloc:
            raise Exception("Unsupported forge")
        repo = parsed.path.split("/")[1:3]
        path = format("/%s/%s" % (repo[0], repo[1]))
        return urlunparse((self.host.scheme, self.host.netloc, path, "", "", ""))

    def get_owner_repo_from_url(self, url: str) -> (str, str):
        """Get (owner, repo) from repository URL"""
        url = self.get_fetch_remote(url)
        parsed = urlparse(url)
        details = parsed.path.split("/")[1:3]
        (owner, repo) = (details[0], details[1])
        return (owner, repo)

    def get_local_html_url(self, repo: str) -> str:
        """get local repository's HTML url"""
        raise NotImplementedError

    def get_local_push_url(self, repo: str) -> str:
        raise NotImplementedError

    """ Forge characteristics. All interfaces must implement this class"""

    def get_issues(self, owner: str, repo: str, *args, **kwargs):
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

    def comment_on_issue(self, owner: str, repo: str, issue_url: str, body: str):
        """Add comment on an existing issue"""
        raise NotImplementedError
