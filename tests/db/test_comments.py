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

from interface.db import get_db
from interface.db.repo import DBRepo
from interface.db.issues import DBIssue
from interface.db.users import DBUser
from interface.db.comments import DBComment
from interface.db.cache import CACHE_TTL
from interface.utils import since_epoch

from tests.db.test_user import cmp_user
from tests.db.test_issue import cmp_issue


def cmp_comment(lhs: DBComment, rhs: DBComment) -> bool:
    assert lhs is not None
    assert rhs is not None

    return all(
        [
            lhs.body == rhs.body,
            lhs.created == rhs.created,
            lhs.updated == rhs.updated,
            lhs.is_native == rhs.is_native,
            cmp_user(lhs.user, rhs.user),
            cmp_issue(lhs.belongs_to_issue, rhs.belongs_to_issue),
            lhs.comment_id == rhs.comment_id,
            lhs.html_url == rhs.html_url,
        ]
    )


def test_comment(client):
    """Test user route"""

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
    user.save()

    # repository data
    repo_name = "repo_name"
    repo_owner = user.user_id
    repo = DBRepo(
        name=repo_name,
        owner=user,
        description="foo",
        html_url=f"{profile_url}/{repo_name}",
    )
    repo.save()

    title = "Test issue"
    description = "foo bar"
    repo_scope_id = 8
    html_url = f"https://git.batsense/{repo_owner}/{repo_name}/issues/{repo_scope_id}"
    created = since_epoch()
    updated = since_epoch()
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

    comment_body = "test comment"
    comment_id1 = 1
    comment_url1 = f"https://git.batsense.net/{repo_owner}/{repo_name}/issues/{repo_scope_id}/{comment_id1}"
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
    assert DBComment.load_issue_comments(issue) is None
    assert DBComment.load_from_comment_url(comment1.html_url) is None
    assert DBComment.count.count() == 0

    comment1.save()
    assert DBComment.count.count() == 0
    time.sleep(CACHE_TTL * 2)
    assert DBComment.count.count() == 1
    assert comment1.id is not None

    comment_id2 = 2
    comment_url2 = f"https://git.batsense.net/{repo_owner}/{repo_name}/issues/{repo_scope_id}/{comment_id2}"

    comment2 = DBComment(
        body=comment_body,
        created=since_epoch(),
        updated=since_epoch(),
        is_native=True,
        belongs_to_issue=issue,
        user=user,
        html_url=comment_url2,
        comment_id=comment_id2,
    )

    comment2.save()

    for comment in DBComment.load_issue_comments(issue):
        from_url = DBComment.load_from_comment_url(comment.html_url)
        assert cmp_comment(comment, from_url)
        if comment.comment_id == comment1.comment_id:
            assert cmp_comment(comment1, comment)
        else:
            assert cmp_comment(comment2, comment)
