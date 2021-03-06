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
    def load_private_from_str(cls, key: str) -> "RSAKeyPair":
        x = cls()
        x.key = serialization.load_pem_private_key(key.encode("utf-8"), password=None)
        return x

    @staticmethod
    def load_public_from_str(key: str):
        key = serialization.load_pem_public_key(key.encode("utf-8"))
        return key

    def to_json_key(self) -> str:
        """new line characters are formatted to \\n"""
        #        key = self.public_key().replace("\n", "\\n")
        return self.public_key()

    @staticmethod
    def from_json_key(key) -> str:
        key = key.replace("\\n", "\n")
        return key
