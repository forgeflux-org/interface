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

from interface.auth import RSAKeyPair

from .conn import get_db
from .interfaces import DBInterfaces
from .webfinger import INTERFACE_BASE_URL, INTERFACE_DOMAIN


@dataclass
class DBUser:
    """User information as stored in the database"""

    # Display name
    name: str
    # login handle/username
    user_id: str
    profile_url: str
    avatar_url: str
    description: str
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
            return

        conn = get_db()
        cur = conn.cursor()
        count = 0
        while True:
            try:
                self.private_key = RSAKeyPair()
                cur.execute(
                    """
                    INSERT INTO gitea_users
                        (
                            name, user_id, profile_url,
                            avatar_url, signed_by, private_key,
                            description
                        ) VALUES (
                            ?, ?, ?, ?, 
                            (SELECT ID from interfaces WHERE url = ?),
                            ?, ?
                        );
                    """,
                    (
                        self.name,
                        self.user_id,
                        self.profile_url,
                        self.avatar_url,
                        self.signed_by.url,
                        self.private_key.private_key(),
                        self.description,
                    ),
                )
                conn.commit()
                break
            except IntegrityError as e:
                count += 1
                if count > 5:
                    raise e
                continue

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
                 avatar_url,
                 signed_by,
                 description
             FROM
                 gitea_users
            WHERE
                user_id = ?
            """,
            (user_id,),
        ).fetchone()
        if data is None:
            return None

        signed_by = DBInterfaces.load_from_database_id(data[5])
        res = cls(
            id=data[0],
            name=data[1],
            user_id=user_id,
            profile_url=data[2],
            avatar_url=data[4],
            signed_by=signed_by,
            description=data[6],
        )
        res.private_key = RSAKeyPair.load_private_from_str(data[3])
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
                 user_id,
                 name,
                 profile_url,
                 private_key,
                 avatar_url,
                 signed_by,
                 description
             FROM
                 gitea_users
             WHERE ID = ?
            """,
            (db_id,),
        ).fetchone()
        if data is None:
            return None

        signed_by = DBInterfaces.load_from_database_id(data[5])

        res = cls(
            user_id=data[0],
            name=data[1],
            id=db_id,
            profile_url=data[2],
            avatar_url=data[4],
            signed_by=signed_by,
            description=data[6],
        )
        res.private_key = RSAKeyPair.load_private_from_str(data[3])
        return res

    def actor_url(self) -> str:
        act_url = f"{INTERFACE_BASE_URL}/u/{self.user_id}"
        return act_url

    def actor_name(self) -> str:
        return self.user_id

    def webfinger_subject(self) -> str:
        subject = f"acct:{self.actor_name()}@{INTERFACE_DOMAIN}"
        return subject

    def to_actor(self):
        act_url = self.actor_url()

        actor = {
            "@context": [
                "https://www.w3.org/ns/activitystreams",
                "https://w3id.org/security/v1",
            ],
            "id": act_url,
            "type": "Person",
            "preferredUsername": self.actor_name(),
            "name": self.name,
            "inbox": f"{act_url}/inbox",
            "outbox": f"{act_url}/outbox",
            "followers": f"{act_url}/followers",
            "following": f"{act_url}/following",
            "publicKey": {
                "id": f"{act_url}#main-key",
                "owner": act_url,
                "publicKeyPem": self.private_key.to_json_key(),
            },
            "summary": f"<p>{self.description}</p>",
            "url": act_url,
            "manuallyApprovesFollowers": False,
            "discoverable": True,
            "published": "2016-03-16T00:00:00Z",
            "alsoKnownAs": [act_url],
            "tag": [],
            "endpoints": {"sharedInbox": f"{act_url}/inbox"},
            "icon": {
                "type": "Image",
                "mediaType": "image/png",
                "url": self.avatar_url,
            },
            "image": {
                "type": "Image",
                "mediaType": "image/png",
                "url": self.avatar_url,
            },
        }
        return actor

    def webfinger(self):
        act_url = self.actor_url()
        resp = {
            "subject": self.webfinger_subject(),
            "aliases": [act_url],
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
