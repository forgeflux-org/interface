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
import datetime
from dateutil.parser import parse as date_parse
from urllib.parse import urlunparse, urlparse
import requests

from rfc3339 import rfc3339
from interface import local_settings

from .base import Forge
from .payload import CreateIssue, RepositoryInfo, CreatePullrequest
from .notifications import Notification, NotificationResp, Comment
from .notifications import ISSUE, PULL, COMMIT, REPOSITORY


class Gitea(Forge):
    def __init__(self):  # self, base_url: str, admin_user: str, admin_email):
        super().__init__(local_settings.GITEA_HOST)

    def _auth(self):
        return {"Authorization": format("token %s" % (local_settings.GITEA_API_KEY))}

    def _get_url(self, path: str) -> str:
        prefix = "/api/v1/"
        if path.startswith("/"):
            path = path[1:]

        path = format("%s%s" % (prefix, path))
        url = urlunparse((self.host.scheme, self.host.netloc, path, "", "", ""))
        return url

    def get_issues(self, owner: str, repo: str, *args, **kwargs):
        """Get issues on a repository. Supports pagination via 'page' optional param"""
        query = {}
        since = kwargs.get("since")
        if since is not None:
            query["since"] = since

        page = kwargs.get("page")
        if page is not None:
            query["page"] = page

        url = self._get_url(format("/repos/%s/%s/issues" % (owner, repo)))

        headers = self._auth()
        response = requests.request("GET", url, params=query, headers=headers)
        return response.json()

    def get_forge_url(self) -> str:
        return urlunparse((self.host.scheme, self.host.netloc, "", "", "", ""))

    def create_issue(self, owner: str, repo: str, issue: CreateIssue):
        """Creates issue on a repository"""
        url = self._get_url(format("/repos/%s/%s/issues" % (owner, repo)))

        headers = self._auth()
        payload = issue.get_payload()
        response = requests.request("POST", url, json=payload, headers=headers)
        data = response.json()
        return data["html_url"]

    def _into_repository(self, data) -> RepositoryInfo:
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
        return info

    def create_repository(self, repo: str, description: str):
        url = self._get_url("/user/repos/")
        payload = {"name": repo, "description": description}
        headers = self._auth()
        _response = requests.request("POST", url, json=payload, headers=headers)

    def subscribe(self, owner: str, repo: str):
        url = self._get_url(format("/repos/%s/%s/subscription" % (owner, repo)))
        headers = self._auth()
        _response = requests.request("PUT", url, headers=headers)

    def get_notifications(self, since: datetime.datetime) -> NotificationResp:
        # Setting up a simple query object
        query = {}
        query["since"] = rfc3339(since)
        print("Checking type : ", type(query["since"]))

        # Sending a request for a JSON notifications response
        # to the notifications section
        url = self._get_url("/notifications")
        headers = self._auth()
        response = requests.request("GET", url, params=query, headers=headers)
        notifications = response.json()

        # Setting last_read to a string
        # to be parsed into a datetime
        last_read = query["since"]
        val = []

        for n in notifications:
            # rn: Repository Notification
            rn = Notification()
            subject = n["subject"]
            notification_type = subject["type"]

            # Setting up data for the object
            last_read = n["updated_at"]
            rn.set_updated_at(last_read)
            rn.set_type(notification_type)
            rn.set_title(subject["title"])
            rn.set_state(subject["state"])
            rn.set_repo_url(n["repository"]["html_url"])

            if notification_type == REPOSITORY:
                print(n)
            if notification_type == PULL:
                rn.set_pr_url(
                    requests.request("GET", subject["url"]).json()["html_url"]
                )
                rn.set_upstream(n["repository"]["description"])
                print(n["repository"]["description"])

            if notification_type == ISSUE:
                comment_url = subject["latest_comment_url"]
                print(comment_url)
                if len(comment_url) != 0:
                    resp = requests.request("GET", comment_url)
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
            val.append(rn)
        return NotificationResp(val, date_parse(last_read))

    def create_pull_request(self, owner: str, repo: str, pr: CreatePullrequest):
        url = self._get_url(format("/repos/%s/%s/pulls" % (owner, repo)))
        headers = self._auth()

        payload = pr.get_payload()
        for key in ["repo", "owner"]:
            del payload[key]

        payload["assignees"] = []
        payload["lables"] = [0]
        payload["milestones"] = 0

        response = requests.request("POST", url, json=payload, headers=headers)
        return response.json()["html_url"]

    def fork(self, owner: str, repo: str):
        """Fork a repository"""
        url = self._get_url(format("/repos/%s/%s/forks" % (owner, repo)))
        print(url)
        headers = self._auth()
        payload = {"oarganization": "bot"}
        _response = requests.request("POST", url, json=payload, headers=headers)

    def get_issue_index(self, issue_url, owner: str) -> int:
        parsed = urlparse(issue_url)
        path = parsed.path
        path.endswith("/")
        if path.endswith("/"):
            path = path[0:-1]
        index = path.split(owner)[0].split("issue")[2]
        if index.startswith("/"):
            index = index[1:]

        if index.endswith("/"):
            index = index[0:-1]

        return int(index)

    def comment_on_issue(self, owner: str, repo: str, issue_url: str, body: str):
        headers = self._auth()
        (owner, repo) = self.get_fetch_remote(issue_url)
        index = self.get_issue_index(issue_url, owner)
        url = self._get_url(format("/repos/%s/%s/issues/%s" % (owner, repo, index)))
        payload = {"body": body}
        _response = requests.request("POST", url, json=payload, headers=headers)

    def get_local_html_url(self, repo: str) -> str:
        path = format("/%s/%s" % local_settings.GITEA_USERNAME, repo)
        return urlunparse((self.host.scheme, self.host.netloc, path, "", "", ""))

    def get_local_push_url(self, repo: str) -> str:
        return format(
            "git@%s:%s/%s.git" % (self.host.netloc, local_settings.GITEA_USERNAME, repo)
        )


# if __name__ == "__main__":
#    owner = "realaravinth"
#    repo = "tmp"
#    g = Gitea()
#    issue = CreateIssue()
#    issue.set_title("from lib")
#    #print(g.create_issue(owner, repo, issue))
#    print(g.get_repository(owner, repo))
#    g.create_repository("tmp", "lib created")
#    g.subscribe("bot", "tmp")
#    g.subscribe("realaravinth", "tmp")
#    notifications = g.get_notifications(since=date_parse("2021-10-10T17:06:02+05:30"))
#    import json
#    print(json.dumps(notifications.get_payload()))
#    pr = CreatePullrequest()
#    pr.set_base("master")
#    pr.set_body("PR body")
#    pr.set_title("demo pr from lib")
#    pr.set_owner("realaravinth")
#    pr.set_repo("tmp")
#    pr.set_head("bot:master-fork")
#    print(g.create_pull_request(pr))
#    g.fork(owner, repo)
