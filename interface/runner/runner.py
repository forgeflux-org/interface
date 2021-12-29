"""
A job runner that receives events(notifications) and runs relevant jobs on them
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
import sys
from dateutil.parser import parse as date_parse

from flask import g

from dynaconf import settings
from interface.git import get_forge
from interface.forges.notifications import PULL, ISSUE
from interface.forges.utils import get_patch, get_branch_name
from interface.db import get_db
from interface.runner.events import resolve_notification

RUNNING = False


class Runner:
    def __init__(self, app):
        self.app = app
        logging.getLogger("jobs").setLevel(logging.WARNING)
        self.logger = logging.getLogger("jobs")
        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.shutdown_flag = threading.Event()
        self.current_run = None

        with self.app.app_context():
            self.git = get_forge()
            conn = get_db()
            cur = conn.cursor()
            last_run = date_parse("2021-11-10T17:06:02+05:30")
            cur.execute(
                """
                INSERT OR IGNORE INTO interface_jobs_run
                    (this_interface_url, last_run) VALUES (?, ?);
                """,
                (settings.SERVER.domain, str(last_run)),
            )
            conn.commit()
        self.thread = threading.Thread(target=self._background_job)
        self.thread.start()
        return

    def get_switch(self):
        return self.shutdown_flag

    def kill(self):
        if self.current_run is not None:
            self.scheduler.cancel(self.current_run)
        self.shutdown_flag.set()
        self.shutdown_flag.wait()
        print("set")
        self.thread.join()
        print("exit")

    def _update_time(self, last_run: datetime.datetime):
        with self.app.app_context():
            conn = get_db()
            cur = conn.cursor()
            cur.execute(
                "UPDATE interface_jobs_run set last_run = ? WHERE this_interface_url = ?;",
                (str(last_run), settings.SERVER.domain),
            )
            conn.commit()

    def get_last_run(self):
        with self.app.app_context():
            conn = get_db()
            cur = conn.cursor()
            res = cur.execute(
                "SELECT last_run FROM interface_jobs_run WHERE this_interface_url = ?;",
                (settings.SERVER.domain,),
            ).fetchone()
            return res[0]

    def _background_job(self):
        print("running")
        while True:
            if self.shutdown_flag.is_set():
                print("exiting worker")
                break
            with self.app.app_context():
                global RUNNING
                if RUNNING:
                    self.scheduler.enter(
                        settings.SYSTEM.job_runner_delay, 8, self._background_job
                    )
                    return
                else:
                    RUNNING = True
                last_run = self.get_last_run()
                print(last_run)

                notifications = self.git.forge.get_notifications(
                    since=date_parse(last_run)
                )
                for n in notifications.notifications:
                    resolve_notification(n).run()

            time.sleep(settings.SYSTEM.job_runner_delay)


def init_app(app):
    runner = Runner(app)
    return runner
