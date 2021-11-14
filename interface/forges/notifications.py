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
    upstream: str = None
    pr_url: str = None
    comment: Comment = None


@dataclass
class NotificationResp:
    """Notification response helper type"""

    last_read: datetime
    notifications: list[Notification]
