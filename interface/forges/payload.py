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
from datetime import datetime
from enum import Enum, unique

from interface.db import DBUser, DBInterfaces, DBRepo, get_db_interface
from interface.utils import clean_url, trim_url


@unique
class MessageType(str, Enum):
    CREATE_PR = "F_CREATE_PR"
    CREATE_ISSUE = "F_CREATE_ISSUE"
    COMMENT_ON_ISSUE = "F_COMMENT_ON_ISSUE"

    def human_readable(self) -> str:
        if self.name == self.CREATE_PR.name:
            return "issue"
        if self.name == self.CREATE_ISSUE.name:
            return "issue"
        if self.name == self.COMMENT_ON_ISSUE.name:
            return "issue"


@dataclass
class RepositoryInfo:
    """Describes a repository"""

    name: str
    owner: str
    description: str = None

    def to_db_repo(self) -> DBRepo:
        return DBRepo(name=self.name, owner=self.owner)


@dataclass
class Author:
    """Information of the author of a comment, issue or pull request"""

    fqdn_username: str
    name: str
    profile_url: str


# TODO get rid of Author. ForgeUser is supposed to be used only to represent
# local users
@dataclass
class ForgeUser:
    name: str
    user_id: str
    profile_url: str

    def to_db_user(self) -> DBUser:
        return DBUser(
            name=self.name,
            user_id=self.user_id,
            profile_url=self.profile_url,
            signed_by=get_db_interface(),
        )


EPOCH = datetime.utcfromtimestamp(0)


@dataclass
class MetaData:
    """
    Describes basic metadata of a forgeflux message:
    """

    # time since epoch in milliseconds
    html_url: str
    author: Author
    interface_url: str
    date: int = int((datetime.now() - EPOCH).total_seconds() * 1000)

    def get_date(self) -> datetime:
        """Get date in human readable form"""
        return datetime.utcfromtimestamp(self.date / 1000)

    def get_header(self, msg_type: MessageType) -> str:
        """
        When messages(issues, comments and PRs) are federated over, it's
        possible that the Interface might not render them properly or it may
        not be possible to present the received information as the forge may
        not support that message type(reactions, etc).

        In these cases, including tracable information within all federated message
        in the form of a header will enable the user overcome these deficiences.

        Additionally, there can be multiple interfaces running on the same
        forge, which makes it difficult to trace which interface the message
        came from. So including source information in the header can help with
        administrative tasks.
        """
        return f"""
        <details>
        <summary>

        This {msg_type.human_readable()} is from {trim_url(clean_url(self.html_url))}, see [source]({self.html_url})

        </summary>
        Federation metadata, please ignore

        user: [self.author.fqdn_username](self.author.profile_url):
        date: {str(self.get_date)}
        federated_by: {self.interface_url}

        Intrigued? [Click here to learn more](https://forgeflux.org)
        </details>

        [self.author.fqdn_username](self.author.profile_url):
        """


@dataclass
class Message:
    """Basic message interface of ForgeFlux"""

    meta: MetaData


@dataclass
class CommentOnIssue(Message):
    """Comment on an Issue or a PR"""

    body: str
    repository: RepositoryInfo
    issue_url: str
    meta: MetaData
    msg_type: MessageType = MessageType.COMMENT_ON_ISSUE

    def comment(self) -> str:
        """Rendered comment body"""
        return f"""
        {self.meta.get_header(self.msg_type)}\n\n

        {self.body}
        """


@dataclass
class CreateIssue(Message):
    """Create new issue payload"""

    title: str
    body: str
    repository: RepositoryInfo
    meta: MetaData
    due_date: str = None
    closed: bool = False
    msg_type: MessageType = MessageType.CREATE_ISSUE
    """
    It's possible that there might be comments on the sender forge on a issue
    that's yet to be created on the receiver forge. This field is to be used to
    attach child comments in such cases.
    """
    comments: [CommentOnIssue] = None

    def description(self) -> str:
        """rendered description"""
        return f"""
        {self.meta.get_header(self.msg_type)}\n\n

        {self.body}
        """


@dataclass
class CreatePullrequest(Message):
    """
    Data structure that contains params to create a pull request.
    See https://docs.github.com/en/rest/reference/pulls
    """

    repository: RepositoryInfo
    title: str
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
    meta: MetaData
    body: str = None
    msg_type: MessageType = MessageType.CREATE_PR
    """
    It's possible that there might be comments on the sender forge on a PR
    that's yet to be created on the receiver forge. This field is to be used to
    attach child comments in such cases.
    """
    comments: [CommentOnIssue] = None

    def description(self) -> str:
        """rendered description"""
        return f"""
        {self.meta.get_header(self.msg_type)}\n\n

        {self.body}
        """
