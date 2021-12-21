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
from dataclasses import asdict
from dateutil.parser import parse as date_parse
from urllib.parse import urlunparse, urlparse
import requests

from rfc3339 import rfc3339
from dynaconf import settings

from .base import (
    Forge,
    F_D_REPOSITORY_NOT_FOUND,
    F_D_FORGE_FORBIDDEN_OPERATION,
    F_D_REPOSITORY_EXISTS,
)
from .payload import CreateIssue, RepositoryInfo, CreatePullrequest
from .notifications import Notification, NotificationResp, Comment
from .notifications import ISSUE, PULL, COMMIT, REPOSITORY
from interface.error import F_D_FORGE_UNKNOWN_ERROR


class Gitea(Forge):
    def __init__(self):  # self, base_url: str, admin_user: str, admin_email):
        super().__init__(settings.GITEA.host)

    def _auth(self):
        return {"Authorization": format("token %s" % (settings.GITEA.api_key))}

    def _get_url(self, path: str) -> str:
        prefix = "/api/v1/"
        if path.startswith("/"):
            path = path[1:]

        path = format("%s%s" % (prefix, path))
        url = urlunparse((self.host.scheme, self.host.netloc, path, "", "", ""))
        return url

    def get_issues(
        self, owner: str, repo: str, since: datetime.datetime = None, *args, **kwargs
    ):
        """Get issues on a repository. Supports pagination via 'page' optional param"""
        query = {}
        if since is not None:
            query["since"] = rfc3339(since)

        page = kwargs.get("page")
        if page is not None:
            query["page"] = page

        url = self._get_url(format("/repos/%s/%s/issues" % (owner, repo)))

        headers = self._auth()
        response = requests.request("GET", url, params=query, headers=headers)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            raise F_D_REPOSITORY_NOT_FOUND
        else:
            raise F_D_FORGE_UNKNOWN_ERROR

    def get_owner_repo_from_url(self, url: str) -> (str, str):
        """Get (owner, repo) from repository URL"""
        url = self.get_fetch_remote(url)
        parsed = urlparse(url)
        details = parsed.path.split("/")[1:3]
        (owner, repo) = (details[0], details[1])
        return (owner, repo)

    def get_forge_url(self) -> str:
        return urlunparse((self.host.scheme, self.host.netloc, "", "", "", ""))

    def create_issue(self, owner: str, repo: str, issue: CreateIssue):
        """Creates issue on a repository"""
        url = self._get_url(format("/repos/%s/%s/issues" % (owner, repo)))

        headers = self._auth()
        payload = asdict(issue)
        print(payload)
        response = requests.request("POST", url, json=payload, headers=headers)
        print(f"log: {response.status_code} {response.json()}")
        if response.status_code == 201:
            data = response.json()
            return data["html_url"]
        elif response.status_code == 403:
            raise F_D_FORGE_FORBIDDEN_OPERATION
        elif response.status_code == 404:
            raise F_D_REPOSITORY_NOT_FOUND
        else:
            raise F_D_FORGE_UNKNOWN_ERROR

    def _into_repository(self, data) -> RepositoryInfo:
        info = RepositoryInfo(
            description=data["description"],
            name=data["name"],
            owner=data["owner"]["login"],
        )
        return info

    def get_repository(self, owner: str, repo: str) -> RepositoryInfo:
        """Get repository details"""
        url = self._get_url(format("/repos/%s/%s" % (owner, repo)))
        response = requests.request("GET", url)
        if response.status_code == 200:
            data = response.json()
            info = self._into_repository(data)
            return info
        elif response.status_code == 404:
            raise F_D_REPOSITORY_NOT_FOUND
        else:
            raise F_D_FORGE_UNKNOWN_ERROR

    def create_repository(self, repo: str, description: str):
        url = self._get_url("/user/repos")
        payload = {"name": repo, "description": description}
        headers = self._auth()
        response = requests.request("POST", url, json=payload, headers=headers)
        if response.status_code == 201:
            return
        elif response.status_code == 409:
            # TODO: repository with the same name exists  <21-12-21, ATM> #
            raise F_D_REPOSITORY_EXISTS
        else:
            raise F_D_FORGE_UNKNOWN_ERROR

    def subscribe(self, owner: str, repo: str):
        url = self._get_url(format("/repos/%s/%s/subscription" % (owner, repo)))
        headers = self._auth()
        _response = requests.request("PUT", url, headers=headers)

    def _into_notification(self, n) -> Notification:
        subject = n["subject"]
        notification_type = subject["type"]

        last_read = n["updated_at"]
        rn = Notification(
            updated_at=last_read,
            type=notification_type,
            title=subject["title"],
            state=subject["state"],
            id=n["id"],
            repo_url=n["repository"]["html_url"],
        )

        if notification_type == REPOSITORY:
            print(n)

        elif notification_type == PULL:
            rn.pr_url = requests.request("GET", subject["url"]).json()["html_url"]

            rn.upstream = n["repository"]["description"]
            print(n["repository"]["description"])

        elif notification_type == ISSUE:
            comment_url = subject["latest_comment_url"]
            print(comment_url)
            if len(comment_url) != 0:
                resp = requests.request("GET", comment_url)
                comment = resp.json()

                url = ""
                pr_url = comment["pull_request_url"]
                if len(comment["pull_request_url"]) == 0:
                    url = comment["issue_url"]
                else:
                    url = pr_url

                c = Comment(
                    updated_at=comment["updated_at"],
                    author=comment["user"]["login"],
                    id=comment["id"],
                    body=comment["body"],
                    url=url,
                )

                rn.comment = c
        return rn

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
        resp = []

        for n in notifications:
            # rn: Repository Notification
            rn = self._into_notification(n)
            last_read = rn.updated_at
            resp.append(rn)
        return NotificationResp(notifications=resp, last_read=date_parse(last_read))

    def create_pull_request(self, owner: str, repo: str, pr: CreatePullrequest):
        url = self._get_url(format("/repos/%s/%s/pulls" % (owner, repo)))
        headers = self._auth()

        payload = asdict(pr)
        for key in ["repo", "owner"]:
            del payload[key]

        payload["assignees"] = []
        payload["labels"] = [0]
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
        path = f"/{settings.GITEA.username}/{repo}"
        return urlunparse((self.host.scheme, self.host.netloc, path, "", "", ""))

    def get_local_push_url(self, repo: str) -> str:
        return f"git@{self.host.netloc}:{settings.GITEA.username}/{repo}.git"


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
