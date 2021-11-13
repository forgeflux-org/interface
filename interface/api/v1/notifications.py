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

from interface import db
from interface.error import F_D_INVALID_PAYLOAD
from interface.git import get_forge
from interface.client import SUBSCRIBE, EVENTS
from interface.runner.events import RunNoification
from interface.forges.notifications import Notification


bp = Blueprint("API_V1_NOTIFICATIONS", __name__, url_prefix="/notifications")


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
    data = request.json()
    git = get_forge()
    repository_url = git.forge.get_fetch_remote(data["repository_url"])
    interface_url = git.forge.get_fetch_remote(data["interface_url"])
    (owner, repo) = git.forge.get_owner_repo_from_url(repository_url)
    git.forge.subscribe(owner, repo)

    conn = db.get_db()
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
            (SELECT interface_local_repositories WHERE html_url = ?)
        );
        """,
        (interface_url, repository_url),
    )
    return jsonify({})


@bp.route(EVENTS, methods=["POST"])
def events():
    """
    receive events

    ## Request
    {
        "id": string
        "type": string
        "state": string
        "updated_at": string
        "title": string

        "repo_url": string?
        "upstream": string?
        "comment": string?
        "pr_url": string?
    }

    ## Response
    { } # empty json
    """
    data = request.json()
    if any(
        [
            "type" not in data,
            "status" not in data,
            "updated_at" not in data,
            "title" not in data,
        ]
    ):
        return F_D_INVALID_PAYLOAD.get_error_resp()
    n = Notification()
    n.payload = data
    runable = RunNoification.resolve(n)
    # TODO send to worker
    runable.run()

    return jsonify({})
