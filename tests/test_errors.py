""" Test errors helper class"""
# North Star ---  A lookup service for forged fed ecosystem
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
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from interface.app import create_app

from interface.error import F_D_INVALID_PAYLOAD, F_D_INTERFACE_UNREACHABLE, Error


def test_errors(client):
    """Test interface registration handler"""

    def verify_status(e: Error, status: int):
        assert e.status() == status
        resp = e.get_error_resp()
        assert resp.status.find(str(status)) is not -1

    verify_status(F_D_INVALID_PAYLOAD, 400)
    verify_status(F_D_INTERFACE_UNREACHABLE, 503)
