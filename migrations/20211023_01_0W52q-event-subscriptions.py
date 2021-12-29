"""
event subscriptions
"""

from yoyo import step

__depends__ = {}

steps = [
    ## local repositories: repositories on the forge that this interface services
    step(
        """
        CREATE TABLE IF NOT EXISTS interfaces(
            url VARCHAR(3000) UNIQUE NOT NULL,
            public_key TEXT UNIQUE NOT NULL,
            ID INTEGER PRIMARY KEY NOT NULL
        );
    """
    ),
]
