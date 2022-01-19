"""
Gitea-specific utilities
"""
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
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from urllib.parse import urlparse

from dynaconf import settings

from interface.utils import trim_url
from interface.forges.base import F_D_INVALID_ISSUE_URL


def get_issue_index(issue_url) -> int:
    """
    Get issue index from issue URL
    https://git.batsense.net/{owner}/{repo}/issues/{id} returns {id}
    """
    issue_frag = "issues/"
    if issue_frag not in issue_url:
        raise F_D_INVALID_ISSUE_URL
    parsed = urlparse(trim_url(issue_url))
    path = parsed.path
    fragments = path.split(f"{issue_frag}")
    if len(fragments) < 2:
        raise F_D_INVALID_ISSUE_URL

    index = fragments[1]

    if not index.isdigit():
        if "/" in index:
            index = index.split("/")[0]
            if not index.isdigit():
                raise F_D_INVALID_ISSUE_URL
        else:
            raise F_D_INVALID_ISSUE_URL

    return int(index)


def get_owner_repo_from_url(url: str) -> (str, str):
    """Get (owner, repo) from repository URL"""
    parsed = urlparse(url)
    details = parsed.path.split("/")[1:3]
    (owner, repo) = (details[0], details[1])
    return (owner, repo)


def get_issue_html_url(owner: str, repo: str, issue_id) -> str:
    """issue HTML URL from compoenents"""
    return f"{settings.GITEA.host}/{owner}/{repo}/issues/{issue_id}"


def get_issue_api_url(owner: str, repo: str, issue_id) -> str:
    """issue API URL from compoenents"""
    return f"{settings.GITEA.host}/api/v1/repos/{owner}/{repo}/issues/{issue_id}"
