""" Test errors helper class"""
# Interface ---  API-space federation for software forges
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
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from interface.app import create_app
from interface.error import (
    F_D_INVALID_PAYLOAD,
    F_D_INTERFACE_UNREACHABLE,
    Error,
    bad_req,
    internal_server_error,
    not_found,
)


def expect_error(response, err: Error) -> bool:
    """Test responses"""
    data = response.json
    return all(
        [
            str(err.status) in response.status,
            err.error == data["error"],
            err.errcode == data["errcode"],
        ]
    )


def pytest_expect_errror(got, expected: Error) -> bool:
    return got.value.errcode == expected.errcode


def test_errors(client):
    """Test interface registration handler"""

    def verify_status(e: Error, status: int):
        """Utility function to verify status"""
        assert e.status == status
        resp = e.get_error_resp()
        assert resp.status.find(str(status)) is not -1

    verify_status(F_D_INVALID_PAYLOAD, 400)
    verify_status(F_D_INTERFACE_UNREACHABLE, 503)
    assert bad_req().status_code == 400
    assert internal_server_error().status_code == 500
    assert not_found().status_code == 404
