"""
Errors
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
from dataclasses import dataclass

from flask import jsonify, Response as FlaskResponse
from requests import Response


@dataclass
class Error(Exception):
    """Helper class for presenting errors in the format specified by the specification"""

    errcode: str
    error: str
    status: int

    def get_error(self):
        """Get error in serialziable form"""
        error = {}
        error["errcode"] = self.errcode
        error["error"] = self.error
        return error

    def get_error_resp(self):
        """Get error response"""
        resp = jsonify(self.get_error())
        resp.status = self.status
        return resp

    @staticmethod
    def from_resp(resp: Response):
        if resp.status_code != 200:
            data = resp.json()
            print(data)
            return Error(
                status=resp.status_code, error=data["error"], errcode=data["errcode"]
            )
        return None


F_D_INTERFACE_UNREACHABLE = Error(
    errcode="F_D_INTERFACE_UNREACHABLE",
    error="Interface unreachable",
    status=503,
)

F_D_INVALID_PAYLOAD = Error(
    errcode="F_D_INVALID_PAYLOAD",
    error="Please submit valid payload",
    status=400,
)

F_D_FORGE_UNKNOWN_ERROR = Error(
    errcode="F_D_FORGE_UNKNOWN_ERROR",
    error="Something went wrong on the Software Forge side",
    status=502,
)


def bad_req():
    """Empty response with 400 bad request status code"""
    res = FlaskResponse()
    res.status_code = 400
    return res


def internal_server_error():
    """Empty response with 500 internal_server_error status code"""
    res = FlaskResponse()
    res.status_code = 500
    return res


def not_found():
    """Empty response with 404 not found status code"""
    res = FlaskResponse()
    res.status_code = 404
    return res
