""" Test interface handlers"""
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
from datetime import datetime
from urllib.parse import urlparse, urlunparse

import pytest
from dynaconf import settings

from interface.forges.base import Forge
from interface.forges.payload import (
    CreateIssue,
    CreatePullrequest,
    Author,
    RepositoryInfo,
    MetaData,
    CommentOnIssue,
)


class BasicForge(Forge):
    def __init__(self):
        super().__init__(settings.GITEA.host)

    def get_forge_url(self) -> str:
        return urlunparse((self.host.scheme, self.host.netloc, "", "", "", ""))


def test_base_forge():
    """test Forge"""

    author = Author(
        name="Author",
        fqdn_username="author@example.com",
        profile_url="https://example.com",
    )

    meta = MetaData(html_url="", author=author, interface_url="")
    repo = (
        RepositoryInfo(
            name="",
            owner="",
            description="",
            html_url="",
        ),
    )

    with pytest.raises(Exception) as _:
        Forge("ssh://git@foo:x")

    with pytest.raises(Exception) as _:
        Forge("https://git.batsense.net")

    with pytest.raises(Exception) as _:
        f = Forge("https://git.batsense.net")
        f.get_fetch_remote("ftp://example.com")

    forge = BasicForge()

    with pytest.raises(NotImplementedError) as _:
        forge.get_owner_repo_from_url("")

    with pytest.raises(NotImplementedError) as _:
        forge.get_local_html_url("")

    with pytest.raises(NotImplementedError) as _:
        forge.get_local_push_url("")

    with pytest.raises(NotImplementedError) as _:
        forge.get_issues("", "")

    with pytest.raises(NotImplementedError) as _:
        issue = CreateIssue(
            title="",
            body="",
            meta=meta,
            repository=RepositoryInfo(
                name="",
                owner="",
                html_url="",
                description="",
            ),
        )
        forge.create_issue(issue)

    with pytest.raises(NotImplementedError) as _:
        forge.get_repository("", "")

    with pytest.raises(NotImplementedError) as _:
        forge.create_repository("", "")

    with pytest.raises(NotImplementedError) as _:
        forge.subscribe("", "")

    with pytest.raises(NotImplementedError) as _:
        forge.get_notifications(since=datetime.now())

    with pytest.raises(NotImplementedError) as _:
        pr = CreatePullrequest(
            head="",
            base="",
            title="",
            body="",
            meta=meta,
            repository=repo,
        )
        forge.create_pull_request(pr=pr)

    with pytest.raises(NotImplementedError) as _:
        forge.fork_inner("", "")

    with pytest.raises(NotImplementedError) as _:
        forge.close_pr("", "")

    with pytest.raises(NotImplementedError) as _:
        forge.get_notification("")

    with pytest.raises(NotImplementedError) as _:
        comment = CommentOnIssue(meta=meta, body="", repository=repo, issue_url="")
        forge.comment_on_issue(comment)

    with pytest.raises(NotImplementedError) as _:
        forge.get_notification_resolver()

    with pytest.raises(NotImplementedError) as _:
        forge.get_user("")
