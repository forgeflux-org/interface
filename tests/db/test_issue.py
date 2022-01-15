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

import pytest

from interface.db import get_db
from interface.db.interfaces import DBInterfaces
from interface.db.repo import DBRepo
from interface.db.issues import DBIssue, OPEN, MERGED, CLOSED
from interface.db.users import DBUser

from .test_interface import cmp_interface
from .test_repo import cmp_repo
from .test_user import cmp_user


def cmp_issue(lhs: DBIssue, rhs: DBIssue) -> bool:
    assert lhs is not None
    assert rhs is not None

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
            cmp_interface(lhs.signed_by, rhs.signed_by),
        ]
    )


def test_issue(client):
    """Test user route"""

    # first interface data
    interface_url1 = "https://db-test-issue.example.com"
    interface1 = DBInterfaces(url=interface_url1)

    # second interface data
    interface_url2 = "https://db-test-issue2.example.com"
    interface2 = DBInterfaces(url=interface_url2)

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
        signed_by=interface1,
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
    assert DBIssue.load(repository=repo, repo_scope_id=repo_scope_id) is None
    assert DBIssue.load_with_html_url(html_url=html_url) is None
    assert DBIssue.load_with_id(db_id=11) is None

    issue.save()

    pr_repo_scope_id = 2
    html_url_of_pr = (
        f"https://git.batsense/{user.user_id}/{repo_name}/issues/{pr_repo_scope_id}"
    )
    pr = DBIssue(
        title="test issue PR",
        description=description,
        html_url=html_url_of_pr,
        created=created,
        updated=updated,
        repo_scope_id=pr_repo_scope_id,
        repository=repo,
        user=user,
        signed_by=interface2,
        is_closed=is_closed,
        is_merged=False,
        is_native=is_native,
    )

    pr.save()

    pr_from_db = DBIssue.load(repo, repo_scope_id=pr_repo_scope_id)
    assert cmp_issue(pr, pr_from_db) is True

    issue_from_db = DBIssue.load(repo, repo_scope_id=repo_scope_id)
    with_id = DBIssue.load_with_id(issue_from_db.id)
    with_html_url = DBIssue.load_with_html_url(html_url)
    assert cmp_issue(issue_from_db, issue) is True
    assert cmp_issue(issue_from_db, with_id) is True
    assert cmp_issue(issue_from_db, with_html_url) is True

    # testing states and updates
    db_stored_id = issue_from_db.id
    issue = DBIssue.load_with_id(db_stored_id)
    assert issue.is_pr() is False
    with pytest.raises(TypeError) as e:
        issue.set_merged(str(datetime.now()))

    assert issue.state() == OPEN
    assert issue.is_closed is False
    assert issue.is_merged is None

    # test close issue
    closed_at = str(datetime.now())
    issue.set_closed(closed_at)
    from_db = DBIssue.load_with_id(db_stored_id)
    assert from_db.state() == CLOSED
    assert from_db.updated == closed_at
    assert from_db.is_closed is True
    assert from_db.is_merged is None

    # test open issue
    opened_at = str(datetime.now())
    issue.set_open(opened_at)
    from_db = DBIssue.load_with_id(db_stored_id)
    assert from_db.is_closed is False
    assert from_db.is_merged is None

    ## test PR states

    # is_pr is True
    pr_stored_id = pr_from_db.id
    pr = DBIssue.load_with_id(pr_stored_id)
    assert pr.is_pr() is True

    # merge PR
    merged_at = str(datetime.now())
    pr.set_merged(merged_at)
    assert pr.state() == MERGED
    assert pr.updated == merged_at
    assert pr.is_closed is True
    assert pr.is_merged is True

    # Re-open PR
    opened_at = str(datetime.now())
    pr.set_open(opened_at)
    assert pr.state() == OPEN
    assert pr.updated == opened_at
    assert pr.is_closed is False
    assert pr.is_merged is False

    # Re-open PR
    opened_at = str(datetime.now())
    pr.set_open(opened_at)
    assert pr.state() == OPEN
    assert pr.updated == opened_at
