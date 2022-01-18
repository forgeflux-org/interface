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
import random
import string
from urllib.parse import urlparse, urlunparse
from datetime import datetime

import requests


def clean_url(url: str):
    """Remove paths and tracking elements from URL"""
    parsed = urlparse(url)
    cleaned = urlunparse((parsed.scheme, parsed.netloc, "", "", "", ""))
    return cleaned


def trim_url(url: str) -> str:
    if url.endswith("/"):
        url = url[0:-1]
    return url


def get_rand(len: int) -> str:
    return "".join(
        random.choice(string.ascii_uppercase + string.digits) for _ in range(len)
    )


EPOCH = datetime.utcfromtimestamp(0)


def since_epoch(date: datetime = None) -> int:
    """Get current time since Unix  epoch in seconds"""
    if not date:
        date = datetime.now()
    return int((date - EPOCH).total_seconds())


_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


def from_epoch(date: int) -> datetime:
    """Get time milliseconds from seconds since Unix epoch"""
    return datetime.utcfromtimestamp(date)


def date_from_string(date: str) -> datetime:
    """get datetime from string"""
    return datetime.strptime(date, _DATE_FORMAT)
