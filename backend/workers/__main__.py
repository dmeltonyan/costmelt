"""
Entry point for running batch worker as a module.

Usage: python -m workers.batch_worker
"""

import asyncio
from workers.batch_worker import main

if __name__ == "__main__":
    asyncio.run(main())

