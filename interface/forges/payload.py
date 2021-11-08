"""
Payload data structures
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


class Payload:
    """Payload base class. self.mandatory should be defined"""

    def __init__(self, mandatory: list[str]):
        self.payload = {}
        self.mandatory = []

    def get_payload(self):
        """get payload"""
        for f in self.mandatory:
            if self.payload[f] is None:
                raise Exception("%s can't be empty" % f)
        return self.payload


class RepositoryInfo(Payload):
    """Describes a repository"""

    def __init__(self):
        mandatory = ["name", "owner_name"]
        super().__init__(mandatory)

    def set_name(self, name):
        """Set name of repository"""
        self.payload["name"] = name

    def set_owner_name(self, name):
        """Set owner name of repository"""
        self.payload["owner_name"] = name

    def set_description(self, description):
        """Is this a template repository"""
        self.payload["description"] = description


class CreateIssue(Payload):
    """Create new issue payload"""

    def __init__(self):
        mandatory = ["title"]
        super().__init__(mandatory)

    def set_title(self, title):
        """set issue title"""
        self.payload["title"] = title

    def set_body(self, body):
        """set issue body"""
        self.payload["body"] = body

    def set_due_date(self, due_date):
        """set issue due date"""
        self.payload["due_date"] = due_date

    def set_closed(self, closed: bool):
        """set issue open status"""
        self.payload["closed"] = closed


class CreatePullrequest(Payload):
    """
    Data structure that contains params to create a pull request.
    See https://docs.github.com/en/rest/reference/pulls
    """

    def __init__(self):
        mandatory = ["owner", "message", "repo", "head", "base", "title"]
        super().__init__(mandatory)

    def set_owner(self, name):
        """Set owner name of repository"""
        self.payload["owner"] = name

    def set_repo(self, repo):
        """Set owner name of repository"""
        self.payload["repo"] = repo

    def set_head(self, head):
        """
        From GitHub Docs:

        The name of the branch you want the changes pulled into.
        This should be an existing branch on the current repository.
        You cannot submit a pull request to one repository that requests a merge to
        a base of another repository.
        """
        self.payload["head"] = head

    def set_base(self, base):
        """
        From GitHub Docs:
        The name of the branch you want the changes pulled into.
        This should be an existing branch on the current repository.
        You cannot submit a pull request to one repository that requests a merge to
        a base of another repository.
        """
        self.payload["base"] = base

    def set_title(self, title):
        """set title of the PR"""
        self.payload["title"] = title

    def set_message(self, message):
        """set message of the PR"""
        self.payload["message"] = message

    def set_body(self, body):
        """set title of the PR message"""
        self.payload["body"] = body
