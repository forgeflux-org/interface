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
from interface.db import get_db
from interface.db.interfaces import DBInterfaces
from interface.db.repo import DBRepo
from interface.db.issues import DBIssue
from interface.db.users import DBUser

from interface.auth import KeyPair


def cmp_user(lhs: DBUser, rhs: DBUser) -> bool:
    assert lhs is not None
    assert rhs is not None

    return all(
        [
            lhs.name == rhs.name,
            lhs.user_id == rhs.user_id,
            lhs.profile_url == rhs.profile_url,
            lhs.signed_by.url == rhs.signed_by.url,
        ]
    )


def test_user(client):
    """Test user route"""

    key = KeyPair()
    url = "https://db-test-user.example.com"
    interface = DBInterfaces(url=url, public_key=key.to_base64_public())
    name = "db_test_user"
    user_id = name
    user = DBUser(
        name=name,
        user_id=user_id,
        profile_url=f"https://git.batsense.net/{user_id}",
        signed_by=interface,
    )

    assert DBUser.load(user_id) is None
    assert DBUser.load_with_db_id(11) is None

    user.save()

    from_db = DBUser.load(user.user_id)
    assert from_db is not None
    with_id = DBUser.load_with_db_id(from_db.id)

    assert cmp_user(from_db, user) is True
    assert cmp_user(from_db, with_id) is True
