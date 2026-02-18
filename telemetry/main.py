"""Telemetry service entry point."""
import asyncio
import signal
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend'))

from telemetry.subscriber import start, logger


def handle_shutdown(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info("telemetry.shutdown_signal_received", signal=signum)
    raise SystemExit(0)


# Register signal handlers
signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)


if __name__ == "__main__":
    logger.info("telemetry.service_starting")
    try:
        asyncio.run(start())
    except SystemExit:
        logger.info("telemetry.service_stopped")
    except Exception as e:
        logger.error("telemetry.service_failed", error=str(e), exc_info=True)
        raise
