"""
Issues related routes
"""
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
from flask import Blueprint, jsonify, request

from interface.git import get_forge
from interface.client import CREATE_ISSUE, COMMENT_ON_ISSUE
from interface.forges.payload import CreateIssue

bp = Blueprint("API_V1_ISSUES", __name__, url_prefix="/issues")


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
    data = request.get_json()
    git = get_forge()
    (owner, repo) = git.forge.get_owner_repo_from_url(data["repository_url"])

    c = CreateIssue()
    c.set_title(data["title"])
    c.set_body(data["body"])
    c.set_due_date(data["due_date"])
    c.set_closed(data["closed"])

    resp = {"html_url": git.forge.create_issue(owner, repo, c)}
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
    data = request.get_json()
    git = get_forge()
    (owner, repo) = git.forge.get_owner_repo_from_url(data["repository_url"])
    git.forge.comment_on_issue(
        owner, repo, issue_url=data["issue_url"], body=data["body"]
    )
    return jsonify({})
