"""
Nodeinfo routes
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
from flask import Blueprint, jsonify

from interface.db import DBUser, DBComment, DBActivity, INTERFACE_BASE_URL
from interface.error import internal_server_error

bp = Blueprint("nodeinfo", __name__, url_prefix="/nodeinfo")


@bp.route("/2.0.json", methods=["GET"])
def nodeinfo_v2_0():
    """get nodeinfo v2.0"""
    resp = {
        "version": "2.0",
        "software": {
            "name": "ForgeFlux Interface",
            "version": "0.1.0-alpha",
        },
        "services": {"inbound": [], "outbound": []},
        "protocols": ["activitypub"],
        "usage": {
            "users": {
                "total": DBUser.count.count(),
                "activeMonth": DBActivity.monthly_active_users.count(),
                "activeHalfyear": DBActivity.six_month_active_users.count(),
            },
            "localPosts": DBActivity.count.count(),
            "localComments": DBComment.count.count(),
        },
        "openRegistrations": False,
        "metadata": {"forgeflux-protocols": ["interface.forgeflux.org"]},
    }
    return jsonify(resp)


@bp.route("", methods=["GET"])
def index():
    resp = {
        "links": [
            {
                "href": f"{INTERFACE_BASE_URL}/.well-known/nodeinfo/2.0.json",
                "rel": "http://nodeinfo.diaspora.software/ns/schema/2.0",
            }
        ]
    }
    return jsonify(resp)
