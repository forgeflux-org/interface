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
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from dataclasses import dataclass
from datetime import datetime
from dateutil.parser import parse as date_parse


from .conn import get_db
from .users import DBUser
from .repo import DBRepo
from .issues import DBIssue
from .interfaces import DBInterfaces


@dataclass
class DBComment:
    body: str
    html_url: str
    created: str
    updated: str
    comment_id: int  # comment ID
    is_native: bool
    user: DBUser
    belongs_to_issue: DBIssue
    signed_by: DBInterfaces

    __belongs_to_issue_id: int = None
    __signed_by_interface_id: int = None

    def save(self):
        """Save COmment to database"""
        self.user.save()
        self.signed_by.save()
        self.belongs_to_issue.save()

        conn = get_db()
        cur = conn.cursor()
        print(type(self.comment_id))
        print(type(self.updated))
        cur.execute(
            """
            INSERT OR IGNORE INTO gitea_issue_comments
                (

                    body, html_url, created, updated,
                    comment_id, is_native, user,
                    belongs_to_issue, signed_by

                )
                VALUES (
                    ?, ?, ?, ?,
                    ?, ?,
                    (SELECT ID from gitea_users WHERE user_id  = ?),
                    (SELECT ID from gitea_forge_issues WHERE html_url  = ?),
                    (SELECT ID from interfaces WHERE url  = ?)
                )
            """,
            (
                self.body,
                self.html_url,
                self.created,
                self.updated,
                self.comment_id,
                self.is_native,
                self.user.user_id,
                self.belongs_to_issue.html_url,
                self.signed_by.url,
            ),
        )
        conn.commit()

    @classmethod
    def load_issue_comments(cls, issue: DBIssue) -> "[DBComment]":
        """Load issue from database"""
        conn = get_db()
        cur = conn.cursor()
        data = cur.execute(
            """
         SELECT
             body,
             html_url,
             created,
             updated,
             comment_id,
             is_native,
             user,
             signed_by
         FROM
             gitea_issue_comments
         WHERE
             belongs_to_issue = ?
             """,
            (issue.id,),
        ).fetchall()
        if data is None:
            return None

        comments = []
        for comment in data:
            user = DBUser.load_with_db_id(comment[6])
            signed_by = DBInterfaces.load_from_database_id(comment[7])
            comments.append(
                cls(
                    body=comment[0],
                    html_url=comment[1],
                    created=comment[2],
                    updated=comment[3],
                    comment_id=comment[4],
                    is_native=comment[5],
                    user=user,
                    signed_by=signed_by,
                    belongs_to_issue=issue,
                )
            )
        return comments
