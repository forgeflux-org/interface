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
from datetime import datetime

from interface.db import get_db
from interface.db.interfaces import DBInterfaces
from interface.db.repo import DBRepo
from interface.db.issues import DBIssue
from interface.db.users import DBUser
from interface.db.comments import DBComment

from interface.auth import KeyPair


from tests.db.test_user import cmp_user
from tests.db.test_issue import cmp_issue
from tests.db.test_interface import cmp_interface


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
            cmp_interface(lhs.signed_by, rhs.signed_by),
            cmp_issue(lhs.belongs_to_issue, rhs.belongs_to_issue),
            lhs.comment_id == rhs.comment_id,
            lhs.html_url == rhs.html_url,
            lhs.signed_by.url == rhs.signed_by.url,
        ]
    )


def test_comment(client):
    """Test user route"""

    # first interface data
    key1 = KeyPair()
    interface_url1 = "https://db-test-issue.example.com"
    interface1 = DBInterfaces(url=interface_url1, public_key=key1.to_base64_public())

    # second interface data
    key2 = KeyPair()
    interface_url2 = "https://db-test-issue2.example.com"
    interface2 = DBInterfaces(url=interface_url2, public_key=key2.to_base64_public())

    # user data signed by interface1
    username = "db_test_user"
    user_id = f"{username}@git.batsense.net"
    profile_url = f"https://git.batsense.net/{username}"
    user = DBUser(
        name=username,
        user_id=user_id,
        profile_url=profile_url,
        signed_by=interface1,
        id=None,
    )

    # repository data
    repo_name = "repo_name"
    repo_owner = "repo_owner"
    repo = DBRepo(name=repo_name, owner=repo_owner)

    title = "Test issue"
    description = "foo bar"
    repo_scope_id = 8
    html_url = f"https://git.batsense/{repo_owner}/{repo_name}/issues/{repo_scope_id}"
    created = str(datetime.now())
    updated = str(datetime.now())
    # repository= repo
    # signed_by = interface2
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
        signed_by=interface2,
        is_closed=is_closed,
        is_merged=is_merged,
        is_native=is_native,
    )

    comment_body = "test comment"
    comment_id1 = 1
    comment_url1 = f"https://git.batsense.net/{repo_owner}/{repo_name}/issues/{repo_scope_id}/{comment_id1}"
    comment1 = DBComment(
        body=comment_body,
        created=str(datetime.now()),
        updated=str(datetime.now()),
        is_native=True,
        signed_by=interface1,
        belongs_to_issue=issue,
        user=user,
        html_url=comment_url1,
        comment_id=comment_id1,
    )
    assert DBComment.load_issue_comments(issue) is None
    assert DBComment.load_from_comment_url(comment1.html_url) is None

    comment1.save()

    comment_id2 = 2
    comment_url2 = f"https://git.batsense.net/{repo_owner}/{repo_name}/issues/{repo_scope_id}/{comment_id2}"

    comment2 = DBComment(
        body=comment_body,
        created=str(datetime.now()),
        updated=str(datetime.now()),
        is_native=True,
        signed_by=interface1,
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
