"""
Entry point for running batch worker as a module.

Usage: python -m workers.batch_worker
"""

import asyncio
from workers.batch_worker import BatchWorker

if __name__ == "__main__":
    worker = BatchWorker()
    asyncio.run(worker.run())

