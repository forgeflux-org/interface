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
import json
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum, unique
from uuid import UUID, uuid4
from sqlite3 import IntegrityError

from interface.forges.payload import (
    Message,
    MessageType,
    CreatePullrequest,
    CreateIssue,
    CommentOnIssue,
)
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
    """Task information in the database"""

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
    def load_with_db_id(cls, db_id: int) -> "DBTask":
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


@dataclass
class DBTaskJson:
    """Task configuration and related data stored as JSON in the database"""

    job_uuid: UUID
    message: Message
    id: int = None

    @staticmethod
    def __create_msg(data: str) -> Message:
        data = json.loads(data)
        msg_type = data["msg_type"]
        if msg_type == MessageType.COMMENT_ON_ISSUE:
            return CommentOnIssue(**data)

        if msg_type == MessageType.CREATE_ISSUE:
            return CreateIssue(**data)

        if msg_type == MessageType.CREATE_PR:
            return CreatePullrequest(**data)
        raise ValueError(f"{msg_type} unknown")

    def save(self):
        """Save message to database"""
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO tasks_json
                (json, task_id)
            VALUES
                (?, (SELECT ID FROM tasks WHERE job_id = ?))
            """,
            (json.dumps(asdict(self.message)), str(self.job_uuid)),
        )
        conn.commit()
        data = cur.execute(
            """
            SELECT ID FROM tasks_json
            WHERE
                task_id = (SELECT ID FROM tasks WHERE job_id =?)
            """,
            (str(self.job_uuid),),
        ).fetchone()
        self.id = data[0]

    @classmethod
    def load_with_job_id(cls, job_id: UUID) -> "DBTaskJson":
        """Load user from database with the URL of the interface which signed it's creation"""
        task = DBTask.load_with_job_id(job_id)
        if task is None:
            return None

        conn = get_db()
        cur = conn.cursor()
        data = cur.execute(
            """
             SELECT
                 ID,
                 json
             FROM
                 tasks_json
             WHERE
                task_id = (SELECT ID FROM tasks WHERE job_id =?)
            """,
            (str(job_id),),
        ).fetchone()
        if data is None:
            return None

        message = cls.__create_msg(data[1])

        val = cls(
            id=data[0],
            message=message,
            job_uuid=job_id,
        )
        return val

    @classmethod
    def load_with_db_id(cls, db_id: int) -> "DBTaskJson":
        """Load job from database with database ID assigned to the job"""
        conn = get_db()
        cur = conn.cursor()
        data = cur.execute(
            """
             SELECT
                 task_id,
                 json
             FROM
                 tasks_json
             WHERE
                ID = ?
            """,
            (db_id,),
        ).fetchone()
        if data is None:
            return None
        job_uuid = DBTask.load_with_db_id(data[0]).uuid
        message = cls.__create_msg(data[1])
        val = cls(id=db_id, job_uuid=job_uuid, message=message)
        return val


def save_message(msg: Message) -> DBTask:
    """save a message in database and it's status as an event in database"""
    interface = DBInterfaces.load_from_url(msg.meta.interface_url)
    if interface is None:
        # get and save interface
        raise NotImplementedError
    task = DBTask(signed_by=interface)
    task.save()

    task_json = DBTaskJson(job_uuid=task.uuid, message=msg)
    task_json.save()
    return task
