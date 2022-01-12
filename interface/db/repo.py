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

trimed_base_url = trim_url(settings.SERVER.url)


@dataclass
class DBRepo:
    """Repository information as stored in the database"""

    name: str
    owner: str
    id: int = None
    private_key: RSAKeyPair = None

    def save(self):
        """Save repository to database"""
        repo = self.load(self.name, self.owner)
        if repo is not None:
            self.private_key = repo.private_key
            self.id = repo.id
            print("repo early exit")
            return

        conn = get_db()
        cur = conn.cursor()
        count = 0
        while True:
            try:
                self.private_key = RSAKeyPair()
                cur.execute(
                    """
                    INSERT INTO gitea_forge_repositories
                        (owner, name, private_key) VALUES
                        (?, ?, ?);
                    """,
                    (self.owner, self.name, self.private_key.private_key()),
                )
                conn.commit()
                break
            except IntegrityError as e:
                print(e)
                count += 1
                if count > 5:
                    raise e
                continue

    @classmethod
    def load(cls, name: str, owner: str) -> "DBRepo":
        """Load repository from database"""
        conn = get_db()
        cur = conn.cursor()
        data = cur.execute(
            """
                SELECT ID, private_key from gitea_forge_repositories
                WHERE name = ? AND owner = ?;
            """,
            (name, owner),
        ).fetchone()
        print(data)
        if data is None:
            return None
        resp = cls(name=name, owner=owner)
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
                SELECT name, owner, private_key from gitea_forge_repositories
                WHERE ID = ?;
            """,
            (db_id,),
        ).fetchone()
        if data is None:
            return None
        resp = cls(name=data[0], owner=data[1])
        resp.private_key = RSAKeyPair.load_private_from_str(data[2])
        resp.id = db_id
        return resp

    def actor_name(self) -> str:
        name = f"!{self.owner}!{self.name}"
        return name

    def actor_url(self) -> str:
        act_url = f"{trimed_base_url}/r/!{self.actor_name()}"
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
            "subject": f"acct:{self.actor_name()}@{trimed_base_url}",
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
