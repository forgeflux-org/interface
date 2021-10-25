"""
Repository related routes
"""
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
from flask import Blueprint, jsonify, request
from libgit import Patch

from interface.forges import get_forge
from interface.forges.payload import CreatePullrequest
from interface.forges.utils import get_local_repository_from_foreign_repo
from interface.client import GET_REPOSITORY, GET_REPOSITORY_INFO, FORK_FOREIGN
from interface.client import FORK_LOCAL, CREATE_PULL_REQUEST, get_client

bp = Blueprint("API_V1_REPO", __name__, url_prefix="/repository")


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
    data = request.json()
    payload = {"repository_url": get_forge().get_fetch_remote(data["url"])}
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
    data = request.json()
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
    data = request.json()
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
    data = request.json()
    forge = get_forge()
    repository_url = data["repository_url"]
    client = get_client()
    repository_url = client.get_repository(repository_url)
    info = client.get_repository_info(repository_url)
    local_name = get_local_repository_from_foreign_repo(repository_url)
    forge.create_repository(repo=local_name, description=repository_url)
    forge.git_clone(repository_url, local_name)
    return jsonify({})


@bp.route(CREATE_PULL_REQUEST, methods=["POST"])
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
    data = request.json()
    forge = get_forge()
    repository_url = data["repository_url"]
    (owner, repo) = forge.get_owner_repo_from_url(repository_url)
    try:
        forge.fork(owner, repo)
    except:
        pass
    forge.comment_on_issue(owner, repo, issue_url=data["issue_url"], body=data["body"])
    patch = Patch(data["message"], data["author_name"], data["author_email"])
    branch = forge.apply_patch(patch, repository_url, data["pr_url"])
    pr = CreatePullrequest()
    pr.set_base(data["base"])
    pr.set_body(data["message"])
    pr.set_title(data["title"])
    pr.set_owner(owner)
    pr.set_repo(repo)
    pr.set_head(format("%s:%s", forge.admin.name, branch))

    resp = {"html_url": forge.create_pull_request(pr)}
    return jsonify(resp)
