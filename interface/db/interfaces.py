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


@dataclass
class DBInterfaces:
    """Interface information as represented in database"""

    url: str
    public_key: str
    id: int = None

    def save(self):
        """Save interface to database"""
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO interfaces (url, public_key) VALUES (?, ?);",
            (self.url, self.public_key),
        )
        conn.commit()

    @classmethod
    def load_from_url(cls, url: str) -> "DBInterfaces":
        """Load interface from database"""
        conn = get_db()
        cur = conn.cursor()
        data = cur.execute(
            "SELECT ID, public_key  FROM interfaces WHERE url = ?;",
            (url,),
        ).fetchone()
        if data is None:
            return None
        return cls(
            id=data[0],
            public_key=data[1],
            url=url,
        )

    @classmethod
    def load_from_pk(cls, public_key: str) -> "DBInterfaces":
        """Load interface from database"""
        conn = get_db()
        cur = conn.cursor()
        data = cur.execute(
            "SELECT ID, url  FROM interfaces WHERE public_key = ?;",
            (public_key,),
        ).fetchone()
        if data is None:
            return None

        return cls(
            id=data[0],
            url=data[1],
            public_key=public_key,
        )
