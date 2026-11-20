import os
import signal

from supervisor.childutils import listener


if __name__ == "__main__":
    listener.wait()
    listener.ok()
    os.kill(os.getppid(), signal.SIGTERM)
