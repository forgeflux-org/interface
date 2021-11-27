"""
A job runner that receives events(notifications) and runs relevant jobs on them
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
from dataclasses import dataclass
import requests
from dynaconf import settings

from interface.git import get_forge
from interface.db import get_db
from interface.forges.utils import get_patch, get_branch_name
from interface.forges.notifications import Notification, PULL, ISSUE


@dataclass
class RunNotification:
    """Process notification"""

    notification: Notification

    def __post_init__(self):
        if self._check_mandatory():
            raise Exception("mandatory fields not present")

    def _check_mandatory(self) -> bool:
        """get mandatory fields"""
        raise NotImplementedError


def resolve_notification(n: Notification) -> RunNotification:
    """Convert Notification into runnable unit of work"""
    git = get_forge()
    (owner, _repo) = git.forge.get_owner_repo_from_url(n.repo_url)
    if n.type == PULL:
        if owner == settings.GITEA.username:
            return PrEvent(n)
        raise Exception("Unknown PULL notification")
    elif n.type == ISSUE:
        return IssueEvent(n)


class PrEvent(RunNotification):
    """PR type Notification"""

    def _check_mandatory(self) -> bool:
        return any(
            [
                self.notification.pr_url is None,
                self.notification.upstream is None,
            ]
        )

    def run(self):
        git = get_forge()
        (owner, _repo) = git.forge.get_owner_repo_from_url(self.notification.repo_url)
        if all([self.notification.type == PULL, owner == settings.GITEA.username]):
            patch = get_patch(self.notification.pr_url)
            local = self.notification.repo_url
            _upstream = self.notification.upstream
            patch = git.process_patch(
                patch, local, get_branch_name(self.notification.pr_url)
            )
            print(patch)


class IssueEvent(RunNotification):
    """Issue type notificatin"""

    def _check_mandatory(self) -> bool:
        return any(
            [
                self.notification.comment is None,
                self.notification.pr_url is None,
            ]
        )

    def run(self):
        git = get_forge()
        (_owner, repo) = git.forge.get_owner_repo_from_url(self.notification.repo_url)
        if self.notification.type == ISSUE:
            repo_url = self.notification.repo_url
            conn = get_db()
            cur = conn.cursor()
            repo_urls = cur.execute(
                """
                SELECT url FROM interface_interfaces WHERE URL = (
                    SELECT 
                        interface_id 
                    FROM 
                        interface_event_subscriptsions 
                    WHERE 
                        repository_id = (SELECT id WHERE url = ?)
                    );
                """,
                (repo_url,),
            ).fetchall()
            for r in repo_urls:
                requests
                r.append(r[0])
            raise NotImplementedError
