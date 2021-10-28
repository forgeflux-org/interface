"""
Helper class to interact with git repositories
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
from urllib.parse import urlparse
import rfc3339

from libgit import InterfaceAdmin, Repo, Patch

from interface.db import get_db
from interface import local_settings

# from interface.forges.notifications import Notification, NotificationResp, Comment
# from interface.forges.payload import RepositoryInfo, CreatePullrequest, CreateIssue
from interface.forges.utils import get_branch_name
from interface.forges.base import Forge
from interface.forges.gitea import Gitea


class Git:
    def __init__(self, forge: Forge, admin_user: str, admin_email):
        self.forge = forge
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
        local_url = self.forge.get_local_html_url(local_name)
        local_push_url = self.forge.get_local_push_url(local_name)

        if self._lock_repo(local_url):
            repo = Repo(local_settings.BASE_DIR, local_push_url, upstream_url)
            default_branch = repo.default_branch()
            repo.push_local(default_branch)
            self._unlock_repo(local_url)

    def apply_patch(self, patch: Patch, repository_url: str, pr_url: str) -> str:
        """apply patch"""
        (_, repo) = self.forge.get_owner_repo_from_url(repository_url)
        local_url = self.forge.get_local_html_url(repo)
        local_push_url = self.forge.get_local_push_url(repo)
        branch = get_branch_name(pr_url)
        if self._lock_repo(local_url):
            repo = Repo(local_settings.BASE_DIR, local_push_url, repository_url)
            repo.apply_patch(patch, self.admin, branch)
            repo.push_loca(branch)
            self._unlock_repo(local_url)
        return branch

    def process_patch(
        self, patch: str, local_url: str, upstream_url, branch_name
    ) -> str:
        """process patch"""
        repo = Repo(local_settings.BASE_DIR, local_url, upstream_url)
        repo.fetch_upstream()
        patch = repo.process_patch(patch, branch_name)
        return patch


def get_forge():
    forge = Gitea()
    git = Git(forge, local_settings.GITEA_USERNAME, local_settings.ADMIN_EMAIL)
    return git
