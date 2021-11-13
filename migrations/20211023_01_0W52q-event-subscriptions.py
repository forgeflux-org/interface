"""
event subscriptions
"""

from yoyo import step

__depends__ = {}

steps = [
        ## local repositories: repositories on the forge that this interface services
    step("""
    CREATE TABLE IF NOT EXISTS interface_local_repositories(
        html_url VARCHAR(3000) UNIQUE NOT NULL,
        ID INTEGER PRIMARY KEY NOT NULL
    );

    """),
    step("""
        CREATE TABLE IF NOT EXISTS interface_interfaces(
            url VARCHAR(3000) UNIQUE NOT NULL,
            ID INTEGER PRIMARY KEY NOT NULL
        );
    """),
    step("""
        CREATE TABLE IF NOT EXISTS interface_event_subscriptsions(
            repository_id INTEGER NOT NULL REFERENCES interface_local_repositories(ID) ON DELETE CASCADE,
            interface_id INTEGER NOT NULL REFERENCES interface_interfaces(ID) ON DELETE CASCADE
        );
    """)
]
