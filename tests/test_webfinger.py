# Interface ---  API-space federation for software forges
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
import json
from interface.app import create_app
from interface.db import INTERFACE_DOMAIN, DBUser, DBRepo
from interface.webfinger import JRD_JSON
from interface.git import get_issue, get_user, get_repo

from .forges.gitea.test_utils import (
    REPOSITORY_NAME,
    REPOSITORY_OWNER,
    ISSUE_URL,
    SINGLE_ISSUE,
    NON_EXISTENT,
)


def test_get_webfinger(client, requests_mock):
    """Test webfinger route"""

    assert INTERFACE_DOMAIN != "example.com"  # Please change domain settings

    for x in [
        f"?resource=acct:{REPOSITORY_OWNER}@example.com",
        f"?resource=acct:{REPOSITORY_OWNER}{INTERFACE_DOMAIN}",
        f"?resource={REPOSITORY_OWNER}{INTERFACE_DOMAIN}",
        f"?resource=!foo!bar!baz@{INTERFACE_DOMAIN}",
        f"?resource=!foo!bar!baz!foo!bar!baz@{INTERFACE_DOMAIN}",
        "",
    ]:
        resp = client.get(f"/.well-known/webfinger{x}")
        assert resp.status_code == 400

    user = get_user(REPOSITORY_OWNER)
    repo = get_repo(REPOSITORY_OWNER, REPOSITORY_NAME)
    issue = get_issue(REPOSITORY_OWNER, REPOSITORY_NAME, SINGLE_ISSUE["number"])
    for actor in [user, issue, repo]:
        resp = client.get(
            f"/.well-known/webfinger?resource={actor.webfinger_subject()}"
        )
        data = resp.json
        assert data == json.loads(json.dumps(actor.webfinger()))
        assert resp.status_code == 200
        assert resp.headers["Content-Type"] == JRD_JSON
