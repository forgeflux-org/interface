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
from functools import lru_cache

from interface.settings import settings

from interface.utils import since_epoch
from .conn import get_db

CACHE_TTL = settings.SYSTEM.cache_ttl  # in seconds
CACHE_TTL = CACHE_TTL if CACHE_TTL is not None else 1800  # in seconds


class RecordCount:
    def __init__(self, table_name: str):
        self.table_name = table_name

    @lru_cache(maxsize=1)
    def __count(self) -> (int, int):
        conn = get_db()
        cur = conn.cursor()
        count = cur.execute(f"SELECT COUNT(*) FROM {self.table_name}").fetchone()[0]
        return (int(count), since_epoch())

    def count(self) -> int:
        """Get total number of records stored"""
        (num, created_at) = self.__count()
        if since_epoch() - created_at > CACHE_TTL:
            self.__count.cache_clear()
            (num, _) = self.__count()
        return num
