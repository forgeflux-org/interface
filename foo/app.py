from rfc3339 import rfc3339
import datetime
import requests
from urllib.parse import urlparse, urlunparse
from dateutil.parser import parse as date_parse
import logging
import sched
import threading
import time
import datetime



from flask import Blueprint, jsonify, request, Flask
#from interface import FORGE

#from interface.db import get_db
#from interface.client import get_client, GET_REPOSITORY, GET_REPOSITORY_INFO
#from interface.client import SUBSCRIBE, COMMENT_ON_ISSUE, CREATE_ISSUE
#from interface.client import FORK_FOREIGN, FORK_LOCAL


import libgit as forge_libgit


from flask import current_app, g

#from interface.utils import clean_url, get_branch_name, get_patch
#from interface.forges.gitea import Gitea
#from interface import local_settings
#from interface import utils

import local_settings


import sqlite3
import os

import click
from flask import current_app, g
from flask.cli import with_appcontext
from yoyo import read_migrations
from yoyo import get_backend

def get_patch(url: str) -> str:
    """ Get patch from pull request"""
    if url.endswith('/'):
        url = url[0:-1] + ".patch"
    else:
        url += ".patch"
    resp = requests.get(url)
    if resp.status_code == 200:
        print("patch", resp.text)
        return resp.text

def clean_url(url: str):
    """Remove paths and tracking elements from URL"""
    parsed = urlparse(url)
    cleaned = urlunparse((parsed.scheme, parsed.netloc, "", "", "", ""))
    return cleaned

def get_branch_name(pull_request_url: str) -> str:
    """ Get branch name from pull request URL """
    parsed = urlparse(pull_request_url)
    return format("%s%s" % (parsed.netloc, parsed.path.replace("/", "-")))

def get_local_repository_from_foreign_repo(repo_url: str) -> str:
    return get_branch_name(repo_url)

def get_db() -> sqlite3.Connection:
    """Get database connection"""
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE"], detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop("db", None)

    if db is not None:
        db.close()

def init_db():
    """Apply database migrations"""
    db = str.format("sqlite:///%s" % (current_app.config["DATABASE"]))
    backend = get_backend(db)
    migrations = read_migrations("./migrations/")
    with backend.lock():
        backend.apply_migrations(backend.to_apply(migrations))
        backend.commit()

@click.command("migrate")
@with_appcontext
def migrate_db_command():
    """Apply database migrations CLI handler"""
    init_db()
    click.echo("Migrations applied")


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(migrate_db_command)


ISSSUE="Issue"
PULL ="Pull"
COMMIT = "commit"
REPOSITORY = "repository"

class Payload:
    """ Payload base class. self.mandatory should be defined"""
    def __init__(self, mandatory: [str]):
        self.payload = {}
        self.mandatory = []

    def get_payload(self):
        """ get payload """
        for f in self.mandatory:
            if self.payload[f] is None:
                raise Exception("%s can't be empty" % f)
        return self.payload

class RepositoryInfo(Payload):
    """ Describes a repository"""
    def __init__(self):
        mandatory = ["name", "owner_name"]
        super().__init__(mandatory)

    def set_name(self, name):
        """ Set name of repository"""
        self.payload["name"] = name

    def set_owner_name(self, name):
        """ Set owner name of repository"""
        self.payload["owner_name"] = name

    def set_description(self, description):
        """ Is this a template repository"""
        self.payload["description"] = description

class CreateIssue(Payload):
    """ Create new issue payload"""
    def __init__(self):
        mandatory = ["title"]
        super().__init__(mandatory)

    def set_title(self,title):
        """ set issue title"""
        self.payload["title"] = title

    def set_body(self,body):
        """ set issue body"""
        self.payload["body"] = body

    def set_due_date(self, due_date):
        """ set issue due date"""
        self.payload["due_date"] = due_date

    def set_closed(self, closed: bool):
        """ set issue open status"""
        self.payload["closed"] = closed

class Comment(Payload):
    def __init__(self):
        mandatory = ["body", "author", "updated_at", "url"]
        super().__init__(mandatory)

    def set_updated_at(self,date):
        """ set comment update time"""
        self.payload["updated_at"] = date

    def set_body(self,body):
        """ set issue body"""
        self.payload["body"] = body

    def set_author(self, author):
        """ set issue author"""
        self.payload["author"] = author

    def set_url(self, url):
        """ set url of comment"""
        self.payload["url"] = url

class Notification(Payload):
    def __init__(self):
        mandatory = ["type", "state", "updated_at", "title"]
        super().__init__(mandatory)

    def set_updated_at(self,date):
        """ set comment update time"""
        self.payload["updated_at"] = date

    def set_upstream(self,upstream):
        """ set comment update time"""
        print("settings upstream", upstream)
        self.payload["upstream"] = upstream


    def set_pr_url(self,url):
        """ set comment pr url"""
        self.payload["pr_url"] = url


    def set_type(self,notification_type):
        """ set comment update time"""
        self.payload["type"] = notification_type

    def set_state(self,state):
        """ set comment update time"""
        self.payload["state"] = state

    def set_comment(self,comment: Comment):
        """ set comment update time"""
        self.payload["status"] = comment.get_payload()

    def set_repo_url(self,repo_url: str):
        """ set repository URL update time"""
        self.payload["repo_url"] = repo_url


    def set_title(self,title):
        """ set issue title"""
        self.payload["title"] = title


class NotificationResp:
    def __init__(self, notifications: [Notification], last_read: datetime.datetime):
        self.notifications = notifications
        self.last_read = last_read
    def get_payload(self):
        notifications = []
        for n in self.notifications:
            notifications.append(n.get_payload())

        return notifications

class CreatePullrequest(Payload):
    # see https://docs.github.com/en/rest/reference/pulls
    def __init__(self):
        mandatory = ["owner", "message", "repo", "head", "base", "title"]
        super().__init__(mandatory)

    def set_owner(self, name):
        """ Set owner name of repository"""
        self.payload["owner"] = name

    def set_repo(self, repo):
        """ Set owner name of repository"""
        self.payload["repo"] = repo

    def set_head(self, head):
        """
        From GitHub Docs:

        The name of the branch you want the changes pulled into.
        This should be an existing branch on the current repository.
        You cannot submit a pull request to one repository that requests a merge to
        a base of another repository.
        """
        self.payload["head"] = head

    def set_base(self, base):
        """
        From GitHub Docs:
        The name of the branch you want the changes pulled into.
        This should be an existing branch on the current repository.
        You cannot submit a pull request to one repository that requests a merge to
        a base of another repository.
        """
        self.payload["base"] = base

    def set_title(self, title):
        """ set title of the PR"""
        self.payload["title"] = title

    def set_message(self, message):
        """ set message of the PR"""
        self.payload["message"] = message

    def set_body(self, body):
        """ set title of the PR message"""
        self.payload["body"] = body



class Forge:
    def __init__(self, base_url: str, admin_user: str, admin_email):
        self.base_url = urlparse(clean_url(base_url))
        if all([self.base_url.scheme != "http", self.base_url.scheme != "https"]):
            print(self.base_url.scheme)
            raise Exception("scheme should be wither http or https")
        self.admin = forge_libgit.InterfaceAdmin(admin_email, admin_user)


    def _lock_repo(self, local_url):
        conn = db.get_db()
        cur = conn.cursor()

        res = cur.execute(
                "SELECT ID, is_locked from interface_repositories WHERE html_url = ?",
                (local_url,),).fetch_one()

        now = rfc3339(datetime.datetime.now())
        if len(res) == 0:
            cur.execute(
                "INSERT OR IGNORE INTO interface_repositories (html_url, is_locked) VALUES (?);",
                (local_url, now),
            )
            conn.commit()
            return True
        else:
            if res[0]["is_locked"] is None:
                cur.execute(
                    "UPDATE interface_repositories is_locked = ? WHERE html_url = ?;",
                    (now, local_url),
                )
                conn.commit()
                cur.execute(
                    "UPDATE interface_repositories is_locked = ? WHERE html_url = ?;",
                    (None, local_url),
                )
                conn.commit()
                return True
            return False

    def _unlock_repo(self, local_url):
        conn = db.get_db()
        cur = conn.cursor()
        cur.execute(
                    "UPDATE interface_repositories is_locked = ? WHERE html_url = ?;",
                    (None, local_url),
                )
        conn.commit()

    def git_clone(self, upstream_url: str, local_name: str):
        local_url = self.get_local_html_url(local_name)
        local_push_url = self.get_local_push_url(local_name)

        if self._lock_repo(local_url):
            repo = forge_libgit.Repo(local_settings.BASE_DIR, local_push_url, upstream_url)
            default_branch = repo.default_branch()
            repo.push_local(default_branch)
            self._unlock_repo(local_url)

    def get_fetch_remote(self, url: str) -> str:
        """Get fetch remote for possible forge URL"""
        parsed = urlparse(url)
        if all([parsed.scheme != "http", parsed.scheme != "https"]):
            raise Exception("scheme should be wither http or https")
        if parsed.netloc != self.base_url.netloc:
            raise Exception("Unsupported forge")
        repo = parsed.path.split('/')[1:3]
        path = format("/%s/%s" % (repo[0], repo[1]))
        return urlunparse((self.base_url.scheme, self.base_url.netloc, path, "", "", ""))

    def apply_patch(self, patch: forge_libgit.Patch, repository_url: str, pr_url: str) -> str:
        """apply patch"""
        (_, repo) = self.get_owner_repo_from_url(repository_url)
        local_url = self.get_local_html_url(repo)
        local_push_url = self.get_local_push_url(repo)
        branch = get_branch_name(pr_url)
        if self._lock_repo(local_url):
            repo = forge_libgit.Repo(local_settings.BASE_DIR, local_push_url, repository_url)
            repo.apply_patch(patch, self.admin, branch)
            repo.push_loca(branch)
            self._unlock_repo(local_url)
        return branch


    def process_patch(self, patch: str, local_url: str, upstream_url, branch_name) -> str:
        """ process patch"""
        repo = forge_libgit.Repo(local_settings.BASE_DIR, local_url, upstream_url)
        repo.fetch_upstream()
        patch = repo.process_patch(patch, branch_name)
        print(patch)

    def get_owner_repo_from_url(self, url: str) -> (str, str):
        """ Get (owner, repo) from repository URL"""
        url = self.get_fetch_remote(url)
        parsed = urlparse(url)
        details = parsed.path.split('/')[1:3]
        (owner, repo) = (details[0], details[1])
        return (owner, repo)

    def get_local_html_url(self, repo: str) -> str:
        """ get local repository's HTML url"""
        raise NotImplementedError

    def get_local_push_url(self, repo: str) -> str:
        raise NotImplementedError


    """ Forge characteristics. All interfaces must implement this class"""
    def get_issues(self, owner: str, repo: str, *args, **kwargs):
        """ Get issues on a repository. Supports pagination via 'page' optional param"""
        raise NotImplementedError

    def create_issue(self, owner: str, repo: str, issue: CreateIssue) -> str:
        """ Creates issue on a repository. reurns html url of the newly created issue"""
        raise NotImplementedError

    def get_repository(self, owner: str, repo: str) -> RepositoryInfo:
        """ Get repository details"""
        raise NotImplementedError

    def create_repository(self, repo: str, description: str):
        """ Create new repository """
        raise NotImplementedError

    def subscribe(self, owner: str, repo: str):
        """ subscribe to events in repository"""
        raise NotImplementedError

    def get_notifications(self, since: datetime.datetime) -> NotificationResp:
        """ subscribe to events in repository"""
        raise NotImplementedError

    def create_pull_request(self, pr: CreatePullrequest) -> str:
        """
            create pull request
            return value is the URL(HTML page) of the newely created PR
        """
        raise NotImplementedError

    def fork(self, owner: str, repo:str):
        """ Fork a repository """
        raise NotImplementedError

    def close_pr(self, owner: str, repo:str):
        """ Fork a repository """
        raise NotImplementedError

    def comment_on_issue(self, owner: str, repo: str, issue_url: str, body:str):
        """Add comment on an existing issue"""
        raise NotImplementedError

class Gitea(Forge):
    def __init__(self, base_url: str, admin_user: str, admin_email):
        super().__init__(base_url=base_url, admin_user=admin_user, admin_email=admin_email)
        self.host = urlparse(clean_url(local_settings.GITEA_HOST))

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
        response = requests.request("GET", url, params=query, headers=headers)
        return response.json()

    def create_issue(self, owner: str, repo: str, issue: CreateIssue):
        """ Creates issue on a repository"""
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
        """ Get repository details"""
        url = self._get_url(format("/repos/%s/%s" % (owner, repo)))
        response = requests.request("GET", url)
        data = response.json()
        info = self._into_repository(data)
        return info

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
        val = []
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
            rn.set_repo_url(n["repository"]["html_url"])

            if notification_type == REPOSITORY:
                print(n)
            if notification_type == PULL:
                rn.set_pr_url(requests.request("GET", subject["url"]).json()["html_url"])
                rn.set_upstream(n["repository"]["description"])
                print(n["repository"]["description"])


            if notification_type == ISSSUE:
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

    def create_pull_request(self, pr: CreatePullrequest):
        url = self._get_url(format("/repos/%s/%s/pulls" , (pr.owner, pr.repo)))
        headers = self._auth()

        payload  = pr.get_payload()
        for key in ["repo", "owner"]:
            del payload[key]

        payload["assignees"] = []
        payload["lables"] = [0]
        payload["milestones"] = 0

        response = requests.request("POST", url, json=payload, headers=headers)
        return response.json()["html_url"]

    def fork(self, owner: str, repo:str):
        """ Fork a repository """
        url = self._get_url(format("/repos/%s/%s/forks" % (owner, repo)))
        print(url)
        headers = self._auth()
        payload = {"oarganization" :"bot"}
        _response = requests.request("POST", url, json=payload, headers=headers)

    def get_issue_index(self, issue_url, owner: str) -> int:
        parsed = urlparse(issue_url)
        path = parsed.path
        path.endswith('/')
        if path.endswith('/'):
            path=path[0:-1]
        index = path.split(owner)[0].split('issue')[2]
        if index.startswith('/'):
            index = index[1:]

        if index.endswith('/'):
            index = index[0:-1]

        return int(index)


    def comment_on_issue(self, owner: str, repo: str, issue_url: str, body:str):
        headers = self._auth()
        (owner, repo) = self.get_fetch_remote(issue_url)
        index = self.get_issue_index(issue_url, owner)
        url = self._get_url(format("/repos/%s/%s/issues/%s" % (owner, repo, index)))
        payload = {"body": body}
        _response = requests.request("POST", url, json=payload, headers=headers)

    def get_local_html_url(self, repo:str) -> str:
        path = format("/%s/%s", local_settings.GITEA_USERNAME, repo)
        return urlunparse((self.host.scheme, self.host.netloc, path, "", "", ""))

    def get_local_push_url(self, repo:str) -> str:
        return format("git@%s:%s/%s.git", self.host.netloc, local_settings.GITEA_USERNAME, repo)

def get_forge() -> Forge:
    return Gitea(base_url=local_settings.GITEA_HOST,
                admin_user=local_settings.ADMIN_USER, 
                admin_email=local_settings.ADMIN_EMAIL)



from urllib.parse import urlparse, urlunparse
import requests

from flask import g

#from interface import forge
#from interface import db
#from interface.api.v1.repo import GET_REPOSITORY

GET_REPOSITORY = "/fetch"
GET_REPOSITORY_INFO = "/info"
FORK_LOCAL = "/fork/local"
FORK_FOREIGN = "/fork/foreign"
SUBSCRIBE = "/subscribe"
COMMENT_ON_ISSUE  = "/issues/comment"
CREATE_ISSUE = "/issue/create"
CREATE_PULL_REQUEST = "/pull/create"

class ForgeClient:
    def __init__(self, forge: Forge):
        self.forge = forge
        self.interfaces = [
                    {
                        "forge": "https://github.com",
                        "interface": "https://github-interface.shuttlecraft.io",
                    },
                    {
                        "forge": "https://git.batsense.net",
                        "interface": "https://gitea-interface.shuttlecraft.io",
                    }
                ]
    def _construct_url(self, interface_url: str, path: str) -> str:
        """ Get interface API routes"""
        prefix = "/api/v1/"
        if path.startswith('/'):
            path=path[1:]

        path = format("%s%s" % (prefix, path))
        parsed = urlparse(interface_url)
        url = urlunparse((parsed.scheme, parsed.netloc, path, "", "", ""))
        return url


    def find_interface(self, url: str):
        parsed = urlparse(url)
        for interface in self.interfaces:
            if urlparse(interface["forge"]).netloc == parsed.netloc:
                return interface["interface"]


    def get_repository(self, repo_url: str):
        """ Get foreign repository url """
        interface_url = self.forge.find_interface(repo_url)
        interface_api_url = self._construct_url(interface_url=interface_url, path=GET_REPOSITORY)

        payload = { "url": repo_url }
        response = requests.request("POST", interface_api_url, json=payload)
        data = response.json()
        return data["repository_url"]

    def get_repository_info(self, repo_url: str):
        """ Get foreign repository url """
        interface_url = self.forge.find_interface(repo_url)
        interface_api_url = self._construct_url(interface_url=interface_url, path=GET_REPOSITORY_INFO)

        payload = { "repository_url": repo_url }
        response = requests.request("POST", interface_api_url, json=payload)
        data = response.json()
        return data


def get_client() -> ForgeClient:
    if "client" not in g:
        g.client = ForgeClient(db.get_forge())
    return g.client



#from .errors import Error

bp = Blueprint("API_V1_INTERFACE", __name__, url_prefix="/api/v1/repository")

#F_D_EMPTY_FORGE_LIST = Error(
#    errcode="F_D_EMPTY_FORGE_LIST",
#    error="The forge list submitted is empty",
#    status=400,
#)
#
#F_D_INTERFACE_UNREACHABLE = Error(
#    errcode="F_D_INTERFACE_UNREACHABLE",
#    error="The interface was unreachable with the publicly accessible URL provided",
#    status=503,
#)


@bp.route(GET_REPOSITORY, methods=["POST"])
def get_repository():
    """
        get repository URL

        ## Request
        {
            "url": string
        }

        ## Response
        {
            "repository_url": string
        }
    """
    data =  request.json()
    payload = { "repository_url": get_forge().get_fetch_remote(data["url"]) }
    return jsonify(payload)

@bp.route(GET_REPOSITORY_INFO, methods=["POST"])
def get_repository_info():
    """
        get repository INFO

        ## Request
        {
            "repository_url": string
        }

        ## Response
        {
            "name": string
            "owner": string
            "description": string
        }
    """
    data =  request.json()
    forge = get_forge()
    (owner, repo) = forge.get_owner_repo_from_url(data["repository_url"])
    resp = forge.get_repository(owner, repo).get_payload()
    return jsonify(resp)

@bp.route(FORK_LOCAL, methods=["POST"])
def fork_local_repository():
    """
        fork local repository

        ## Request
        {
            "repository_url": string
        }

        ## Response
        { } # empty json
    """
    data =  request.json()
    forge = get_forge()
    (owner, repo) = forge.get_owner_repo_from_url(data["repository_url"])
    forge.fork(owner, repo)
    return jsonify({})

@bp.route(FORK_FOREIGN, methods=["POST"])
def fork_foreign_repository():
    """
        fork foreign repository

        ## Request
        {
            "repository_url": string
        }

        ## Response
        { } # empty json
    """
    data =  request.json()
    forge = get_forge()
    repository_url = data["repository_url"]
    client = get_client()
    repository_url = client.get_repository(repository_url)
    info = client.get_repository_info(repository_url)
    local_name = get_local_repository_from_foreign_repo(repository_url)
    forge.create_repository(repo=local_name, description=repository_url)
    forge.git_clone(repository_url, local_name)
    return jsonify({})

@bp.route(SUBSCRIBE, methods=["POST"])
def subscribe():
    """
        subscribe to repository

        ## Request
        {
            "repository_url": string
            "interface_url": string
        }

        ## Response
        { } # empty json
    """
    data =  request.json()
    forge = get_forge()
    repository_url = forge.get_fetch_remote(data["repository_url"])
    interface_url = forge.get_fetch_remote(data["interface_url"])
    (owner, repo) = forge.get_owner_repo_from_url(repository_url)
    forge.subscribe(owner, repo)

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO interface_repositories (html_url) VALUES (?);",
        (repository_url,),
    )
    cur.execute(
        "INSERT OR IGNORE INTO interface_interfaces (url) VALUES (?);",
        (interface_url,),
    )
    conn.commit()
    cur.execute(
        """
        INSERT OR IGNORE INTO interface_event_subscriptsions (repository_id, interface_id)
        VALUES (
            (SELECT interface_interfaces WHERE url = ?),
            (SELECT interface_repositories WHERE html_url = ?)
        );
        """,
        (interface_url,repository_url),
    )
    return jsonify({})

@bp.route(CREATE_ISSUE, methods=["POST"])
def create_issue():
    """
        create new issue

        ## Request
        {
            "repository_url": string
            "title": string
            "body": string
            "due_date": string
            "closed": bool
        }

        ## Response
         {
            "html_url": string // of the newly created issue
         }
    """
    data =  request.json()
    forge = get_forge()
    (owner, repo) = forge.get_owner_repo_from_url(data["repository_url"])

    c = CreateIssue()
    c.set_title(data["title"])
    c.set_body(data["body"])
    c.set_due_date(data["due_date"])
    c.set_closed(data["closed"])

    resp = {"html_url" : forge.create_issue(owner, repo, c) }
    return jsonify(resp)


@bp.route(COMMENT_ON_ISSUE, methods=["POST"])
def comment_on_issue():
    """
        get repository URL

        ## Request
        {
            "issue_url": string // of the target issue
            "body": string // message body
        }

        ## Response
         { }
    """
    data =  request.json()
    forge = get_forge()
    (owner, repo) = forge.get_owner_repo_from_url(data["repository_url"])
    forge.comment_on_issue(owner, repo, issue_url=data["issue_url"], body=data["body"])
    return jsonify({})


@bp.route(COMMENT_ON_ISSUE, methods=["POST"])
def create_pull_request():
    """
        get repository URL

        ## Request
        {
            "repository_url": string // of the target issue
            "pr_url": string // pull request url
            "message": string // message body
            "head": string
            "base" string
            "title": string
            "patch": string
            "author_name": string
            "author_email": string
        }

        ## Response
         { }
    """
    data =  request.json()
    forge = get_forge()
    repository_url = data["repository_url"]
    (owner, repo) = forge.get_owner_repo_from_url(repository_url)
    try:
        forge.fork(owner, repo)
    except:
        pass
    forge.comment_on_issue(owner, repo, issue_url=data["issue_url"], body=data["body"])
    patch = libgit.Patch(data["message"], data["author_name"], data["author_email"])
    branch = forge.apply_patch(patch, repository_url, data["pr_url"])
    pr = CreatePullrequest()
    pr.set_base(data["base"])
    pr.set_body(data["message"])
    pr.set_title(data["title"])
    pr.set_owner(owner)
    pr.set_repo(repo)
    pr.set_head(format("%s:%s", forge.admin.name, branch))

    resp = {"html_url" : forge.create_pull_request(pr) }
    return jsonify(resp)

RUNNING = False
APP = ""

def init(app):
   # global APP
    with app.app_context():
        conn = get_db()
        cur = conn.cursor()
        last_run = date_parse("2021-10-10T17:06:02+05:30")
        cur.execute(
            "INSERT OR IGNORE INTO interface_jobs_run (this_interface_url, last_run) VALUES (?, ?);",
            (local_settings.INTERFACE_URL, str(last_run)),
            )
        conn.commit()

def update_time(time: datetime.datetime, app):
   # global APP
    with app.app_context():
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
                "UPDATE interface_jobs_run set last_run = ? WHERE this_interface_url = ?;",
                (str(time), local_settings.INTERFACE_URL),
            )
        conn.commit()


def get_last_run(app):
    with app.app_context():
        conn = get_db()
        cur = conn.cursor()
        res = cur.execute(
                "SELECT last_run FROM interface_jobs_run WHERE this_interface_url = ?;",
                (local_settings.INTERFACE_URL,),
            ).fetchone()
        return res[0]

#def proces_pull_request():



def run(app):
    #global APP
    #APP = app
    with app.app_context():
        logging.getLogger('jobs').setLevel(logging.WARNING)
        logger = logging.getLogger('jobs')
        scheduler = sched.scheduler(time.time, time.sleep)

        init(app)

        def background_job(app):
            with app.app_context():
                global RUNNING
                if RUNNING:
                    scheduler.enter(local_settings.JOB_RUNNER_DELAY, 8, background_job)
                    return
                else:
                    RUNNING = True

                last_run = get_last_run(app)
                print(last_run)

                forge = get_forge()
                notifications = forge.get_notifications(since=date_parse(last_run)).get_payload()
#                print(notifications)
                for n in notifications:
                    (owner, repo) = forge.get_owner_repo_from_url(n["repo_url"])
                    if all([n["type"] == PULL, owner == local_settings.ADMIN_USER]):
                        print("pr_url")
                        patch = get_patch(n["pr_url"])
    #patch = libgit.Patch(data["message"], data["author_name"], data["author_email"])
                        local = n["repo_url"]
                        upstream = n["upstream"]
                        #print(local, upstream)
                        patch  = forge.process_patch(patch, local, upstream, get_branch_name(n["pr_url"]))
#                       # patch = libgit.Patch(n["title"], n["owner"], local_settings.ADMIN_EMAIL)
                        print(patch)


#                    if n["type"] == 
                scheduler.enter(local_settings.JOB_RUNNER_DELAY, 8, background_job, argument=(app,))
                RUNNING = False

        scheduler.enter(local_settings.JOB_RUNNER_DELAY, 8, background_job, argument=(app,))
        threading.Thread(target=scheduler.run).start()



def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        DATABASE=os.path.join(app.instance_path, "interface.db"),
    )

    init_app(app)
    if test_config is None:
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    @app.after_request
    def flock_google(response):
        response.headers["Permissions-Policy"] = "interest-cohort=()"
        return response

    run(app)

    app.register_blueprint(bp)
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(threaded=True,port=7000)
