# Bridges software forges to create a distributed software development environment
# Copyright © 2021 G V Datta Adithya <dat.adithya@gmail.com>
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

from urllib.parse import urlparse, urlunparse
import requests
import sys

sys.path.append("..")
import local_settings
import utils
from forge import Forge, CreateIssue, RepositoryInfo, NotificationResp


class GitHub(Forge):
    def __init__(self):
        """Initializes the class variables"""
        self.host = urlparse(utils.clean_url(local_settings.GITHUB_HOST))

    def _get_url(self, path: str) -> str:
        """Retrieves the forge url"""
        if path.startswith("/"):
            path = path[1:]

        url = urlunparse((self.host.scheme, self.host.netloc, path, "", "", ""))
        return url

    def _auth(self):
        """Authorizes the request with a token"""
        return {"Authorization": format("token %s" % (local_settings.GITHUB_API_KEY))}

    def get_issues(self, owner: str, repo: str, *args, **kwargs):
        """Get the issues present in a provided repository"""

        # Defining a formatted url with the repo details
        url = format("https://api.github.com/repos/%s/%s/issues" % (owner, repo))

        # Requesting the issues present in the repo
        # GitHub provides a paginated response for 30
        # issues at a time
        response = requests.request("GET", url)

        # returning the responses in the form of JSON
        return response.json()

    def create_issue(self, owner: str, repo: str, issue: CreateIssue):
        """Creates an issue on a repository"""
        url = self._get_url(format("/repos/%s/%s/issues" % (owner, repo)))

        # Defining authorization headers and a payload
        headers = self._auth()
        payload = issue.get_payload()

        # Sending in a POST request
        response = requests.request("POST", url, json=payload, headers=headers)

        # Returns the response with a JSON output
        return response.json()

    def _into_repository(self, data) -> RepositoryInfo:
        """Getting and setting data"""

        info = RepositoryInfo()
        info.set_description(data["description"])
        info.set_name(data["name"])
        info.set_owner_name(data["owner"]["login"])
        return info

    def get_repository(self, owner: str, repo: str) -> RepositoryInfo:
        """Get repository details"""

        url = self._get_url(format("/repos/%s/%s" % (owner, repo)))
        response = requests.request("GET", url)
        data = response.json()
        info = self._into_repository(data)
        print("Payload deets", info.get_payload())
        return info

    def create_repository(self, repo: str, description: str):
        """Creates a repository in the users forge"""
        url = self._get_url("/users/repos/")
        payload = {"name": repo, "description": description}
        headers = self._auth()
        _response = requests.request("POST", url, json=payload, headers=headers)

    def subscribe(self, owner: str, repo: str):
        """Subscribes/watches a repository"""
        url = self._get_url(format("/repos/%s/%s/subscription" % (owner, repo)))
        headers = self._auth()
        _response = requests.request("PUT", url, headers=headers)

    def get_notifications(self, since: datetime.datetime) -> NotificationResp:
        """Notifications for watched repositories"""
        return "ToBeImplemented"


if __name__ == "__main__":
    # Testing the API primitively with a simple call
    owner = "dat-adi"
    repo = "tmp"
    g = GitHub()
    issue = CreateIssue()
    issue.set_title("testing yet again")
    print(g.create_issue(owner, repo, issue))
    print(
        g._into_repository(
            {
                "name": "G V Datta Adithya",
                "description": "Octowhat?",
                "owner": {"login": "userwhat?"},
            }
        )
    )
