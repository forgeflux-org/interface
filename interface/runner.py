"""
A job runner that receives events(notifications) and runs revelant jobs on them
"""
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
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import logging
import sched
import threading
import time
import datetime
from os import getenv
from dotenv import load_dotenv

from interface.git import get_forge
from interface.forges.notifications import PULL, ISSUE
from interface.forges.utils import get_patch, get_branch_name
from interface.db import get_db
from interface.forges.gitea import date_parse

RUNNING = False


class Runner:
    def __init__(self, app):
        self.app = app
        logging.getLogger("jobs").setLevel(logging.WARNING)
        self.logger = logging.getLogger("jobs")
        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.git = get_forge()

        with self.app.app_context():
            conn = get_db()
            cur = conn.cursor()
            last_run = date_parse("2021-10-10T17:06:02+05:30")
            cur.execute(
                """
                INSERT OR IGNORE INTO interface_jobs_run
                    (this_interface_url, last_run) VALUES (?, ?);
                """,
                (getenv("INTERFACE_URL"), str(last_run)),
            )
            conn.commit()

    def _update_time(self, last_run: datetime.datetime):
        with self.app.app_context():
            conn = get_db()
            cur = conn.cursor()
            cur.execute(
                "UPDATE interface_jobs_run set last_run = ? WHERE this_interface_url = ?;",
                (str(last_run), getenv("INTERFACE_URL")),
            )
            conn.commit()

    def get_last_run(self):
        with self.app.app_context():
            conn = get_db()
            cur = conn.cursor()
            res = cur.execute(
                "SELECT last_run FROM interface_jobs_run WHERE this_interface_url = ?;",
                (getenv("INTERFACE_URL"),),
            ).fetchone()
            return res[0]

    def _background_job(self):
        with self.app.app_context():
            global RUNNING
            if RUNNING:
                self.scheduler.enter(
                    getenv("JOB_RUNNER_DELAY"), 8, self._background_job
                )
                return
            else:
                RUNNING = True

            last_run = self.get_last_run()
            print(last_run)

            notifications = self.git.forge.get_notifications(
                since=date_parse(last_run)
            ).get_payload()
            #                    print(notifications)
            for n in notifications:
                (owner, _repo) = self.git.forge.get_owner_repo_from_url(n["repo_url"])
                if all([n["type"] == PULL, owner == getenv("ADMIN_USER")]):
                    patch = get_patch(n["pr_url"])
                    local = n["repo_url"]
                    upstream = n["upstream"]
                    patch = self.git.process_patch(
                        patch, local, upstream, get_branch_name(n["pr_url"])
                    )
                    print(patch)

            #                        if n["type"] ==
            RUNNING = False
            self.scheduler.enter(getenv("JOB_RUNNER_DELAY"), 8, self._background_job)
            # argument=(app,))

    def run(self):
        """Start job runner"""
        self.scheduler.enter(
            getenv("JOB_RUNNER_DELAY"), 8, self._background_job
        )  # argument=(self,))
        threading.Thread(target=self.scheduler.run).start()
