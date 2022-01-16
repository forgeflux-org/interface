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
import pytest

from interface.db import DBRepo, DBUser

from .test_user import cmp_user


def cmp_repo(lhs: DBRepo, rhs: DBRepo) -> bool:
    """Compare two DBRepo objects"""
    assert lhs is not None
    assert rhs is not None
    return all(
        [
            lhs.name == rhs.name,
            lhs.description == rhs.description,
            lhs.html_url == rhs.html_url,
            cmp_user(lhs.owner, rhs.owner),
        ]
    )


def test_repo(client):
    """Test repo"""

    # user data signed by interface1
    username = "db_test_user"
    user_id = f"{username}@git.batsense.net"
    profile_url = f"https://git.batsense.net/{username}"
    user = DBUser(
        name=username,
        user_id=user_id,
        profile_url=profile_url,
        avatar_url=profile_url,
        description="description",
        id=None,
    )

    name = "foo"

    repo = DBRepo(
        name=name,
        owner=user,
        description="foo",
        id=None,
        html_url=f"{profile_url}/{name}",
    )
    assert DBRepo.load(name, user.user_id) is None
    assert DBRepo.load_with_id(11) is None

    user.save()
    repo.save()
    from_db = DBRepo.load(name, user.user_id)
    with_id = DBRepo.load_with_id(from_db.id)

    assert cmp_repo(from_db, repo)
    assert cmp_repo(from_db, with_id)
    from_db2 = DBRepo.load(name, user.user_id)
    assert cmp_repo(from_db, from_db2)
    assert from_db.id == from_db2.id

    webfinger = from_db.webfinger()
    assert webfinger["subject"] == from_db.webfinger_subject()
    assert webfinger["aliases"] == [from_db.actor_url()]
    assert len(webfinger["links"]) == 2
    for link in webfinger["links"]:
        assert link["href"] == from_db.actor_url()

    actor = from_db.to_actor()
    assert actor["preferredUsername"] == from_db.actor_name()
    assert actor["name"] == from_db.actor_name()
    assert actor["id"] == from_db.actor_url()
    assert actor["inbox"] == f"{from_db.actor_url()}/inbox"
    assert actor["outbox"] == f"{from_db.actor_url()}/outbox"
    assert actor["followers"] == f"{from_db.actor_url()}/followers"
    assert actor["following"] == f"{from_db.actor_url()}/following"
    assert from_db.description in actor["summary"]
    assert actor["url"] == from_db.actor_url()
    assert actor["icon"]["url"] == from_db.owner.avatar_url
    assert actor["image"]["url"] == from_db.owner.avatar_url

    with pytest.raises(ValueError) as _:
        from_db.split_actor_name("foo")

    (r_owner, r_repo_name) = from_db.split_actor_name(actor["name"])
    assert r_owner == from_db.owner.user_id
    assert r_repo_name == from_db.name

    cmp_repo(from_db, from_db.from_actor_name(actor["name"]))
