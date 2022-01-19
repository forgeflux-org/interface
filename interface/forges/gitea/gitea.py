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
import datetime
from urllib.parse import urlunparse, urlparse
from dataclasses import asdict
from dateutil.parser import parse as date_parse

import requests

from rfc3339 import rfc3339
from dynaconf import settings

from interface.forges.base import (
    Forge,
    F_D_REPOSITORY_NOT_FOUND,
    F_D_FORGE_FORBIDDEN_OPERATION,
    F_D_REPOSITORY_EXISTS,
    F_D_INVALID_ISSUE_URL,
)
from interface.forges.payload import (
    CreateIssue,
    RepositoryInfo,
    CreatePullrequest,
    CommentOnIssue,
    ForgeUser,
)
from interface.forges.notifications import Notification, NotificationResp, Comment
from interface.forges.notifications import ISSUE, PULL, COMMIT, REPOSITORY
from interface.error import F_D_FORGE_UNKNOWN_ERROR, Error
from interface.utils import trim_url, clean_url, get_rand

from .html_client import HTMLClient
from .utils import get_issue_index, get_owner_repo_from_url, get_issue_html_url
from .responses import GiteaIssue, GiteaComment


class Gitea(Forge):
    html_client: HTMLClient
    gitea_user_id: int

    def __init__(self):  # self, base_url: str, admin_user: str, admin_email):
        self.html_client = HTMLClient()
        super().__init__(settings.GITEA.host)
        self.gitea_user_id = self.get_gitea_user()["id"]

    def _auth(self):
        return {"Authorization": f"token {settings.GITEA.api_key}"}

    def _get_url(self, path: str) -> str:
        prefix = "/api/v1/"
        if path.startswith("/"):
            path = path[1:]

        path = f"{prefix}{path}"
        url = urlunparse((self.host.scheme, self.host.netloc, path, "", "", ""))
        return url

    @staticmethod
    def get_issue(owner: str, repo: str, issue_id) -> GiteaIssue:
        return GiteaIssue.get_issue(owner=owner, repo=repo, issue_id=issue_id)

    @staticmethod
    def get_issue_html_url(owner: str, repo: str, issue_id: str) -> GiteaIssue:
        return get_issue_html_url(owner=owner, repo=repo, issue_id=issue_id)

    @staticmethod
    def get_comments(issue_url: str) -> [GiteaComment]:
        return GiteaComment.from_issue_url(issue_url)

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

        url = self._get_url(f"/repos/{owner}/{repo}/issues")

        headers = self._auth()
        response = requests.request("GET", url, params=query, headers=headers)
        if response.status_code == 200:
            return response.json()
        if response.status_code == 404:
            raise F_D_REPOSITORY_NOT_FOUND
        raise F_D_FORGE_UNKNOWN_ERROR

    @staticmethod
    def get_owner_repo_from_url(url: str) -> (str, str):
        """Get (owner, repo) from repository URL"""
        return get_owner_repo_from_url(url)

    def get_forge_url(self) -> str:
        return urlunparse((self.host.scheme, self.host.netloc, "", "", "", ""))

    def create_issue(self, owner: str, repo: str, issue: CreateIssue):
        """Creates issue on a repository"""
        url = self._get_url(f"/repos/{owner}/{repo}/issues")

        headers = self._auth()
        payload = asdict(issue)
        print(payload)
        response = requests.request("POST", url, json=payload, headers=headers)
        print(f"log: {response.status_code} {response.json()}")
        if response.status_code == 201:
            data = response.json()
            return data["html_url"]
        if response.status_code == 403:
            raise F_D_FORGE_FORBIDDEN_OPERATION
        if response.status_code == 404:
            raise F_D_REPOSITORY_NOT_FOUND
        raise F_D_FORGE_UNKNOWN_ERROR

    def _into_repository(self, data) -> RepositoryInfo:
        info = RepositoryInfo(
            description=data["description"],
            name=data["name"],
            owner=data["owner"]["login"],
            html_url=data["html_url"],
        )
        return info

    def get_repository(self, owner: str, repo: str) -> RepositoryInfo:
        """Get repository details"""
        data = self.get_gitea_repo(owner, repo)
        return self._into_repository(data)

    def create_repository(self, repo: str, description: str):
        url = self._get_url("/user/repos")
        payload = {"name": repo, "description": description}
        headers = self._auth()
        response = requests.request("POST", url, json=payload, headers=headers)
        if response.status_code == 201:
            return
        if response.status_code == 409:
            # TODO: repository with the same name exists  <21-12-21, ATM> #
            raise F_D_REPOSITORY_EXISTS
        raise F_D_FORGE_UNKNOWN_ERROR

    def subscribe(self, owner: str, repo: str):
        url = self._get_url(format(f"/repos/%s/%s/subscription" % (owner, repo)))
        headers = self._auth()
        response = requests.request("PUT", url, headers=headers)
        if response.status_code == 200:
            return
        if response.status_code == 404:
            raise F_D_REPOSITORY_NOT_FOUND
        raise F_D_FORGE_UNKNOWN_ERROR

    def _into_notification(self, n) -> Notification:
        subject = n["subject"]
        notification_type = subject["type"]

        # 2021-12-25: REPOSITORY type notification is only sent out when a
        # repository transfer request is made and the recipient has to confirm
        # it --- irrelevant for us
        if notification_type == REPOSITORY:
            return None

        last_read = n["updated_at"]
        rn = Notification(
            updated_at=last_read,
            type=notification_type,
            title=subject["title"],
            state=subject["state"],
            id=n["id"],
            repo_url=n["repository"]["html_url"],
        )

        if notification_type == PULL:
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
            if rn:
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

    def get_gitea_repo(self, owner: str, repo: str):
        """Get repository details"""
        url = self._get_url(f"/repos/{owner}/{repo}")
        response = requests.request("GET", url)
        if response.status_code == 200:
            return response.json()
        if response.status_code == 404:
            raise F_D_REPOSITORY_NOT_FOUND
        raise F_D_FORGE_UNKNOWN_ERROR

    def get_gitea_user(self):
        url = self._get_url("/user")
        headers = self._auth()
        response = requests.request("GET", url, headers=headers)
        if response.status_code == 200:
            return response.json()
        raise Exception(
            f"[ERROR] getting user info. status code: {response.status_code}"
        )

    def get_user(self, name: str) -> ForgeUser:
        url = self._get_url(f"/users/{name}")
        headers = self._auth()
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            username = data["username"]
            name = data["full_name"].strip()
            name = username if len(name) == 0 else name
            profile_url = f"{trim_url(clean_url(settings.GITEA.host))}/{username}"
            avatar_url = data["avatar_url"]
            description = data["description"]
            return ForgeUser(
                name=name,
                user_id=username,
                profile_url=profile_url,
                avatar_url=avatar_url,
                description=description,
            )
        err_msg = f"[ERROR] getting user info. status code: {response.status_code} {response.text}"
        raise Exception(err_msg)

    def fork_inner(self, owner: str, repo: str) -> str:
        """Fork a repository"""
        url = self._get_url(f"/repos/{owner}/{repo}/forks")
        headers = self._auth()
        response = requests.request("POST", url, headers=headers)
        if response.status_code == 202:
            return repo

        if response.status_code == 403:
            raise F_D_FORGE_FORBIDDEN_OPERATION

        if response.status_code == 404:
            raise F_D_REPOSITORY_NOT_FOUND

        if response.status_code == 500:
            data = response.json()
            if "message" in data:
                if "repository is already forked by user" in data["message"]:
                    # TODO: repository already forked
                    raise Exception("Repository already forked by user")

                if "repository is already exists by user" in data["message"]:
                    repo_info = self.get_gitea_repo(owner, repo)
                    rand_name = ""
                    while True:
                        rand_name = f"{repo}-{get_rand(10)}"
                        try:
                            self.get_gitea_repo(settings.GITEA.username, rand_name)
                        except Error as error:
                            if error.errcode == F_D_REPOSITORY_NOT_FOUND.errcode:
                                break
                    self.html_client.fork(
                        repo_info["id"], rand_name, self.gitea_user_id
                    )
                    return rand_name

        raise F_D_FORGE_UNKNOWN_ERROR

    @staticmethod
    def get_issue_index(issue_url: str) -> int:
        return get_issue_index(issue_url)

    def comment_on_issue(self, comment: CommentOnIssue):
        headers = self._auth()
        (owner, repo) = self.get_fetch_remote(comment.issue_url)
        index = self.get_issue_index(comment.issue_url)
        url = self._get_url("/repos/{owner}/{repo}/issues/{index}")
        payload = {"body": comment.body}
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
