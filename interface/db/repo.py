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
class DBRepo:
    """Repository information as stored in the database"""

    name: str
    owner: str
    id: int = None

    def save(self):
        """Save repository to database"""
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT OR IGNORE INTO gitea_forge_repositories
                (owner, name) VALUES
                (?, ?);
            """,
            (self.owner, self.name),
        )
        conn.commit()

    @classmethod
    def load(cls, name: str, owner: str) -> "DBRepo":
        """Save repository to database"""
        conn = get_db()
        cur = conn.cursor()
        data = cur.execute(
            """
                SELECT ID from gitea_forge_repositories
                WHERE name = ? AND owner = ?;
            """,
            (name, owner),
        ).fetchone()
        if data is None:
            return None
        cls.name = name
        cls.owner = owner
        cls.id = data[0]
        return cls
