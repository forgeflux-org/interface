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
from interface.db import get_db
from interface.db.interfaces import DBInterfaces
from interface.db.repo import DBRepo
from interface.db.issues import DBIssue
from interface.db.users import DBUser

from interface.auth import KeyPair


def test_repo(client):
    """Test repo"""

    owner = "foo"
    name = "foo"

    repo = DBRepo(
        name=name,
        owner=owner,
        id=None,
    )

    repo.save()
    from_db = DBRepo.load(name, owner)

    assert from_db.name == name
    assert from_db.owner == owner
    assert from_db.id is not None
    from_db2 = DBRepo.load(name, owner)
    assert from_db.id is from_db2.id
