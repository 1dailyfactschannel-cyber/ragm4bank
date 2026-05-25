#!/usr/bin/env python
"""
Script for initial database setup
"""
import asyncio
import sys
from app.db.database import init_db, close_db
from app.utils.logging import setup_logger

logger = setup_logger()


async def main():
    logger.info("Initializing database...")
    try:
        await init_db()
        logger.info("Database initialized successfully!")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        sys.exit(1)
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
