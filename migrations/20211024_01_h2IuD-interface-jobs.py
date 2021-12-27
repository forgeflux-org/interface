"""
interface jobs
"""

from yoyo import step

__depends__ = {"20211023_01_0W52q-event-subscriptions"}

steps = [
    step(
        """
        CREATE TABLE IF NOT EXISTS interface_jobs_run(
            this_interface_url VARCHAR(3000) NOT NULL UNIQUE PRIMARY KEY,
            last_run VARCHAR(50) NOT NULL
        );
    """
    )
]
