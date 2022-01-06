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
from dateutil.parser import parse as date_parse

from flask import current_app
from dynaconf import settings

from interface.forges.notifications import (
    CreatePrEvent,
    CreatePrMessage,
    NotificationResolver,
    RunNotification,
    Notification,
    PrEvent,
    IssueEvent,
)
from interface.forges.gitea.utils import get_issue_index
from interface.utils import clean_url, trim_url
from interface.db import get_db, DBRepo, DBUser, DBIssue, DBInterfaces

from interface.forges.gitea.responses import (
    GiteaInternalTracker,
    GiteaNotificationSubject,
    GiteaOwner,
    GiteaRepoPermissions,
    GiteaRepo,
    GiteaIssue,
    GiteaComment,
)

ISSUE = "Issue"
PULL = "Pull"
COMMIT = "commit"
REPOSITORY = "repository"


class GiteaNotification(NotificationResolver):
    id: int
    repository: GiteaRepo
    subject: GiteaNotificationSubject
    unread: bool
    pinned: bool
    updated_at: str
    url: str

    def __process_issue(self):
        if self.subject.type != ISSUE:
            raise TypeError("this method is to be called only on issues")

        issue_index = get_issue_index(self.subject.url)
        issue = DBIssue.load(
            repository=self.repository.to_db_repo(), repo_scope_id=issue_index
        )

        if issue is None or issue.is_closed:
            issue_from_gitea = GiteaIssue.get_issue(self.subject.url)
            issue_from_gitea.to_db_issue().save()
            if issue_from_gitea.comments > 0:
                comments = GiteaComment.from_issue(issue_from_gitea)

    #        if from_db is None:

    def resolve(self):
        if self.subject.type == REPOSITORY:
            return None

        repo = DBRepo.load(self.repository.name, self.repository.owner.username)
        if repo is None:
            repo = DBRepo(self.repository.name, self.repository.owner.username)

        if self.subject.type == ISSUE:

            #            DBIssue.load(

            with current_app().app_context():
                db = get_db()

            cur = conn.cursor()
            last_run = date_parse("2021-11-10T17:06:02+05:30")
            cur.execute(
                """
                INSERT OR IGNORE INTO interface_jobs_run
                    (this_interface_url, last_run) VALUES (?, ?);
                """,
                (settings.SERVER.url, str(last_run)),
            )
            conn.commit()

            comments = []


# class GiteaNotificationResolver(NotificationResolver):
#    @staticmethod
#    def resolve_notification(notification: Notification) -> RunNotification:
#        """Convert Notification into runnable unit of work"""
#        if notification.type == PULL:
#            return PrEvent(notification)
#        if notification.type == ISSUE:
#            return IssueEvent(notification)
#
#        raise Exception(
#            f"Unknown notification type {notification.type} {notification.web_url}"
#        )
#
#    @staticmethod
#    def get_event(notification: Notification) -> RunNotification:
#        """Convert Notification into runnable unit of work"""
#        subject = n["subject"]
#        notification_type = subject["type"]
#
#        # 2021-12-25: REPOSITORY type notification is only sent out when a
#        # repository transfer request is made and the recipient has to confirm
#        # it --- irrelevant for us
#        if notification_type == REPOSITORY:
#            return None
#
#        with current_app().app_context():
#            db = get_db()
#
#        last_read = n["updated_at"]
#        rn = Notification(
#            updated_at=last_read,
#            type=notification_type,
#            title=subject["title"],
#            state=subject["state"],
#            id=n["id"],
#            repo_url=n["repository"]["html_url"],
#        )
#
#        if notification_type == PULL:
#            rn.pr_url = requests.request("GET", subject["url"]).json()["html_url"]
#
#            rn.upstream = n["repository"]["description"]
#            print(n["repository"]["description"])
#
#        elif notification_type == ISSUE:
#            comment_url = subject["latest_comment_url"]
#            print(comment_url)
#            if len(comment_url) != 0:
#                resp = requests.request("GET", comment_url)
#                comment = resp.json()
#
#                url = ""
#                pr_url = comment["pull_request_url"]
#                if len(comment["pull_request_url"]) == 0:
#                    url = comment["issue_url"]
#                else:
#                    url = pr_url
#
#                c = Comment(
#                    updated_at=comment["updated_at"],
#                    author=comment["user"]["login"],
#                    id=comment["id"],
#                    body=comment["body"],
#                    url=url,
#                )
#
#                rn.comment = c
#        return rn
