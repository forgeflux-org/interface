"""
Helper class to interact with git repositories
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
import datetime
from urllib.parse import urlparse
import rfc3339
from flask import g

from libgit import InterfaceAdmin, Repo, Patch, System
from dynaconf import settings

from interface.db import get_db, get_git_system
from interface.forges.utils import get_branch_name
from interface.forges.base import Forge
from interface.forges.gitea import Gitea


class Git:
    def __init__(self, forge: Forge, admin_user: str, admin_email):
        self.forge = forge
        self.admin = InterfaceAdmin(admin_email, admin_user)

    def git_clone(self, upstream_url: str, local_name: str):
        local_push_url = self.forge.get_local_push_url(local_name)

        system = get_git_system()
        repo = system.init_repo(local_push_url, upstream_url)
        default_branch = repo.default_branch()
        system.push_local(repo, default_branch)

    def apply_patch(
        self, patch: Patch, upstream_repository_url: str, pr_url: str
    ) -> str:
        """apply patch"""
        branch = get_branch_name(pr_url)
        system = get_git_system()
        repo = system.with_upstream(upstream_repository_url)
        system.apply_patch(patch, self.admin, branch)
        system.push_loca(repo, branch)
        return branch

    def process_patch(self, patch: str, local_url: str, branch_name) -> str:
        """process patch"""
        system = get_git_system()
        repo = system.with_local(local_url)
        system.fetch_upstream(repo)
        patch = system.process_patch(repo, patch, branch_name)
        return patch

    def push_local(self, local_url: str, branch_name: str):
        system = get_git_system()
        repo = system.with_local(local_url)
        system.push_local(repo, branch_name)

    def with_upstream(self, upstream: str) -> Repo:
        system = get_git_system()
        repo = system.with_upstream(upstream)
        return repo

    def with_local(self, local: str) -> Repo:
        system = get_git_system()
        repo = system.with_local(local)
        return repo

    def fetch_upstream(self, repo: Repo):
        system = get_git_system()
        system.fetch_upstream(repo)

    def fork(self, owner: str, repo: str) -> str:
        """Fork a repository"""
        conn = get_db()
        cur = conn.cursor()
        fork_exists = cur.execute(
            """
            SELECT fork_repo_name FROM forks
            WHERE parent_owner = ? AND parent_repo_name = ?;
            """,
            (owner, repo),
        ).fetchone()
        if fork_exists:
            return fork_exists[0]
        fork_repo_name = self.forge.fork_inner(owner, repo)
        cur.execute(
            """
            INSERT INTO forks 
            (parent_owner, parent_repo_name, fork_repo_name)
            VALUES (?,?,?);
            """,
            (owner, repo, fork_repo_name),
        ).fetchone()
        return fork_repo_name


def get_forge() -> Git:
    if "git" not in g:
        forge = Gitea()
        g.git = Git(forge, settings.GITEA.username, settings.SYSTEM.admin_email)
    return g.git
