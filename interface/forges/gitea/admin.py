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
from interface.settings import settings
from flask import g

from interface.utils import clean_url, trim_url
from interface.db import DBUser, DBInterfaces, get_db_interface


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
            avatar_url="https://git.batsense.net/avatar/a4edc8a838d6e28ddc38ab12aeb9d9cd?size=1160",
            description="ForgeFlux bot",
        )
        db_user.save()
        g.db_user = db_user
    return g.db_interface
