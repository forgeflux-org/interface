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
from datetime import datetime

import pytest
from interface.settings import settings

from interface.db import get_db, DBActivity, ActivityType, DBComment
from interface.db.cache import CACHE_TTL
from interface.db.activity import ActiveUsersinPeriod
from interface.db.repo import DBRepo
from interface.db.issues import DBIssue
from interface.db.users import DBUser
from interface.utils import since_epoch


def cmp_activity(lhs: DBActivity, rhs: DBActivity) -> bool:
    assert lhs is not None
    assert rhs is not None

    return all(
        [
            lhs.user_id == rhs.user_id,
            lhs.comment_id == rhs.comment_id,
            lhs.issue_id == rhs.issue_id,
            lhs.activity == rhs.activity,
            lhs.id == rhs.id,
            lhs.created == rhs.created,
        ]
    )


def test_acitivty(client):
    """Test DBActivity"""

    assert CACHE_TTL < 5  # if this fails, then five_seconds will show more
    assert DBActivity.load_with_db_id(db_id=100) is None

    ttl = settings.SYSTEM.cache_ttl * 2  # in seconds
    assert DBActivity.count.count() == 0

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

    user.save()

    # repository data
    repo_name = "repo_name"
    repo = DBRepo(
        name=repo_name,
        description="foo",
        owner=user,
        html_url=f"{profile_url}/{repo_name}",
    )

    title = "Test issue"
    description = "foo bar"
    repo_scope_id = 8
    html_url = f"https://git.batsense/{user.user_id}/{repo_name}/issues/{repo_scope_id}"
    created = since_epoch()
    updated = since_epoch()
    # repository= repo
    is_closed = False
    is_merged = None
    is_native = True

    issue = DBIssue(
        title=title,
        description=description,
        html_url=html_url,
        created=created,
        updated=updated,
        repo_scope_id=repo_scope_id,
        repository=repo,
        user=user,
        is_closed=is_closed,
        is_merged=is_merged,
        is_native=is_native,
    )

    issue.save()

    five_seconds = ActiveUsersinPeriod(since=5)
    one_second = ActiveUsersinPeriod(since=1)
    assert one_second.count() == 1
    assert five_seconds.count() == 1

    assert DBActivity.count.count() == 0
    time.sleep(ttl)
    assert DBActivity.count.count() == 1
    assert one_second.count() == 0
    assert five_seconds.count() == 1
    time.sleep(5)
    assert five_seconds.count() == 0

    with pytest.raises(ValueError):
        DBActivity(user_id=user.id, activity=ActivityType.CREATE)

    print(f"issue id: {issue.id}")
    activity = DBActivity(
        user_id=user.id, activity=ActivityType.CREATE, issue_id=issue.id
    )
    activity.save()
    assert cmp_activity(activity, DBActivity.load_with_db_id(db_id=activity.id))
    time.sleep(ttl)
    assert DBActivity.count.count() == 2

    comment_body = "test comment"
    comment_id1 = 1
    comment_url1 = f"https://git.batsense.net/{repo.name}/{repo.owner.user_id}/issues/{repo_scope_id}/{comment_id1}"
    comment1 = DBComment(
        body=comment_body,
        created=since_epoch(),
        updated=since_epoch(),
        is_native=True,
        belongs_to_issue=issue,
        user=user,
        html_url=comment_url1,
        comment_id=comment_id1,
    )

    comment1.save()

    activity1 = DBActivity(
        user_id=user.id, activity=ActivityType.CREATE, comment_id=comment1.id
    )
    activity1.save()
    assert cmp_activity(activity1, DBActivity.load_with_db_id(db_id=activity1.id))
