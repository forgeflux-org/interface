"""
Notifications payload
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
from datetime import datetime
from dataclasses import dataclass

ISSUE = "Issue"
PULL = "Pull"
COMMIT = "commit"
REPOSITORY = "repository"


@dataclass
class Comment:
    """Data structure that represents a comment"""

    body: str
    updated_at: str
    author: str
    id: str
    url: str


@dataclass
# pylint: disable=too-many-instance-attributes
class Notification:
    """Data structure that represents a notification"""

    type: str
    id: str
    state: str
    updated_at: str
    title: str
    repo_url: str
    web_url: str
    upstream: str = None
    pr_url: str = None
    comment: Comment = None


@dataclass
class NotificationResp:
    """Notification response helper type"""

    notifications: [Notification]
    last_read: datetime


class RunNotification:
    """Process notification"""

    notification: Notification

    def __post_init__(self):
        if self._check_mandatory():
            raise Exception("mandatory fields not present")

    def _check_mandatory(self) -> bool:
        """get mandatory fields"""
        raise NotImplementedError

    def process(self):
        """Process a notification"""
        raise NotImplementedError

    def propagate(self):
        """Propagate a notification"""
        raise NotImplementedError


class NotificationResolver:
    @staticmethod
    def resolve_notification(notification: Notification) -> RunNotification:
        """Convert Notification into runnable unit of work"""
        if notification.type == PULL:
            return PrEvent(notification)
        if notification.type == ISSUE:
            return IssueEvent(notification)

        raise Exception(f"Unknown notification type {notification.type}")


@dataclass
class CreatePrMessage:
    repository_url: str  # // of the target PR
    pr_url: str  # // pull request url
    message: str  # // message body
    head: str
    base: str
    title: str
    patch: str
    author_name: str
    author_email: str


@dataclass
class PrMessage:
    repository_url: str  # of the target PR
    # only the interface that created the PR or
    # the maintainers of upstream can close PR
    pr_url: str  # pull request url
    state: str  # open, close, merge, etc.
    message: str  # message body
    author_profile: str  # authors' webpage or forge profle page


class CreatePrEvent(RunNotification):
    """PR type Notification"""

    def _check_mandatory(self) -> bool:
        return any(
            [
                self.notification.pr_url is None,
                self.notification.upstream is None,
            ]
        )

    def process(self):
        # Example implementation:
        # Get PR description, title, author and patch content
        # and associated comments
        raise NotImplementedError

    def propagate(self) -> CreatePrMessage:
        raise NotImplementedError


class PrEvent(RunNotification):
    """PR type Notification"""

    def _check_mandatory(self) -> bool:
        return any(
            [
                self.notification.pr_url is None,
                self.notification.upstream is None,
            ]
        )

    def process(self):
        # Example implementation:
        # Get PR description, title, author and patch content
        # and associated comments
        raise NotImplementedError

    def propagate(self) -> PrMessage:
        raise NotImplementedError


class IssueEvent(RunNotification):
    """Issue type notificatin"""

    def _check_mandatory(self) -> bool:
        return any(
            [
                self.notification.comment is None,
                self.notification.pr_url is None,
            ]
        )

    def process(self):
        # Example implementation:
        # Get associated comments
        raise NotImplementedError

    def propagate(self):
        raise NotImplementedError
