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
from urllib.parse import urlparse, urlunparse

from flask import Blueprint, jsonify, request
from interface.utils import clean_url, get_local_repository_from_foreign_repo
#from interface import FORGE
from interface.forge import CreateIssue, CreatePullrequest

from interface.db import get_db
from interface.forge import get_forge
from interface.client import get_client, GET_REPOSITORY, GET_REPOSITORY_INFO
from interface.client import SUBSCRIBE, COMMENT_ON_ISSUE, CREATE_ISSUE
from interface.client import FORK_FOREIGN, FORK_LOCAL
#from .errors import Error

bp = Blueprint("API_V1_INTERFACE", __name__, url_prefix="/repository")

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
    forge.create_repository(repo=local_name, description=info["description"])
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
