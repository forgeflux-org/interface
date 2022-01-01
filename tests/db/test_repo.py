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
from interface.db.repo import DBRepo


def cmp_repo(lhs: DBRepo, rhs: DBRepo) -> bool:
    """Compare two DBRepo objects"""
    assert lhs is not None
    assert rhs is not None
    return all([lhs.name == rhs.name, lhs.owner == rhs.owner])


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
    with_id = DBRepo.load_with_id(from_db.id)

    assert cmp_repo(from_db, repo)
    assert cmp_repo(from_db, with_id)
    from_db2 = DBRepo.load(name, owner)
    assert cmp_repo(from_db, from_db2)
    assert from_db.id == from_db2.id
