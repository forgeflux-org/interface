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
from dynaconf import settings

from interface.db import DBInterfaces, DBSubscribe, DBRepo
from interface.auth import KeyPair
from interface.app import app

from .test_repo import cmp_repo
from .test_interface import cmp_interface


def cmp_subscriber(lhs: DBSubscribe, rhs: DBSubscribe) -> bool:
    """Compare two DBInterfaces objects"""
    return all(
        [
            cmp_interface(lhs.subscriber, rhs.subscriber),
            cmp_repo(lhs.repository, rhs.repository),
        ]
    )


def test_interface(client):
    """Test DBInterfaces database class"""

    key = KeyPair()
    url = "https://test_interface.example.com"
    interface = DBInterfaces(url=url, public_key=key.to_base64_public())
    interface.save()

    repo = DBRepo(name="name", owner="owner")
    repo.save()

    subscriber = DBSubscribe(repository=repo, subscriber=interface)

    assert DBSubscribe.load(repository=repo) is None

    subscriber.save()

    from_db: [DBSubscribe] = DBSubscribe.load(repository=repo)
    assert len(from_db) == 1
    assert cmp_subscriber(from_db.pop(), subscriber)
