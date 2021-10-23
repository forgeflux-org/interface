# Bridges software forges to create a distributed software development environment
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
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from dateutil.parser import parse as date_parse
import datetime
from urllib.parse import urlparse, urlunparse, urlencode
import requests

from rfc3339 import rfc3339

import local_settings
import utils
from forge import CreateIssue, Forge, RepositoryInfo, Comment, Notification, NotificationResp

ISSSUE="Issue"
PULL ="pull"
COMMIT = "commit"
REPOSITORY = "repository"

class Gitea(Forge):
    def __init__(self):
        self.host = urlparse(utils.clean_url(local_settings.GITEA_HOST))

    def _auth(self):
        return {'Authorization': format("token %s" % (local_settings.GITEA_API_KEY))}

    def _get_url(self, path: str) -> str:
        prefix = "/api/v1/"
        if path.startswith('/'):
            path=path[1:]

        path = format("%s%s" % (prefix, path))
        url = urlunparse((self.host.scheme, self.host.netloc, path, "", "", ""))
        return url

    def get_issues(self, owner: str, repo: str, *args, **kwargs):
        """ Get issues on a repository. Supports pagination via 'page' optional param"""
        query = {}
        since = kwargs.get('since')
        if since is not None:
            query["since"] = since

        page = kwargs.get('page')
        if page is not None:
            query["page"] = page

        url = self._get_url(format("/repos/%s/%s/issues" % (owner, repo)))

        headers = self._auth()
        payload = {}
        response = requests.request("GET", url, params=query, headers=headers)
        return response.json()

    def create_issue(self, owner: str, repo: str, issue: CreateIssue):
        """ Creates issue on a repository"""
        url = self._get_url(format("/repos/%s/%s/issues" % (owner, repo)))

        headers = self._auth()
        payload = issue.get_payload()
        response = requests.request("POST", url, json=payload, headers=headers)
        return response.json()

    def _into_repository(self, data) -> RepositoryInfo:
        info = RepositoryInfo()
        info.set_description(data["description"])
        info.set_name(data["name"])
        info.set_owner_name(data["owner"]["login"])
        return info

    def get_repository(self, owner: str, repo: str) -> RepositoryInfo:
        """ Get repository details"""
        url = self._get_url(format("/repos/%s/%s" % (owner, repo)))
        response = requests.request("GET", url)
        data = response.json();
        info = self._into_repository(data)
        return info.get_payload()

    def create_repository(self, repo: str, description: str):
        url = self._get_url("/user/repos/")
        payload = { "name" : repo, "description": description}
        headers = self._auth()
        _response = requests.request("POST", url, json=payload, headers=headers)

    def subscribe(self, owner: str, repo: str):
        url = self._get_url(format("/repos/%s/%s/subscription" % (owner, repo)))
        headers = self._auth()
        _response = requests.request("PUT", url, headers=headers)


    def get_notifications(self, since: datetime.datetime) -> NotificationResp:
        query = {}
        query["since"] =  rfc3339(since)
        url = self._get_url("/notifications")
        headers = self._auth()
        response = requests.request("GET", url, params=query, headers=headers)
        notifications = response.json()
        last_read = ""
        resp = []
        for n in notifications:
            # resp notification
            rn = Notification()
            subject = n["subject"]
            notification_type = subject["type"]

            last_read = n["updated_at"]
            rn.set_updated_at(last_read)
            rn.set_type(notification_type)
            rn.set_title(subject["title"])
            rn.set_state(subject["state"])

            if notification_type == REPOSITORY:
                print(n)
            if notification_type == ISSSUE:
                comment_url = subject["latest_comment_url"]
                print(comment_url)
                if len(comment_url) != 0:
                    resp = requests.request("GET", comment_url);
                    comment = resp.json()
                    if date_parse(comment["updated_at"]) > since:
                        c = Comment()
                        c.set_updated_at(comment["updated_at"])
                        c.set_author(comment["user"]["login"])
                        c.set_body(comment["body"])
                        pr_url = comment["pull_request_url"]
                        if len(comment["pull_request_url"]) == 0:
                            c.set_url(comment["issue_url"])
                        else:
                            url = pr_url
                            c.set_url(comment["pull_request_url"])
                        rn.set_comment(c)
            resp.append(rn)
        return NotificationResp(resp, date_parse(last_read))

                
if __name__ == "__main__":
    owner = "realaravinth"
    repo = "tmp"
    g = Gitea()
    issue = CreateIssue()
    issue.set_title("from lib")
    #print(g.create_issue(owner, repo, issue))
#    print(g.get_repository(owner, repo))
#    g.create_repository("tmp", "lib created")
#    g.subscribe("bot", "tmp")
#    g.subscribe("realaravinth", "tmp")
    g.get_notifications(since=date_parse("2021-10-10T17:06:02+05:30"))
