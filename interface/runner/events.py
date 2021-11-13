"""
A job runner that receives events(notifications) and runs revelant jobs on them
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
import requests

from interface import local_settings
from interface.git import get_forge
from interface.db import get_db
from interface.forges.utils import get_patch, get_branch_name
from interface.forges.notifications import Notification, PULL, ISSUE


class RunNoification:
    """Process notification"""

    def __init__(self, n: Notification):
        self.notification = n

    def run(self):
        """processing rules"""
        raise NotImplementedError

    @staticmethod
    def get_mandatory() -> [str]:
        """get mandatory fields"""
        raise NotImplementedError

    def check_mandatory(self, event: RunNoification) -> bool:
        """check for mandatory fields' presence"""
        for f in event.get_mandatory():
            if f not in self.notification.payload:
                raise Exception("%s can't be empty" % f)
        return True

    @staticmethod
    def resolve(n: Notification) -> RunNoification:
        git = get_forge()
        (owner, _repo) = git.forge.get_owner_repo_from_url(n.get_repo_url())
        if all([n.get_type() == PULL, owner == local_settings.ADMIN_USER]):
            if n.check_mandatory(PrEvent):
                return PrEvent(n)
        elif n.get_type() == ISSUE:
            if n.check_mandatory(IssueEvent):
                return PrEvent(n)


class PrEvent(RunNoification):
    """PR type Notification"""

    @staticmethod
    def get_mandatory():
        return ["pr_url", "upstream", "repo_url"]

    def run(self):
        git = get_forge()
        (owner, _repo) = git.forge.get_owner_repo_from_url(
            self.notification.get_repo_url()
        )
        if all(
            [self.notification.get_type() == PULL, owner == local_settings.ADMIN_USER]
        ):
            patch = get_patch(self.notification.get_pr_url())
            local = self.notification.notification.get_repo_url()
            _upstream = self.notification.get_upstream()
            patch = git.process_patch(
                patch, local, get_branch_name(self.notification.get_pr_url())
            )
            print(patch)


class IssueEvent(RunNoification):
    """Issue type notificatin"""

    @staticmethod
    def get_mandatory():
        return ["pr_url", "repo_url"]

    def run(self):
        git = get_forge()
        (_owner, repo) = git.forge.get_owner_repo_from_url(
            self.notification.get_repo_url()
        )
        if self.notification.get_type() == ISSUE:
            repo_url = self.notification.get_repo_url()
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
