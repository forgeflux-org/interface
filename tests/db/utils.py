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

from interface.db import get_db, DBComment
from interface.db.repo import DBRepo
from interface.db.issues import DBIssue, OPEN, MERGED, CLOSED
from interface.utils import since_epoch
from interface.db.users import DBUser


def cmp_user(lhs: DBUser, rhs: DBUser) -> bool:
    assert lhs is not None
    assert rhs is not None

    return all(
        [
            lhs.name == rhs.name,
            lhs.user_id == rhs.user_id,
            lhs.profile_url == rhs.profile_url,
            lhs.avatar_url == rhs.avatar_url,
            lhs.description == rhs.description,
        ]
    )


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


def cmp_issue(lhs: DBIssue, rhs: DBIssue) -> bool:
    assert lhs is not None
    assert rhs is not None

    res = [
        lhs.title == rhs.title,
        lhs.description == rhs.description,
        lhs.repo_scope_id == rhs.repo_scope_id,
        lhs.html_url == rhs.html_url,
        lhs.created == rhs.created,
        lhs.updated == rhs.updated,
        lhs.is_closed == rhs.is_closed,
        lhs.is_merged == rhs.is_merged,
        lhs.is_native == rhs.is_native,
        cmp_repo(lhs.repository, rhs.repository),
        cmp_user(lhs.user, rhs.user),
    ]

    print(f"cmp_issue: {res}")
    print(f"{lhs.created} == {rhs.created}")
    print(f"{lhs.updated} == {rhs.updated}")

    return all(
        [
            lhs.title == rhs.title,
            lhs.description == rhs.description,
            lhs.repo_scope_id == rhs.repo_scope_id,
            lhs.html_url == rhs.html_url,
            lhs.created == rhs.created,
            lhs.updated == rhs.updated,
            lhs.is_closed == rhs.is_closed,
            lhs.is_merged == rhs.is_merged,
            lhs.is_native == rhs.is_native,
            cmp_repo(lhs.repository, rhs.repository),
            cmp_user(lhs.user, rhs.user),
        ]
    )


def cmp_comment(lhs: DBComment, rhs: DBComment) -> bool:
    assert lhs is not None
    assert rhs is not None

    print(f" lhs: {lhs.id} rhs: {rhs.id}")

    print(
        f"""
        cmp_comment:
        {(
            lhs.body == rhs.body,
            lhs.created == rhs.created,
            lhs.updated == rhs.updated,
            lhs.is_native == rhs.is_native,
            cmp_user(lhs.user, rhs.user),
            cmp_issue(lhs.belongs_to_issue, rhs.belongs_to_issue),
            lhs.comment_id == rhs.comment_id,
            lhs.html_url == rhs.html_url,
            lhs.id == rhs.id
        )}
    """
    )

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
            lhs.id == rhs.id,
        ]
    )


USERNAME = "db_test_user"
PROFILE_URL = f"https://git.batsense.net/{USERNAME}"


def get_user() -> DBUser:
    return DBUser(
        name=USERNAME,
        user_id=USERNAME,
        profile_url=PROFILE_URL,
        avatar_url=PROFILE_URL,
        description="description",
        id=None,
    )


REPO_NAME = "foo"


def get_repo() -> DBRepo:
    owner = get_user()
    #    owner.save()
    return DBRepo(
        name=REPO_NAME,
        owner=owner,
        description="foo",
        html_url=f"{PROFILE_URL}/{REPO_NAME}",
    )


def get_issue(repo_scope_id: int) -> DBIssue:
    title = "Test issue"
    description = "foo bar"
    repo = get_repo()
    #    repo.save()
    user = get_user()
    html_url = f"{repo.html_url}/issues/{repo_scope_id}"
    created = since_epoch()
    updated = since_epoch()
    # repository= repo
    is_closed = False
    is_merged = None
    is_native = True

    return DBIssue(
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


def get_pr(repo_scope_id: int) -> DBIssue:
    pr = get_issue(repo_scope_id)
    pr.title = "test issue PR"
    pr.is_merged = False
    return pr


def get_comment(issue_id: int, comment_id: int) -> DBComment:
    user = get_user()
    issue = get_issue(issue_id)
    #    issue.save()
    comment_body = "test comment"
    comment_url1 = f"{issue.html_url}/{comment_id}"
    return DBComment(
        body=comment_body,
        created=since_epoch(),
        updated=since_epoch(),
        is_native=True,
        belongs_to_issue=issue,
        user=user,
        html_url=comment_url1,
        comment_id=comment_id,
    )
