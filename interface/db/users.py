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
from sqlite3 import IntegrityError
from dynaconf import settings

from interface.auth import RSAKeyPair
from interface.utils import trim_url

from .conn import get_db
from .interfaces import DBInterfaces

trimed_base_url = trim_url(settings.SERVER.url)


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
    private_key: RSAKeyPair = None

    def save(self):
        """Save user to database"""
        self.signed_by.save()

        user = self.load(self.user_id)
        if user is not None:
            self.private_key = user.private_key
            self.id = user.id
            print("early return")
            return

        print("no early return")

        conn = get_db()
        cur = conn.cursor()
        count = 0
        while True:
            try:
                self.private_key = RSAKeyPair()
                cur.execute(
                    """
                    INSERT INTO gitea_users
                        (name, user_id, profile_url, signed_by, private_key) VALUES
                        (?, ?, ?, (SELECT ID from interfaces WHERE url = ?), ?);
                    """,
                    (
                        self.name,
                        self.user_id,
                        self.profile_url,
                        self.signed_by.url,
                        self.private_key.private_key(),
                    ),
                )
                conn.commit()
                break
            except IntegrityError as e:
                count += 1
                if count > 5:
                    raise e
                continue

        print(f"save {self.user_id}")
        print(f" from save: {self.private_key.private_key()}")

    @classmethod
    def load(cls, user_id: str) -> "DBUser":
        """Load user from database with the URL of the interface which signed it's creation"""
        conn = get_db()
        cur = conn.cursor()
        data = cur.execute(
            """
             SELECT
                 ID,
                 name,
                 profile_url,
                 private_key,
                 signed_by
             FROM
                 gitea_users
            WHERE
                user_id = ?
            """,
            (user_id,),
        ).fetchone()
        print(f"load {user_id}")
        if data is None:
            print("data is none")
            return None

        signed_by = DBInterfaces.load_from_database_id(data[4])
        res = cls(
            id=data[0],
            name=data[1],
            user_id=user_id,
            profile_url=data[2],
            signed_by=signed_by,
        )
        res.private_key = RSAKeyPair.load_private_from_str(data[3])
        print(res)
        print(type(res))
        return res

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
                 interfaces.public_key,
                 users.private_key
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
        res = cls(
            user_id=data[0],
            name=data[1],
            id=db_id,
            profile_url=data[2],
            signed_by=DBInterfaces(id=data[3], url=data[4], public_key=data[5]),
        )
        res.private_key = RSAKeyPair.load_private_from_str(data[6])
        return res

    def actor_url(self) -> str:
        act_url = f"{trimed_base_url}/u/{self.user_id}"
        return act_url

    def to_actor(self):
        act_url = self.actor_url()

        actor = {
            "@context": [
                "https://www.w3.org/ns/activitystreams",
                "https://w3id.org/security/v1",
            ],
            "id": act_url,
            "type": "Person",
            "preferredUsername": self.name,
            "inbox": f"{act_url}/inbox",
            "outbox": f"{act_url}/outbox",
            "followers": f"{act_url}/followers",
            "following": f"{act_url}/following",
            "publicKey": {
                "id": f"{act_url}#main-key",
                "owner": act_url,
                "publicKeyPem": self.private_key.to_json_key(),
            },
        }
        return actor

    def webfinger(self):
        act_url = self.actor_url()
        resp = {
            "subject": f"acct:{self.user_id}@{trimed_base_url}",
            "links": [
                {
                    "rel": "self",
                    "type": "application/activity+json",
                    "href": act_url,
                },
                {
                    "rel": "http://webfinger.net/rel/profile-page",
                    "type": "text/html",
                    "href": act_url,
                },
            ],
        }
        return resp
