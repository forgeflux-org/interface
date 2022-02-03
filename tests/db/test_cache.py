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
import time

import pytest

from interface.db import get_db
from interface.db.cache import CACHE_TTL, RecordCount
from interface.db.repo import DBRepo
from interface.db.issues import DBIssue
from interface.db.users import DBUser
from interface.db.webfinger import INTERFACE_BASE_URL, INTERFACE_DOMAIN


def test_cache(client):
    """Test DB record count cache"""

    assert (
        DBUser.count.count() == 1
    )  # interface registers Interface user(bot user) on startup

    ttl = 2 * CACHE_TTL
    name = "db_test_user"
    user_id = name
    user = DBUser(
        name=name,
        user_id=user_id,
        profile_url=f"https://git.batsense.net/{user_id}",
        avatar_url=f"https://git.batsense.net/{user_id}",
        description="description",
    )

    assert DBUser.load(user_id) is None
    assert DBUser.load_with_db_id(11) is None

    user.save()
    assert DBUser.count.count() == 1
    time.sleep(ttl)
    assert DBUser.count.count() == 2
