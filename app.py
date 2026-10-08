"""
NetSimX — Member 4 Application Entry Point
Launches the PyQt6 GUI application.
"""

import sys
import os
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from gui.main_window import MainWindow
from database.database import Database
from config.settings import PATHS
from utils.logger import get_logger

# Configure logging
logger = get_logger("NetSimX", level=logging.INFO)


def main():
    """Main application entry point."""
    logger.info("=" * 60)
    logger.info("NetSimX — Network Simulation & Performance Analysis")
    logger.info("Member 4: GUI, Dashboard, Analytics & Database")
    logger.info("=" * 60)

    # Create QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("NetSimX")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("NETSIMX-CN")

    # Set application-wide style hints
    app.setStyle("Fusion")

    # Ensure database directory exists
    db_path = PATHS.DB_PATH
    os.makedirs(db_path.parent, exist_ok=True)
    logger.info(f"Database path: {db_path}")

    # Create and show main window
    try:
        window = MainWindow()
        window.show()
        logger.info("Main window displayed")
    except Exception as exc:
        logger.error(f"Failed to create main window: {exc}", exc_info=True)
        sys.exit(1)

    # Run event loop
    exit_code = app.exec()
    logger.info(f"Application exiting with code {exit_code}")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
