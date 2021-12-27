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
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
from signedjson.key import (
    generate_signing_key,
    get_verify_key,
    encode_signing_key_base64,
)
import click
from flask.cli import with_appcontext
from flask import Blueprint

keygen_bp = Blueprint("keys", __name__)

# from signedjson.sign import (
#    sign_json, verify_signed_json, SignatureVerifyException
# )
#
# signed_json = sign_json({'my_key': 'my_data'}, 'Alice', signing_key)
#
# verify_key = get_verify_key(signing_key)
#
# try:
#    verify_signed_json(signed_json, 'Alice', verify_key)
#    print('Signature is valid')
# except SignatureVerifyException:
#    print('Signature is invalid')


@keygen_bp.cli.command("generate")
def keygen():
    """Generate key"""
    signing_key = generate_signing_key("zxcvb")
    print(f"\n\nPrivate Key: {encode_signing_key_base64(signing_key)}")
    print(f"Public Key: {encode_signing_key_base64(get_verify_key(signing_key))}")
    exit(0)
