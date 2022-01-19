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
from .webfinger import INTERFACE_BASE_URL, INTERFACE_DOMAIN
from .users import DBUser


@dataclass
class DBRepo:
    """Repository information as stored in the database"""

    name: str
    owner: DBUser
    description: str
    html_url: str
    id: int = None
    private_key: RSAKeyPair = None

    def save(self):
        """Save repository to database"""
        repo = self.load(self.name, self.owner.user_id)
        if repo is not None:
            self.private_key = repo.private_key
            self.id = repo.id
            return

        self.owner.save()

        conn = get_db()
        cur = conn.cursor()
        count = 0
        while True:
            try:
                self.private_key = RSAKeyPair()
                cur.execute(
                    """
                    INSERT INTO gitea_forge_repositories
                        (owner_id, name, private_key, description, html_url) VALUES
                        (?, ?, ?, ?, ?);
                    """,
                    (
                        self.owner.id,
                        self.name,
                        self.private_key.private_key(),
                        self.description,
                        self.html_url,
                    ),
                )
                conn.commit()
                repo = self.load(self.name, self.owner.user_id)
                self.id = repo.id
                break
            except IntegrityError as e:
                count += 1
                if count > 5:
                    raise e
                continue

    @classmethod
    def load(cls, name: str, owner: str) -> "DBRepo":
        """Load repository from database"""
        owner = DBUser.load(owner)
        if owner is None:
            return None

        conn = get_db()
        cur = conn.cursor()

        data = cur.execute(
            """
                SELECT ID, private_key, description, html_url FROM gitea_forge_repositories
                WHERE name = ? AND owner_id = ?;
            """,
            (name, owner.id),
        ).fetchone()
        if data is None:
            return None
        resp = cls(name=name, owner=owner, description=data[2], html_url=data[3])
        resp.id = data[0]
        resp.private_key = RSAKeyPair.load_private_from_str(data[1])
        return resp

    @classmethod
    def load_with_id(cls, db_id: str) -> "DBRepo":
        """
        Load repository from database with database assigned ID>
        Database ID is different from forge assigned ID.
        """
        conn = get_db()
        cur = conn.cursor()
        data = cur.execute(
            """
                SELECT name, owner_id, private_key, description, html_url
                FROM gitea_forge_repositories
                WHERE ID = ?;
            """,
            (db_id,),
        ).fetchone()
        if data is None:
            return None
        owner = DBUser.load_with_db_id(data[1])
        resp = cls(name=data[0], owner=owner, description=data[3], html_url=data[4])
        resp.private_key = RSAKeyPair.load_private_from_str(data[2])
        resp.id = db_id
        return resp

    def actor_name(self) -> str:
        name = f"!{self.owner.user_id}!{self.name}"
        return name

    @staticmethod
    def split_actor_name(name) -> (str, str):
        """return format: (owner, repository_name)"""
        if "!" not in name:
            raise ValueError("Invalid actor name")

        name_parts = name.split("!")
        owner = name_parts[1]
        name = name_parts[2]
        return (owner, name)

    @classmethod
    def from_actor_name(cls, name) -> "DBRepo":
        (owner, name) = cls.split_actor_name(name)
        repo = cls.load(name=name, owner=owner)
        return repo

    def actor_url(self) -> str:
        act_url = f"{INTERFACE_BASE_URL}/r/{self.actor_name()}"
        return act_url

    def to_actor(self):
        act_url = self.actor_url()

        actor = {
            "@context": [
                "https://www.w3.org/ns/activitystreams",
                "https://w3id.org/security/v1",
            ],
            "id": act_url,
            "type": "Group",
            "preferredUsername": self.actor_name(),
            "name": self.actor_name(),
            "summary": f"<p>{self.description}</p>",
            "url": act_url,
            "inbox": f"{act_url}/inbox",
            "outbox": f"{act_url}/outbox",
            "followers": f"{act_url}/followers",
            "following": f"{act_url}/following",
            "publicKey": {
                "id": f"{act_url}#main-key",
                "owner": act_url,
                "publicKeyPem": self.private_key.to_json_key(),
            },
            "manuallyApprovesFollowers": False,
            "discoverable": True,
            "published": "2016-03-16T00:00:00Z",
            "alsoKnownAs": [act_url],
            "tag": [],
            "endpoints": {"sharedInbox": f"{act_url}/inbox"},
            "icon": {
                "type": "Image",
                "mediaType": "image/png",
                "url": self.owner.avatar_url,
            },
            "image": {
                "type": "Image",
                "mediaType": "image/png",
                "url": self.owner.avatar_url,
            },
        }

        return actor

    def webfinger_subject(self) -> str:
        subject = f"acct:{self.actor_name()}@{INTERFACE_DOMAIN}"
        return subject

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
