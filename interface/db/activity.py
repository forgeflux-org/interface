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
from enum import Enum, unique
from dataclasses import dataclass


from .conn import get_db
from interface.utils import since_epoch


@unique
class ActivityType(Enum):
    """Represents the type of an activity"""

    CREATE = 0
    DELETE = 1
    UPDATE = 2
    FOLLOW = 3
    UNFOLLOW = 4

    def __str__(self) -> str:
        return self.name


@dataclass
class DBActivity:
    """Activity information in the database"""

    user_id: int
    activity: ActivityType
    created: int = None
    comment_id: int = None
    issue_id: int = None
    id: int = None

    def __post_init__(self):
        if all([self.issue_id is None, self.comment_id is None]):
            raise ValueError("Either issue_id or comment_id must be provided")
        if self.created is None:
            self.created = since_epoch()

    def save(self):
        """Save message to database"""
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO activities
                (user_id, activity, created, comment_id, issue_id)
            VALUES
                (?, ?, ?, ?, ?)
            """,
            (
                self.user_id,
                self.activity.value,
                self.created,
                self.comment_id,
                self.issue_id,
            ),
        )
        conn.commit()
        if self.issue_id:
            data = cur.execute(
                """
                SELECT ID FROM activities
                WHERE
                    user_id = ?
                AND
                    activity = ?
                AND
                    created = ?
                AND
                    issue_id = ?
                """,
                (
                    self.user_id,
                    self.activity.value,
                    self.created,
                    self.issue_id,
                ),
            ).fetchone()
            self.id = data[0]
        else:
            data = cur.execute(
                """
                SELECT ID FROM activities
                WHERE
                    user_id = ?
                AND
                    activity = ?
                AND
                    created = ?
                AND
                    comment_id = ?
                """,
                (self.user_id, self.activity.value, self.created, self.comment_id),
            ).fetchone()
            self.id = data[0]

    @classmethod
    def load_with_db_id(cls, db_id: int) -> "DBActivity":
        """Load Activity from database with database ID assigned to the activity"""
        conn = get_db()
        cur = conn.cursor()
        data = cur.execute(
            """
             SELECT
                 activity,
                 user_id,
                 created,
                 issue_id,
                 comment_id
             FROM
                 activities
             WHERE
                ID = ?
            """,
            (db_id,),
        ).fetchone()
        if data is None:
            return None
        val = cls(
            activity=ActivityType(data[0]),
            user_id=data[1],
            created=data[2],
            issue_id=data[3],
            comment_id=data[4],
            id=db_id,
        )
        return val
