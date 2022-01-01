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
from html.parser import HTMLParser
from dataclasses import asdict
from dateutil.parser import parse as date_parse
from urllib.parse import urlunparse, urlparse
import requests
from requests import Session
from requests.auth import HTTPBasicAuth

from rfc3339 import rfc3339
from dynaconf import settings

from interface.forges.base import (
    Forge,
    F_D_REPOSITORY_NOT_FOUND,
    F_D_FORGE_FORBIDDEN_OPERATION,
    F_D_REPOSITORY_EXISTS,
    F_D_INVALID_ISSUE_URL,
)
from interface.forges.payload import CreateIssue, RepositoryInfo, CreatePullrequest
from interface.forges.notifications import Notification, NotificationResp, Comment
from interface.forges.notifications import ISSUE, PULL, COMMIT, REPOSITORY
from interface.error import F_D_FORGE_UNKNOWN_ERROR, Error
from interface.utils import trim_url, clean_url, get_rand


class ParseCSRFGiteaForm(HTMLParser):
    token: str = None

    def handle_starttag(self, tag: str, attrs: (str, str)):
        if self.token:
            return

        if tag != "input":
            return

        token = None
        for (index, (k, v)) in enumerate(attrs):
            if k == "value":
                token = v

            if all([k == "name", v == "_csrf"]):
                if token:
                    self.token = token
                    return
                for (inner_index, (nk, nv)) in enumerate(attrs, start=index):
                    if nk == "value":
                        self.token = nv
                        return


class HTMLClient:
    session: Session

    def __init__(self):
        self.host = urlparse(clean_url(settings.GITEA.host))
        if all([self.host.scheme != "http", self.host.scheme != "https"]):
            print(self.host.scheme)
            raise Exception("scheme should be either http or https")
        self.session = Session()
        self.login()
        print(f"constructor {self.session.cookies}")

    @staticmethod
    def get_csrf_token(page: str) -> str:
        parser = ParseCSRFGiteaForm()
        parser.feed(page)
        csrf = parser.token
        return csrf

    def get_url(self, path: str) -> str:
        return urlunparse((self.host.scheme, self.host.netloc, path, "", "", ""))

    def login(self):
        url = self.get_url("/user/login")
        resp = self.session.get(url)
        if resp.status_code != 200:
            print(resp.status_code, resp.text)
            raise Exception(resp.status_code)

        csrf = self.get_csrf_token(resp.text)
        payload = {
            "_csrf": csrf,
            "user_name": settings.GITEA.username,
            "password": settings.GITEA.password,
            "remember": "on",
        }
        resp = self.session.post(url, data=payload, allow_redirects=False)
        print(f"login {self.session.cookies}")
        if resp.status_code == 302:
            return

        raise Exception(
            f"[ERROR] Authentication failed. status code {resp.status_code}"
        )

    def fork(self, repo_id: int, repo_name: str, uid: int):
        url = self.get_url(f"/repo/fork/{repo_id}")
        payload = {
            "uid": uid,
            "repo_name": repo_name,
            "description": "",
        }

        def __inner(payload, count: int = 0):
            print(payload)
            resp = self.session.get(url)
            if resp.status_code != 200:
                # Have to see source code for possible errors(wrong password? user doesn't exist?)
                print(resp.status_code, resp.text)
                raise Exception(resp.status_code)

            csrf = self.get_csrf_token(resp.text)
            payload["_csrf"] = csrf
            print(f"payload in gitea: {payload}")
            resp = self.session.post(url, data=payload, allow_redirects=False)
            if resp.status_code == 302:
                return self.get_url(resp.headers["location"])
            if (
                '<a href="/user/sign_up">Need an account? Register now.</a>'
                in resp.text
            ):
                print("logging in")
                self.login()
                count += 1
                return __inner(count)
            print(resp.text)
            raise Exception(
                f"[ERROR]: CSRF forking repo_id: {repo_id} status: {resp.status_code}"
            )

        return __inner(payload)
