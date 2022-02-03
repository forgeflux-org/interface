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
from .cache import RecordCount


@dataclass
class DBComment:
    body: str
    html_url: str
    created: int
    updated: int
    comment_id: int  # comment ID
    is_native: bool
    user: DBUser
    belongs_to_issue: DBIssue
    count = RecordCount("gitea_issue_comments")

    __belongs_to_issue_id: int = None

    def __set_sqlite_to_bools(self):
        """
        sqlite returns 0 for False and 1 for True and is not automatically typecast
        into bools. This method typecasts all bool values of this class.

        To be invoked by every load_* invocation
        """
        self.is_native = bool(self.is_native)

    def __update(self):
        """
        Update changes in database
        Only fields that can be mutated on the forge will be updated in the DB
        """
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE gitea_issue_comments
            SET
                body = ?,
                updated = ?
            WHERE
                comment_id = ?;
            """,
            (self.body, self.updated, self.comment_id),
        )
        conn.commit()

    def save(self):
        """Save COmment to database"""
        self.user.save()
        self.belongs_to_issue.save()

        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT OR IGNORE INTO gitea_issue_comments
                (

                    body, html_url, created, updated,
                    comment_id, is_native, user,
                    belongs_to_issue 

                )
                VALUES (
                    ?, ?, ?, ?,
                    ?, ?,
                    (SELECT ID from gitea_users WHERE user_id  = ?),
                    (SELECT ID from gitea_forge_issues WHERE html_url  = ?)
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
            ),
        )
        conn.commit()
        data = cur.execute(
            """
                    SELECT ID from gitea_issue_comments WHERE html_url = ?

                    """,
            (self.html_url,),
        ).fetchone()
        self.id = data[0]
        self.__update()

    @classmethod
    def load_from_comment_url(cls, comment_url: str) -> "DBComment":
        """Load comment based on comment URL from database"""
        conn = get_db()
        cur = conn.cursor()
        data = cur.execute(
            """
         SELECT
             body,
             belongs_to_issue,
             created,
             updated,
             comment_id,
             is_native,
             user
         FROM
             gitea_issue_comments
         WHERE
             html_url = ?
             """,
            (comment_url,),
        ).fetchone()
        if data is None:
            return None

        user = DBUser.load_with_db_id(data[6])
        belongs_to_issue = DBIssue.load_with_id(data[1])
        comment = cls(
            body=data[0],
            html_url=comment_url,
            created=data[2],
            updated=data[3],
            comment_id=data[4],
            is_native=data[5],
            user=user,
            belongs_to_issue=belongs_to_issue,
        )
        comment.__set_sqlite_to_bools()
        return comment

    @classmethod
    def load_issue_comments(cls, issue: DBIssue) -> "[DBComment]":
        """Load comments belonging to an issue from database"""
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
             user
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
            comment = cls(
                body=comment[0],
                html_url=comment[1],
                created=comment[2],
                updated=comment[3],
                comment_id=comment[4],
                is_native=comment[5],
                user=user,
                belongs_to_issue=issue,
            )
            comment.__set_sqlite_to_bools()
            comments.append(comment)

        if len(comments) == 0:
            return None

        return comments
