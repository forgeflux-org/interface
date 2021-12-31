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


from .conn import get_db
from .interfaces import DBInterfaces


@dataclass
class DBUser:
    """User information as stored in the database"""

    # Display name
    name: str
    # login handle/username
    user_id: str
    profile_url: str
    signed_by: DBInterfaces
    id: int = None

    def save(self):
        """Save user to database"""
        self.signed_by.save()

        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT OR IGNORE INTO gitea_users
                (name, user_id, profile_url, signed_by) VALUES
                (?, ?, ?, (SELECT ID from interfaces WHERE url = ?));
            """,
            (self.name, self.user_id, self.profile_url, self.signed_by.url),
        )
        conn.commit()

    @classmethod
    def load(cls, user_id: str) -> "DBUser":
        """Load user from database with the URL of the interface which signed it's creation"""
        conn = get_db()
        cur = conn.cursor()
        data = cur.execute(
            """
             SELECT
                 users.ID,
                 users.name,
                 users.profile_url,
                 interfaces.ID,
                 interfaces.url,
                 interfaces.public_key
             FROM
                 gitea_users AS users
             INNER JOIN interfaces AS interfaces
                 ON users.signed_by = interfaces.ID
            WHERE
                users.user_id = ?
            """,
            (user_id,),
        ).fetchone()
        if data is None:
            return None
        return cls(
            id=data[0],
            name=data[1],
            user_id=user_id,
            profile_url=data[2],
            signed_by=DBInterfaces(id=data[3], url=data[4], public_key=data[4]),
        )

    @classmethod
    def load_with_db_id(cls, db_id: str) -> "DBUser":
        """
        Load user from database with the database assigned ID.
        DB assigned ID is different from the one the forge assigns.
        """
        conn = get_db()
        cur = conn.cursor()
        data = cur.execute(
            """
             SELECT
                 users.user_id,
                 users.name,
                 users.profile_url,
                 interfaces.ID,
                 interfaces.url,
                 interfaces.public_key
             FROM
                 gitea_users AS users
             INNER JOIN interfaces AS interfaces
                 ON users.signed_by = interfaces.ID
            WHERE
                users.ID = ?
            """,
            (db_id,),
        ).fetchone()
        if data is None:
            return None
        return cls(
            user_id=data[0],
            name=data[1],
            id=db_id,
            profile_url=data[2],
            signed_by=DBInterfaces(id=data[3], url=data[4], public_key=data[4]),
        )
