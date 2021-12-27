"""
event subscriptions
"""

from yoyo import step

__depends__ = {}

steps = [
    ## local repositories: repositories on the forge that this interface services
    step(
        """
    CREATE TABLE IF NOT EXISTS local_repositories(
        html_url VARCHAR(3000) UNIQUE NOT NULL,
        ID INTEGER PRIMARY KEY NOT NULL
    );

    """
    ),
    # TODO get public key
    step(
        """
        CREATE TABLE IF NOT EXISTS interfaces(
            url VARCHAR(3000) UNIQUE NOT NULL,
            public_key TEXT UNIQUE NOT NULL,
            ID INTEGER PRIMARY KEY NOT NULL
        );
    """
    ),
    step(
        """
        CREATE TABLE IF NOT EXISTS subscriptions(
            repository_id INTEGER NOT NULL REFERENCES local_repositories(ID) ON DELETE CASCADE,
            interface_id INTEGER NOT NULL REFERENCES interfaces(ID) ON DELETE CASCADE
        );
    """
    ),
]
