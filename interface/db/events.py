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
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, unique
from uuid import UUID, uuid4
from sqlite3 import IntegrityError

from .conn import get_db
from .interfaces import DBInterfaces


@unique
class JobStatus(Enum):
    """Represents the completion status of a Job"""

    ERROR = -1
    QUEUED = 0
    COMPLETED = 1

    def __str__(self) -> str:
        return self.name


@dataclass
class DBTask:
    """User information as stored in the database"""

    signed_by: DBInterfaces
    uuid: UUID = uuid4()
    status: JobStatus = JobStatus.QUEUED
    created: str = str(datetime.now())
    updated: str = None
    id: int = None

    def __update(self):
        """
        Save updates to database.
        Caller is advised to set self.updated to datetime.now()
        before calling this method, if job status is changed.
        """
        self.updated = str(datetime.now())
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE tasks
            SET
                updated = ?,
                status = ?
            WHERE
                id=?
            """,
            (
                self.updated,
                self.status.value,
                self.id,
            ),
        )
        conn.commit()

    def set_completed(self):
        """Set job status to completed"""
        self.status = JobStatus.COMPLETED
        self.__update()

    def set_error(self):
        """Set job status to error"""
        self.status = JobStatus.ERROR
        self.__update()

    def get_status(self) -> JobStatus:
        """Get job status"""
        return self.status

    def save(self):
        """Save message to database"""
        self.signed_by.save()

        conn = get_db()
        cur = conn.cursor()
        while True:
            try:
                cur.execute(
                    """
                    INSERT INTO tasks
                        (job_id, status, created, signed_by)
                    VALUES
                        (?, ?, ?, (SELECT ID FROM interfaces WHERE url = ?));
                    """,
                    (
                        str(self.uuid),
                        self.status.value,
                        self.created,
                        self.signed_by.url,
                    ),
                )
                conn.commit()
                data = cur.execute(
                    """
                    SELECT ID FROM tasks
                    WHERE
                        job_id = ?
                    AND
                        signed_by = (SELECT ID FROM interfaces WHERE url = ?);
                    """,
                    (str(self.uuid), self.signed_by.url),
                ).fetchone()
                self.id = data[0]
                break
            except IntegrityError:
                self.uuid = uuid4()
                continue

    @classmethod
    def load_with_job_id(cls, job_id: UUID) -> "DBTask":
        """Load user from database with the URL of the interface which signed it's creation"""
        conn = get_db()
        cur = conn.cursor()
        data = cur.execute(
            """
             SELECT
                 ID,
                 status,
                 created,
                 updated,
                 signed_by
             FROM
                 tasks
             WHERE
                job_id = ?
            """,
            (str(job_id),),
        ).fetchone()
        if data is None:
            return None
        val = cls(
            signed_by=DBInterfaces.load_from_database_id(data[4]),
        )
        val.uuid = job_id
        val.id = data[0]
        val.status = JobStatus(data[1])
        val.created = data[2]
        val.updated = data[3]
        return val

    @classmethod
    def load_job_with_db_id(cls, db_id: int) -> "DBTask":
        """Load job from database with database ID assigned to the job"""
        conn = get_db()
        cur = conn.cursor()
        data = cur.execute(
            """
             SELECT
                 job_id,
                 status,
                 created,
                 updated,
                 signed_by
             FROM
                 tasks
             WHERE
                ID = ?
            """,
            (db_id,),
        ).fetchone()
        if data is None:
            return None
        val = cls(signed_by=DBInterfaces.load_from_database_id(data[4]))
        val.id = db_id
        val.uuid = UUID(data[0])
        val.status = JobStatus(data[1])
        val.created = data[2]
        val.updated = data[3]
        return val
