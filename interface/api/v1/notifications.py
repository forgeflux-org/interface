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
from interface.error import F_D_INVALID_PAYLOAD, F_D_INTERFACE_UNREACHABLE, Error
from interface.git import get_forge
from interface.client import SUBSCRIBE, EVENTS
from interface.runner.events import resolve_notification
from interface.forges.notifications import Notification
from interface.utils import clean_url, verify_interface_online
from interface.client import get_client


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
    data = request.get_json()
    interface_url = clean_url(data["interface_url"])

    if not verify_interface_online(interface_url):
        return F_D_INTERFACE_UNREACHABLE.get_error_resp()

    git = get_forge()
    repository_url = git.forge.get_fetch_remote(data["repository_url"])

    (owner, repo) = git.forge.get_owner_repo_from_url(repository_url)
    try:
        git.forge.subscribe(owner, repo)

        conn = db.get_db()
        cur = conn.cursor()

        repo_exists = cur.execute(
            "SELECT EXISTS (SELECT 1 FROM local_repositories WHERE html_url = ?);",
            (repository_url,),
        ).fetchone()

        if any([repo_exists is None, len(repo_exists) != 1, repo_exists[0] == 0]):
            cur.execute(
                # TODO use gitea_forge_repositories
                "INSERT OR IGNORE INTO local_repositories (html_url) VALUES (?);",
                (repository_url,),
            )
            conn.commit()

        interface_exists = cur.execute(
            "SELECT EXISTS (SELECT 1 FROM interfaces WHERE url = ?);", (interface_url,)
        ).fetchone()

        if any(
            [
                interface_exists is None,
                len(interface_exists) != 1,
                interface_exists[0] == 0,
            ]
        ):
            key = get_client().get_pubkey(interface_url)
            cur.execute(
                "INSERT OR IGNORE INTO interfaces (url, public_key) VALUES (?, ?);",
                (interface_url, key),
            )
            conn.commit()

        cur.execute(
            """
            INSERT OR IGNORE INTO subscriptions (repository_id, interface_id)
            VALUES (
                (SELECT ID from interfaces WHERE url = ?),
                (SELECT ID from local_repositories WHERE html_url = ?)
            );
            """,
            (interface_url, repository_url),
        )
        conn.commit()
        return jsonify({})
    except Error as e:
        return e.get_error_resp()


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
    data = request.get_json()
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
    resolve_notification(n).run()
    return jsonify({})
