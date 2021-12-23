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

from dynaconf import settings

from interface.git import Git, get_forge

from tests.test_utils import register_ns
from tests.forges.gitea.test_utils import register_gitea


UPSTREAM = "https://github.com/realaravinth/actix-auth-middleware"


def test_git(app, client, requests_mock):
    """Test git module"""

    register_ns(requests_mock)
    register_gitea(requests_mock)
    git = get_forge()


#    git.git_clone(UPSTREAM)
