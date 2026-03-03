"""Simple sync engine skeleton for PoC.
This module would run on the edge gateway and sync local SQLite -> central API.
"""
import time
import threading

class SyncEngine:
    def __init__(self, interval_seconds: int = 10):
        self.interval = interval_seconds
        self._running = False
        self._thread = None

    def _work(self):
        while self._running:
            # TODO: scan local SQLite for unsynced records and POST to central API
            print("[sync] heartbeat: scanning local store for unsynced records...")
            time.sleep(self.interval)

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._work, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=1)

if __name__ == "__main__":
    s = SyncEngine(5)
    s.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        s.stop()
