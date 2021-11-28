""" Test interface handlers"""
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
from interface.forges.utils import (
    get_patch,
    get_branch_name,
    get_local_repository_from_foreign_repo,
)

repo_url = "https://github.com/forgefedv2"
pr_url = f"{repo_url}/interface/pull/19"


def test_get_patch(requests_mock):
    """test get patch"""
    patch = "patch"
    requests_mock.get(f"{pr_url}.patch", text=patch)
    assert get_patch(pr_url) == patch

    assert get_patch(f"{pr_url}/") == patch


def test_get_branch_name():
    """test get branch name from PR url"""
    assert get_branch_name(pr_url) == "github.com-forgefedv2-interface-pull-19"


def test_get_local_repository_from_foreign_repo():
    """test get local repository name foreign repo url"""

    assert get_local_repository_from_foreign_repo(repo_url) == "github.com-forgefedv2"
    assert (
        get_local_repository_from_foreign_repo(f"{repo_url}/")
        == "github.com-forgefedv2"
    )
