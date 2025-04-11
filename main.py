#!/usr/bin/env python
"""
YDR Policy RAG Project - Main Command Line Interface

Provides access to various project functionalities including data collection,
database management, MCP server, Agent interaction, and Frontend tasks.
"""
import typer
import asyncio
import logging
import os
import sys
# subprocess and Path are no longer needed as Alembic commands are removed
from typing import Optional

# --- Configuration ---
# Import both configs, potentially aliasing them if needed elsewhere
from ydrpolicy.data_collection.config import config as data_collection_config
from ydrpolicy.backend.config import config as backend_config

# --- Logging ---
# Use specific loggers for different components
from ydrpolicy.data_collection.logger import DataCollectionLogger
from ydrpolicy.backend.logger import BackendLogger # Assuming BackendLogger can be instantiated

# --- Utilities ---
from ydrpolicy.backend.utils.paths import ensure_directories # Ensure base dirs exist


# Create main app instance
app = typer.Typer(
    name="ydrpolicy",
    help="Main CLI for the Yale Diagnostic Radiology Policy RAG Project."
)

# ============================================================================
# 1. Policy Mode (Data Collection & Single Policy Management)
# ============================================================================
policy_app = typer.Typer(name="policy", help="Manage data collection and individual policies.")
app.add_typer(policy_app)

# --- Helper to setup data collection logger ---
def get_data_collection_logger(name: str, log_file_key: str = 'CRAWLER_LOG_FILE') -> DataCollectionLogger:
    """Initializes the DataCollectionLogger."""
    default_log_filename = f"{name.lower().replace('-', '_')}.log"
    log_path = getattr(data_collection_config.LOGGING, log_file_key, os.path.join(data_collection_config.PATHS.DATA_DIR, "logs", default_log_filename))
    try:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
    except OSError as e:
         print(f"Warning: Could not create log directory {os.path.dirname(log_path)}: {e}", file=sys.stderr)
         log_path = None
    return DataCollectionLogger(name=name, level=logging.INFO, path=log_path)

# --- Helper to setup backend logger ---
def get_backend_logger(name="BackendCLI") -> BackendLogger:
    """Initializes the BackendLogger."""
    log_path = backend_config.LOGGING.FILE
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    return BackendLogger(name=name, path=log_path, level=backend_config.LOGGING.LEVEL)


# --- Policy Commands (Data Collection) ---
@policy_app.command("collect-all", help="Run the full crawl and scrape process.")
def policy_collect_all():
    """Runs crawl_main followed by scrape_main."""
    logger = get_data_collection_logger("collect_all", "COLLECT_POLICIES_LOG_FILE")
    logger.info("Starting full data collection process (crawl + scrape)...")
    try:
        from ydrpolicy.data_collection.collect_policies import collect_all
        collect_all(config=data_collection_config, logger=logger)
        logger.success("Full data collection process completed.")
    except Exception as e:
        logger.failure(f"Full data collection failed: {e}", exc_info=True)
        raise typer.Exit(code=1)

@policy_app.command("collect-one", help="Collect, process, and classify a single policy URL.")
def policy_collect_one(
    url: str = typer.Argument(..., help="The URL of the policy to collect.")
):
    """Collects a single URL using the collect_one logic."""
    logger = get_data_collection_logger("collect_one", "COLLECT_POLICIES_LOG_FILE")
    logger.info(f"Starting single URL collection for: {url}")
    try:
        from ydrpolicy.data_collection.collect_policies import collect_one
        collect_one(url=url, config=data_collection_config, logger=logger)
        logger.success(f"Single URL collection finished for: {url}")
    except Exception as e:
        logger.failure(f"Single URL collection failed for {url}: {e}", exc_info=True)
        raise typer.Exit(code=1)

@policy_app.command("scrape-all", help="Run only the scraping/classification process on existing crawled data.")
def policy_scrape_all():
    """Runs the scrape_main function."""
    logger = get_data_collection_logger("scrape_all", "SCRAPER_LOG_FILE")
    logger.info("Starting scraping process...")
    try:
        from ydrpolicy.data_collection.scrape.scrape import main as scrape_main
        scrape_main(config=data_collection_config, logger=logger)
        logger.success("Scraping process completed.")
    except Exception as e:
        logger.failure(f"Scraping process failed: {e}", exc_info=True)
        raise typer.Exit(code=1)

@policy_app.command("crawl-all", help="Run only the crawling process.")
def policy_crawl_all():
    """Runs the crawl_main function."""
    logger = get_data_collection_logger("crawl_all", "CRAWLER_LOG_FILE")
    logger.info("Starting crawling process...")
    try:
        from ydrpolicy.data_collection.crawl.crawl import main as crawl_main
        crawl_main(config=data_collection_config, logger=logger)
        logger.success("Crawling process completed.")
    except Exception as e:
        logger.failure(f"Crawling process failed: {e}", exc_info=True)
        raise typer.Exit(code=1)


# --- Policy Commands (Single Policy Management) ---
@policy_app.command("remove", help="Remove a single policy and its data from the database by ID or Title.")
def policy_remove(
    policy_id: Optional[int] = typer.Option(None, "--id", help="ID of the policy to remove."),
    title: Optional[str] = typer.Option(None, "--title", help="Exact title of the policy to remove."),
    db_url: Optional[str] = typer.Option(None, help="Custom database URL to override config."),
    force: bool = typer.Option(False, "--force", "-f", help="Force removal without confirmation."),
):
    """Removes a single policy from the database."""
    logger = get_backend_logger("PolicyRemove")

    if policy_id is None and title is None:
        logger.error("You must provide either --id or --title to remove a policy.")
        raise typer.Exit(code=1)
    if policy_id is not None and title is not None:
        logger.error("Provide either --id or --title, not both.")
        raise typer.Exit(code=1)

    identifier = policy_id if policy_id is not None else title
    id_type = "ID" if policy_id is not None else "Title"
    logger.warning(f"Policy removal initiated for {id_type}: '{identifier}'.")

    if not force:
         confirm = typer.confirm(f"Are you sure you want to remove policy '{identifier}' and all its associated data?")
         if not confirm:
              logger.info("Policy removal cancelled.")
              raise typer.Exit()

    logger.warning(f"Proceeding with removal of policy {id_type}: '{identifier}'...")
    try:
        # Assuming remove_policy.py has run_remove async function
        from ydrpolicy.backend.scripts.remove_policy import run_remove
        success = asyncio.run(run_remove(identifier=identifier, db_url=db_url))
        if success:
            logger.success(f"Policy '{identifier}' removed successfully.")
        else:
            logger.error(f"Failed to remove policy '{identifier}'. Check previous logs for details.")
            raise typer.Exit(code=1)
    except ImportError:
         logger.failure("Could not import 'run_remove' from 'ydrpolicy.backend.scripts.remove_policy'. Make sure the script exists.", exc_info=True)
         raise typer.Exit(code=1)
    except Exception as e:
        logger.failure(f"Policy removal failed: {e}", exc_info=True)
        raise typer.Exit(code=1)

# ============================================================================
# 2. Database Mode (Simplified - No Migrations)
# ============================================================================
db_app = typer.Typer(name="database", help="Manage the backend database setup and removal.")
app.add_typer(db_app)

# --- Database Commands ---
@db_app.command("init", help="Initialize DB: create DB/extensions/tables, optionally populate.")
def db_init(
    db_url: Optional[str] = typer.Option(None, help="Custom database URL to override config."),
    no_populate: bool = typer.Option(False, "--no-populate", help="Skip populating the DB from processed data."),
):
    """
    Initializes the database schema using models and optionally populates data.
    Assumes the schema defined in models.py is the final target state.
    """
    logger = get_backend_logger("DBInit")
    logger.info("Starting database initialization...")
    ensure_directories() # Ensure log/data paths exist
    should_populate = not no_populate

    try:
        # Step 1: Initialize DB, Tables, Extensions, and Populate Data
        logger.info("Initializing database structure and populating data...")
        from ydrpolicy.backend.database.init_db import init_db
        # init_db handles DB creation, extension, tables via create_all, triggers, population
        asyncio.run(init_db(db_url=db_url, populate=should_populate))
        logger.success("Database initialization process completed successfully.")

    except Exception as e:
        logger.failure(f"Database initialization failed: {e}", exc_info=True)
        raise typer.Exit(code=1)


@db_app.command("remove", help="Remove (DROP) the entire database (DELETES ALL DATA). Requires confirmation.")
def db_remove(
    db_url: Optional[str] = typer.Option(None, help="Custom database URL to override config."),
    force: bool = typer.Option(False, "--force", "-f", help="Force drop without confirmation (DANGEROUS)."),
):
    """Drops the entire database."""
    logger = get_backend_logger("DBRemove")
    logger.warning("Command to remove entire database initiated.")

    if not force:
        confirm = typer.confirm("Are you absolutely sure you want to REMOVE (DROP) the ENTIRE database? This cannot be undone.")
        if not confirm:
            logger.info("Database removal (drop) cancelled.")
            raise typer.Exit()

    logger.warning("Proceeding with database removal (drop)...")
    try:
        from ydrpolicy.backend.database.init_db import drop_db
        asyncio.run(drop_db(db_url=db_url))
        logger.success("Database removal (drop) completed.")
    except Exception as e:
        logger.failure(f"Database removal (drop) failed: {e}", exc_info=True)
        raise typer.Exit(code=1)

# --- Migration Sub-App ---
# MIGRATION COMMANDS REMOVED

# ============================================================================
# 3. MCP Mode (Placeholder)
# ============================================================================
mcp_app = typer.Typer(name="mcp", help="Manage the MCP server.")
app.add_typer(mcp_app)

@mcp_app.command("start", help="Start the MCP server (Not Implemented).")
def mcp_start(
    host: str = typer.Option(backend_config.MCP.HOST, help="Host to bind the server to."),
    port: int = typer.Option(backend_config.MCP.PORT, help="Port to bind the server to."),
    transport: str = typer.Option(backend_config.MCP.TRANSPORT, help="Transport mode (http or stdio).")
):
    logger = get_backend_logger("MCP")
    logger.info(f"Attempting to start MCP server on {host}:{port} via {transport}...")
    logger.warning("MCP server start functionality is not yet implemented.")
    # Placeholder for actual MCP server start logic
    # from ydrpolicy.backend.mcp.server import start_mcp_server # Example import
    # asyncio.run(start_mcp_server(host, port, transport)) # Example call

# ============================================================================
# 4. Agent Mode (Placeholder)
# ============================================================================
agent_app = typer.Typer(name="agent", help="Interact with the chat agent.")
app.add_typer(agent_app)

@agent_app.command("chat", help="Start an interactive chat session with the agent (Not Implemented).")
def agent_chat():
    logger = get_backend_logger("Agent") # Or a dedicated agent logger
    logger.info("Starting interactive chat agent session...")
    logger.warning("Agent chat functionality is not yet implemented.")
    # Placeholder for agent interaction logic
    # from ydrpolicy.agent.cli import run_chat_session # Example import
    # run_chat_session() # Example call


# ============================================================================
# Main Execution Guard
# ============================================================================
if __name__ == "__main__":
    # Ensure project root is discoverable if running as script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, os.pardir)) # Adjust if main.py is not in root
    if project_root not in sys.path:
         sys.path.insert(0, project_root)

    app()