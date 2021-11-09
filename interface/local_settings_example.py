import socket

GITEA_API_KEY = ""
GITEA_USERNAME = ""
GITEA_HOST = ""
GITHUB_HOST = ""
GITHUB_API_KEY = ""

# URL at which this interface is available
INTERFACE_URL = socket.gethostbyaddr(socket.gethostname())[0]
PORT = 7000


BASE_DIR = ""

ADMIN_EMAIL = ""
ADMIN_USER = ""
JOB_RUNNER_DELAY = 10  ## in seconds

DEFAULT_NORTHSTAR = "https://northstar.forgefed.io"
