# Interface ---  API-space federation for software forges
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
import pytest

from interface.forges.gitea.utils import get_issue_index
from interface.error import Error
from interface.forges.base import F_D_INVALID_ISSUE_URL


from tests.test_errors import pytest_expect_errror
from tests.forges.gitea.test_utils import GITEA_HOST


def test_get_issue_index():
    owner = "realaravinth"
    repo = "tmp"

    issues = [
        (f"{GITEA_HOST}/{owner}/{repo}/issues/8", 8),
        (f"{GITEA_HOST}/{owner}/{repo}/issues/8/", 8),
        (f"{GITEA_HOST}/{owner}/{repo}/issues/9/foo/bar/baz", 9),
    ]

    for (url, index) in issues:
        assert get_issue_index(url, repo) == index

    not_issues = [
        f"{GITEA_HOST}/{owner}/{repo}/8",
        f"{GITEA_HOST}/{owner}/{repo}/issues/foo",
        f"{GITEA_HOST}/{owner}/{repo}/issues/foo/bar/baz",
        f"{GITEA_HOST}/{owner}/{repo}/issues/",
    ]
    for url in not_issues:
        with pytest.raises(Error) as error:
            get_issue_index(url, repo)
        assert pytest_expect_errror(error, F_D_INVALID_ISSUE_URL)
