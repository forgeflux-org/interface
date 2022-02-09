"""
User activity pub routes
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
from urllib.parse import urlparse
from dataclasses import asdict
import json

from flask import Blueprint, jsonify, Response, request, redirect
from interface.settings import settings

from interface.db import DBIssue, DBUser, DBRepo, INTERFACE_DOMAIN
from interface.git import get_forge, get_user
from interface.error import bad_req, internal_server_error
from interface.utils import activity_json, CONTENT_TYPE_ACTIVITY_JSON

bp = Blueprint("activity-pub-user", __name__, url_prefix="/u/")


@bp.route("<username>", methods=["GET"])
def actor(username):
    """get actor data"""
    user = get_user(username)
    if "Accept" in request.headers:
        if CONTENT_TYPE_ACTIVITY_JSON in request.headers["Accept"]:
            return activity_json(user.to_actor())
    return redirect(user.profile_url)


@bp.route("<username>/inbox", methods=["POST"])
def inbox(username):
    """stub for user actor  inbox"""

    print(f"headers:{request.headers}\npayload: {request.json}")
    return internal_server_error()


@bp.route("<username>/outbox", methods=["GET"])
def outbox(username):
    """stub for user actor outbox"""
    print(f"headers:{request.headers}\npayload: {request.json}")
    return internal_server_error()
