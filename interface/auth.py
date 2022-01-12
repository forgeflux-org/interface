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
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import sys
from dataclasses import dataclass, asdict

from signedjson.key import (
    generate_signing_key,
    get_verify_key,
    encode_signing_key_base64,
    decode_verify_key_base64,
    decode_signing_key_base64,
)
from flask import Blueprint, g, jsonify
from dynaconf import settings

keygen_bp = Blueprint("keys", __name__)

VERSION = "zxcvb"
ALGORITHM = "ed25519"


@dataclass
class PublicKey:
    key: str

    def to_resp(self):
        return jsonify(asdict(self))


class KeyPair:
    def __init__(self):
        self.signing_key = generate_signing_key("zxcvb")

    @classmethod
    def from_base_64(cls, base64_key: str):
        key = decode_signing_key_base64(ALGORITHM, VERSION, base64_key)
        obj = cls()
        obj.signing_key = key
        return obj

    def to_base64_public(self) -> str:
        return encode_signing_key_base64(self.signing_key)

    def to_base64_private(self) -> str:
        return encode_signing_key_base64(get_verify_key(self.signing_key))

    @classmethod
    def loadkey_fresh(cls):
        """Use this method sparingly as it reads private_key from config every time it's called.
        Could be expensive
        """
        return cls.from_base_64(settings.PRIVATE_KEY)

    @staticmethod
    def decode_public_key_base_64(base64_key: str):
        return decode_verify_key_base64(ALGORITHM, VERSION, base64_key)

    @classmethod
    def loadkey(cls):
        """Load key from settings"""
        if "private_key" not in g:
            key = cls.from_base_64(settings.PRIVATE_KEY)
            g.private_key = key
        return g.private_key


@keygen_bp.cli.command("generate")
def keygen():
    """Generate key"""
    key = KeyPair()
    print(f"\n\nPrivate Key: {key.to_base64_private()}")
    print(f"Public Key: {key.to_base64_public()}")
    sys.exit(0)


from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization


class RSAKeyPair:
    def __init__(self):
        self.key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

    def public_key(self):
        key = self.key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        #        return key.decode("ascii")
        return key.decode("utf-8")

    def private_key(self):
        pem = self.key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
        return pem.decode("utf-8")

    @classmethod
    def load_prvate_from_str(cls, key: str) -> "RSAKeyPair":
        x = cls()
        x.key = serialization.load_pem_private_key(key.encode("utf-8"), password=None)
        return x

    @staticmethod
    def load_public_from_str(key: str):
        key = serialization.load_pem_public_key(key.encode("utf-8"))
        return key
