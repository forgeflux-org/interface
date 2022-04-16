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
from interface.db.repo import DBRepo
from interface.db.issues import DBIssue
from interface.db.users import DBUser
from interface.db.webfinger import INTERFACE_BASE_URL, INTERFACE_DOMAIN

from .utils import cmp_user, get_user


def test_user(client):
    """Test user route"""

    user = get_user()

    assert DBUser.load(user.user_id) is None
    assert DBUser.load_with_db_id(11) is None

    user.save()

    from_db = DBUser.load(user.user_id)
    assert from_db is not None
    with_id = DBUser.load_with_db_id(from_db.id)

    assert cmp_user(from_db, user) is True
    assert cmp_user(from_db, with_id) is True

    assert from_db.actor_url() == f"{INTERFACE_BASE_URL}/u/{from_db.user_id}"
    assert from_db.actor_name() == from_db.user_id
    assert from_db.webfinger_subject() == f"acct:{from_db.user_id}@{INTERFACE_DOMAIN}"

    webfinger = from_db.webfinger()
    assert webfinger["subject"] == from_db.webfinger_subject()
    assert webfinger["aliases"] == [from_db.actor_url()]
    assert len(webfinger["links"]) == 2
    for link in webfinger["links"]:
        assert link["href"] == from_db.actor_url()

    actor = from_db.to_actor()
    assert actor["preferredUsername"] == from_db.user_id
    assert actor["name"] == from_db.name
    assert actor["id"] == from_db.actor_url()
    assert actor["inbox"] == f"{from_db.actor_url()}/inbox"
    assert actor["outbox"] == f"{from_db.actor_url()}/outbox"
    assert actor["followers"] == f"{from_db.actor_url()}/followers"
    assert actor["following"] == f"{from_db.actor_url()}/following"
    assert from_db.description in actor["summary"]
    assert actor["url"] == from_db.actor_url()
    assert actor["icon"]["url"] == from_db.avatar_url
    assert actor["image"]["url"] == from_db.avatar_url
