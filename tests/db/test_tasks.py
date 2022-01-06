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
from dataclasses import asdict

from interface.auth import KeyPair
from interface.forges.payload import MetaData, Author, CommentOnIssue, RepositoryInfo
from interface.db import DBInterfaces, JobStatus, DBTask, save_message, DBTaskJson

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


def cmp_task_json(lhs: DBTaskJson, rhs: DBTaskJson) -> bool:
    """Compare two DBTaskJson objects"""
    return all(
        [
            lhs.id == rhs.id,
            lhs.job_uuid == rhs.job_uuid,
            json.dumps(asdict(lhs.message)) == json.dumps(asdict(rhs.message)),
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

    assert DBTask.load_with_db_id(11) is None
    assert DBTask.load_with_job_id(task.uuid) is None
    assert DBTaskJson.load_with_job_id(task.uuid) is None

    task.save()

    from_db_with_db_id = DBTask.load_with_db_id(task.id)
    from_db_with_job_id = DBTask.load_with_job_id(task.uuid)
    assert cmp_tasks(task, from_db_with_db_id)
    assert cmp_tasks(task, from_db_with_job_id)

    task.set_error()
    assert task.get_status() is JobStatus.ERROR
    assert DBTask.load_with_db_id(task.id).get_status() is JobStatus.ERROR

    task.set_completed()
    assert task.get_status() is JobStatus.COMPLETED
    assert DBTask.load_with_db_id(task.id).get_status() is JobStatus.COMPLETED
    db_id = task.id
    uuid = task.uuid

    # A new UUID is created if there's a conflict, check if this works
    task.save()
    assert task.id != db_id
    assert task.uuid != uuid

    # test tasks_json
    author = Author(
        fqdn_username="foo@github.com", name="Foo", profile_url="https://github.com"
    )
    meta = MetaData(
        html_url="https://github.com/foo/bar/issues/4", interface_url=url, author=author
    )
    repo = RepositoryInfo(name="foo", owner="bar")
    comment = CommentOnIssue(
        meta=meta, body="test comment", repository=repo, issue_url=meta.html_url
    )

    task_json = DBTaskJson(job_uuid=task.uuid, message=comment)

    assert DBTaskJson.load_with_db_id(11) is None
    assert DBTaskJson.load_with_job_id(task.uuid) is None

    task_json.save()

    assert cmp_task_json(task_json, DBTaskJson.load_with_db_id(task_json.id))
    assert cmp_task_json(task_json, DBTaskJson.load_with_job_id(task.uuid))

    task = save_message(comment)
    assert cmp_tasks(task, DBTask.load_with_db_id(task.id))
    task_json = DBTaskJson.load_with_job_id(task.uuid)
    task = DBTask.load_with_db_id(task.id)
    assert task_json is not None
    assert task is not None
    assert task_json.job_uuid == task.uuid


def test_event_status():
    assert str(JobStatus.COMPLETED) == "COMPLETED"
    assert str(JobStatus.ERROR) == "ERROR"
    assert str(JobStatus.QUEUED) == "QUEUED"
