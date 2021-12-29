"""
interface forks
"""

from yoyo import step

__depends__ = {"20211024_01_h2IuD-interface-jobs"}

steps = [
    step(
        """
    CREATE TABLE IF NOT EXISTS forks(
        parent_owner VARCHAR(100) NOT NULL,
        parent_repo_name VARCHAR(100) NOT NULL,
        fork_repo_name VARCHAR(100) PRIMARY KEY NOT NULL
    );
    """
    ),
]
