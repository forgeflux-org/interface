"""
Payload data structures
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
from dataclasses import dataclass

from interface.db import (
    DBUser,
    DBInterfaces,
)


@dataclass
class RepositoryInfo:
    """Describes a repository"""

    name: str
    owner: str
    description: str = None


@dataclass
class Author:
    """Information of the author of a comment, issue or pull request"""

    fqdn_username: str
    name: str
    profile_url: str

    def to_db_user(self, public_key: str) -> DBUser:
        """Convert Author into DBUser"""
        if "@" not in self.fqdn_username:
            raise ValueError(
                "Username has to be FQDN of form: usrename@forge.example.com"
            )

        return DBUser(
            name=self.name,
            user_id=self.fqdn_username,
            signed_by=DBInterfaces.load_from_pk(public_key),
            profile_url=self.profile_url,
        )


@dataclass
class CreateIssue:
    """Create new issue payload"""

    title: str
    body: str
    author: Author
    repository: RepositoryInfo
    html_url: str
    due_date: str = None
    closed: bool = False


@dataclass
class CreatePullrequest:
    """
    Data structure that contains params to create a pull request.
    See https://docs.github.com/en/rest/reference/pulls
    """

    author: Author
    repository: RepositoryInfo
    title: str
    html_url: str
    """
    From GitHub Docs:

    The name of the branch you want the changes pulled into.
    This should be an existing branch on the current repository.
    You cannot submit a pull request to one repository that requests a merge to
    a base of another repository.
    """
    head: str
    """
    From GitHub Docs:
    The name of the branch you want the changes pulled into.
    This should be an existing branch on the current repository.
    You cannot submit a pull request to one repository that requests a merge to
    a base of another repository.
    """
    base: str
    body: str = None


@dataclass
class CommentOnIssue:
    """Comment on an Issue or a PR"""

    body: str
    author: Author
    repository: RepositoryInfo
    issue_id: int
    html_url: str
