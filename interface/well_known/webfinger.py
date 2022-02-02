"""
Webfinger route
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

from interface.db import INTERFACE_DOMAIN
from interface.git import get_issue, get_user, get_repo
from interface.error import Error, bad_req, internal_server_error

bp = Blueprint("webfinger", __name__, url_prefix="/webfinger")


JRD_JSON = "application/jrd+json; charset=utf-8"


def set_jrd_json(data):
    resp = jsonify(data)
    resp.headers["Content-Type"] = JRD_JSON
    return resp


@bp.route("", methods=["GET"])
def webfinger():
    """get webfinger data"""
    resource = request.args.get("resource")
    if resource is None:
        return bad_req()
    if any(["acct:" not in resource, "@" not in resource]):
        return bad_req()
    try:
        parts = resource.split("acct:")
        parts = parts[1].split("@")
        username = parts[0]
        domain = parts[1]
        if domain != INTERFACE_DOMAIN:
            return bad_req()
        if "!" not in username:
            user = get_user(username)
            return set_jrd_json(user.webfinger())

        username_parts = username.split("!")
        owner = username_parts[1]
        name = username_parts[2]
        repo = get_repo(name=name, owner=owner)

        if len(username_parts) == 3:
            return set_jrd_json(repo.webfinger())

        if len(username_parts) == 5:
            repo_scope_id = username_parts[4]
            # "!owner!repo!<issue/pull>!id"
            if username_parts[3] == "issue":
                issue = get_issue(owner=owner, repo=name, issue_id=repo_scope_id)
                return set_jrd_json(issue.webfinger())

            if username_parts[3] == "pull":
                print("pull")
                raise NotImplementedError
        return bad_req()
    except Exception as e:
        print("caught exception {e}")
        if isinstance(e, Error):
            return e.get_error_resp()
        return internal_server_error()
