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
from dynaconf import settings

from interface.auth import KeyPair
from interface.app import app
from interface.db import DBInterfaces, JobStatus, DBTask

from .test_interface import cmp_interface


def cmp_tasks(lhs: DBTask, rhs: DBTask) -> bool:
    """Compare two DBTask objects"""
    return all(
        [
            lhs.uuid == rhs.uuid,
            lhs.status == rhs.status,
            lhs.created == rhs.created,
            lhs.updated == rhs.updated,
            lhs.id == rhs.id,
            cmp_interface(lhs.signed_by, rhs.signed_by),
        ]
    )


def test_task(client):
    """Test DBTask database class"""

    key = KeyPair()
    url = "https://test_interface.example.com"
    interface = DBInterfaces(url=url, public_key=key.to_base64_public())
    interface.save()

    task = DBTask(
        signed_by=interface,
    )
    task.save()
    from_db_with_db_id = DBTask.load_job_with_db_id(task.id)
    from_db_with_job_id = DBTask.load_with_job_id(task.uuid)
    assert cmp_tasks(task, from_db_with_db_id)
    assert cmp_tasks(task, from_db_with_job_id)

    task.set_error()
    assert task.get_status() is JobStatus.ERROR
    assert DBTask.load_job_with_db_id(task.id).get_status() is JobStatus.ERROR

    task.set_completed()
    assert task.get_status() is JobStatus.COMPLETED
    assert DBTask.load_job_with_db_id(task.id).get_status() is JobStatus.COMPLETED
    db_id = task.id
    uuid = task.uuid

    # A new UUID is created if there's a conflict, check if this works
    task.save()
    assert task.id != db_id
    assert task.uuid != uuid
