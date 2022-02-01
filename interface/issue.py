"""
Repository activity pub routes
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
from flask import Blueprint, request, redirect

from interface.error import internal_server_error
from interface.git import get_issue_from_actor_name
from interface.utils import CONTENT_TYPE_ACTIVITY_JSON, activity_json

bp = Blueprint("activity-pub-issue", __name__, url_prefix="/i/")


@bp.route("<issue_id>", methods=["GET"])
def actor(issue_id):
    """get actor data"""
    issue = get_issue_from_actor_name(issue_id)
    if "Accept" in request.headers:
        if CONTENT_TYPE_ACTIVITY_JSON in request.headers["Accept"]:
            return activity_json(issue.to_actor())
    return redirect(issue.html_url)


@bp.route("<issue_id>/inbox", methods=["POST"])
def inbox(issue_id):
    """get actor inbox"""

    print(f"headers:{request.headers}\npayload: {request.json}")
    return internal_server_error()


@bp.route("<issue_id>/outbox", methods=["GET"])
def outbox(issue_id):
    """get actor outbox"""
    print(f"headers:{request.headers}\npayload: {request.json}")
    return internal_server_error()
