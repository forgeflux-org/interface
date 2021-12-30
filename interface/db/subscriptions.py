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

from .repo import DBRepo
from .interfaces import DBInterfaces
from .conn import get_db


@dataclass
class DBSubscribe:
    """Issue information as stored in database"""

    repository: DBRepo
    subscriber: DBInterfaces

    def save(self):
        """Save Issue to database"""
        self.repository.save()
        self.subscriber.save()

        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT OR IGNORE INTO subscriptions
                ( repository_id, interface_id)
            VALUES (
                (SELECT ID FROM gitea_forge_repositories WHERE owner  = ? AND name = ?),
                (SELECT ID FROM interfaces WHERE url  = ?)
            )
            """,
            (
                self.repository.owner,
                self.repository.name,
                self.subscriber.url,
            ),
        )
        conn.commit()
        assert self.load(self.repository) is not None
        print("Saved subscriber")

    @classmethod
    def load(cls, repository: DBRepo):
        """Load issue from database"""
        conn = get_db()
        cur = conn.cursor()
        data = cur.execute(
            """
         SELECT
             interfaces.url,
             interfaces.public_key,
             interfaces.ID
        FROM
             subscriptions AS subscriptions
        INNER JOIN interfaces AS interfaces
            ON subscriptions.interface_id = interfaces.ID
        WHERE
            subscriptions.repository_id = (
                SELECT ID FROM gitea_forge_repositories WHERE owner = ? AND name = ?
            );
        """,
            (repository.owner, repository.name),
        ).fetchall()
        if data is None:
            return None

        subscribers = []
        for interface in data:
            subscribers.append(
                cls(
                    subscriber=DBInterfaces(
                        url=interface[0],
                        public_key=interface[2],
                        id=interface[1],
                    ),
                    repository=repository,
                )
            )

        if len(subscribers) == 0:
            return None
        return subscribers
