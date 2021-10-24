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
from interface.utils import clean_url
#from interface import FORGE
from interface.forge import CreateIssue, CreatePullrequest

from interface.db import get_db, get_forge
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


@bp.route("/fetch", methods=["POST"])
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

@bp.route("/fork", methods=["POST"])
def fork_repository():
    """
        fork repository

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

@bp.route("/subscribe", methods=["POST"])
def subscribe():
    """
        subscribe to repository

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
    forge.subscribe(owner, repo)
    return jsonify({})

@bp.route("/issues/create", methods=["POST"])
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


@bp.route("/issues/comment", methods=["POST"])
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
