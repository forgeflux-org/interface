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
from urllib.parse import urlparse

from flask import Blueprint, jsonify, Response, request
from dynaconf import settings

from interface.db import DBIssue, DBUser, DBRepo
from interface.git import get_forge

bp = Blueprint("WELL-KNOWN", __name__, url_prefix="/.well-known/")


def bad_req():
    res = Response()
    res.status_code = 400
    return res


def internal_server_error():
    res = Response()
    res.status_code = 500
    return res


interface_domain = urlparse(settings.SERVER.url).netloc
JRD_JSON = "application/jrd+json; charset=utf-8"


def set_jrd_json(data):
    resp = jsonify(data)
    resp.headers["Content-Type"] = JDR_JSON
    return resp


@bp.route("webfinger", methods=["GET"])
def webfinger():
    """get webfinger data"""
    resource = request.args.get("resource")
    if resource is None:
        return bad_req()
    if any(["acct:" not in resource, "@" not in resource]):
        return bad_req()

    print(resource)
    try:
        parts = resource.split("acct:")
        parts = parts[1].split("@")
        username = parts[0]
        domain = parts[1]
        if domain != interface_domain:
            print(f"this domain: {interface_domain} recv {domain}")
            return bad_req()
        if "!" not in username:
            user = DBUser.load(username)
            if user is None:
                git = get_forge()
                user = git.forge.get_user(username).to_db_user()
                user.save()
                return set_jrd_json(user.webfinger())

        if "!" in username:
            username_parts = username.split("!")
            owner = username_parts[1]
            name = username_parts[2]
            repo = DBRepo.load(name=name, owner=owner)
            git = get_forge()

            if repo is None:
                repo_info = git.forge.get_repository(owner=owner, repo=name)
                repo = repo_info.to_db_repo()
                repo.save()

            if len(username_parts) == 3:
                # "!owner!repo"
                return set_jrd_json(repo.webfinger())

            if len(username_parts) == 5:
                repo_scope_id = username_parts[4]
                print(f"owner: {owner} name: {name} scoped_id: {repo_scope_id}")
                # "!owner!repo!<issue/pull>!id"
                if username_parts[3] == "issue":
                    print("issue")
                    issue = DBIssue.load(repo, repo_scope_id)
                    if issue is None:
                        # fetch info from forge and save
                        raise NotImplementedError
                    return set_jrd_json(issue.webfinger())

                    raise NotImplementedError

                if username_parts[3] == "pull":
                    print("pull")
                    issue = DBIssue.load(repo, repo_scope_id)
                    if issue is None:
                        # fetch info from forge and save
                        raise NotImplementedError
                    return set_jrd_json(issue.webfinger())

                    raise NotImplementedError
                return bad_req()

            # acct:!owner!repo!issue!id@domain.com
            raise NotImplementedError
        print(username)
        print(domain)
        return Response()
    except NotImplementedError as e:
        return internal_server_error()
    except Exception as e:
        return bad_req()
    else:
        return internal_server_error()
