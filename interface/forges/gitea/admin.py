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
from dynaconf import settings
from flask import g

from interface.utils import clean_url, trim_url
from interface.db import DBUser, DBInterfaces
from interface.auth import KeyPair


def get_db_interface() -> DBInterfaces:
    """Get DBInterfaces of this interface"""
    if "g.db_interface" not in g:
        key = KeyPair.loadkey_fresh().to_base64_public()
        interface = DBInterfaces(url=settings.SERVER.url, public_key=key)
        interface.save()
        g.db_interface = interface
    return g.db_interface


def get_db_user() -> DBInterfaces:
    """Get DBUser of this interface"""
    if "g.db_user" not in g:
        interface = get_db_interface()
        username = settings.GITEA.username
        host = trim_url(clean_url(settings.GITEA.host))
        profile_url = f"{host}/{username}"
        db_user = DBUser(
            name=username,
            user_id=username,
            profile_url=profile_url,
            signed_by=interface,
        )
        db_user.save()
        g.db_user = db_user
    return g.db_interface
