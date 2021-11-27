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
import datetime

from .payload import Payload

ISSUE = "Issue"
PULL = "Pull"
COMMIT = "commit"
REPOSITORY = "repository"


class Comment(Payload):
    """Data structure that represents a comment"""

    def __init__(self):
        mandatory = ["body", "author", "updated_at", "url"]
        super().__init__(mandatory)

    def set_updated_at(self, date):
        """set comment last update time"""
        self.payload["updated_at"] = date

    def set_body(self, body):
        """set comment body"""
        self.payload["body"] = body

    def set_author(self, author):
        """set comment author"""
        self.payload["author"] = author

    def set_url(self, url):
        """set url of comment"""
        self.payload["url"] = url


class Notification(Payload):
    """Data structure that represents a notification"""

    def __init__(self):
        mandatory = ["type", "id", "state", "updated_at", "title"]
        super().__init__(mandatory)

    def get_id(self) -> str:
        """get notification id"""
        return self.payload["id"]

    def get_updated_at(self) -> str:
        """get notification update time"""
        return self.payload["updated_at"]

    def get_upstream(self) -> str:
        """get upstream repository URL"""
        return self.payload["upstream"]

    def get_pr_url(self) -> str:
        """get pr url"""
        return self.payload["pr_url"]

    def get_type(self) -> str:
        """get notification type"""
        return self.payload["type"]

    def get_state(self) -> str:
        """get notification state"""
        return self.payload["state"]

    def get_comment(self) -> str:
        """get comment"""
        return self.payload["status"]

    def get_repo_url(self) -> str:
        """get repository URL update time"""
        return self.payload["repo_url"]

    def get_title(self) -> str:
        """get issue title"""
        return self.payload["title"]

    def set_id(self, id_: str) -> str:
        """set notification ID"""
        self.payload["id"] = id_

    def set_updated_at(self, date):
        """set notification update time"""
        self.payload["updated_at"] = date

    def set_upstream(self, upstream):
        """set upstream repository URL"""
        print("settings upstream", upstream)
        self.payload["upstream"] = upstream

    def set_pr_url(self, url):
        """set pr url"""
        self.payload["pr_url"] = url

    def set_type(self, notification_type):
        """set notification type"""
        self.payload["type"] = notification_type

    def set_state(self, state):
        """set notification state"""
        self.payload["state"] = state

    def set_comment(self, comment: Comment):
        """set comment"""
        self.payload["status"] = comment.get_payload()

    def set_repo_url(self, repo_url: str):
        """set repository URL update time"""
        self.payload["repo_url"] = repo_url

    def set_title(self, title):
        """set issue title"""
        self.payload["title"] = title


class NotificationResp:
    """Notification response helper type"""

    def __init__(self, notifications: [Notification], last_read: datetime.datetime):
        self.notifications = notifications
        self.last_read = last_read

    def get_payload(self):
        """get flattened data"""
        notifications = []
        for n in self.notifications:
            notifications.append(n.get_payload())

        return notifications
