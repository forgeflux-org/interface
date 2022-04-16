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

from interface.db.comments import DBComment
from interface.db.cache import CACHE_TTL

from .utils import cmp_comment, get_comment


def test_comment(client):
    """Test user route"""

    # create comment 1
    repo_scope_id = 99
    comment_id1 = 1
    comment1 = get_comment(issue_id=repo_scope_id, comment_id=comment_id1)
    assert DBComment.load_issue_comments(comment1.belongs_to_issue) is None
    assert DBComment.load_from_comment_url(comment1.html_url) is None

    # check comment count, should be 0 as none exists
    assert DBComment.count.count() == 0

    comment1.save()

    # check comment count, should be 0 as one exists but cache hasn't expired yet
    assert DBComment.count.count() == 0

    # sleep till cache TTL and check comment count, should b 1
    time.sleep(CACHE_TTL * 2)
    assert DBComment.count.count() == 1
    assert comment1.id is not None

    # create comment 2
    comment_id2 = 2
    comment2 = get_comment(issue_id=repo_scope_id + 1, comment_id=comment_id2)
    comment2.save()

    comments = DBComment.load_issue_comments(comment1.belongs_to_issue)
    for dbcomment in comments:
        from_url = DBComment.load_from_comment_url(dbcomment.html_url)
        assert cmp_comment(dbcomment, from_url)
        if dbcomment.comment_id == comment1.comment_id:
            assert cmp_comment(comment1, dbcomment)
        else:
            assert cmp_comment(comment2, dbcomment)
