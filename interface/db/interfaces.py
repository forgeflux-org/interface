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
from dynaconf import settings
from flask import g

from .conn import get_db


@dataclass
class DBInterfaces:
    """Interface information as represented in database"""

    url: str
    id: int = None

    def save(self):
        """Save interface to database"""
        conn = get_db()
        cur = conn.cursor()
        cur.execute("INSERT OR IGNORE INTO interfaces (url) VALUES (?);", (self.url,))
        conn.commit()

    @classmethod
    def load_from_url(cls, url: str) -> "DBInterfaces":
        """Load interface from database"""
        conn = get_db()
        cur = conn.cursor()
        data = cur.execute(
            "SELECT ID FROM interfaces WHERE url = ?;",
            (url,),
        ).fetchone()
        if data is None:
            return None
        return cls(
            id=data[0],
            url=url,
        )

    @classmethod
    def load_from_database_id(cls, db_id: int) -> "DBInterfaces":
        """
        Load interface from database using Database assigned, autoincrementd ID.
        This ID is different from the one assigned by forges.
        """
        conn = get_db()
        cur = conn.cursor()
        data = cur.execute(
            "SELECT url  FROM interfaces WHERE ID = ?;",
            (db_id,),
        ).fetchone()
        if data is None:
            return None
        return cls(
            url=data[0],
            id=db_id,
        )


def get_db_interface() -> DBInterfaces:
    """Get DBInterfaces of this interface"""
    if "g.db_interface" not in g:
        interface = DBInterfaces(url=settings.SERVER.url)
        interface.save()
        g.db_interface = interface
    return g.db_interface
