"""FastAPI application entry point.

Run with::

    uvicorn graph_db.api.app:app --reload

Then open http://localhost:8000/docs for interactive Swagger documentation.
"""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from graph_db.api.nodes import router as nodes_router
from graph_db.api.nodes import _db as _nodes_db_dep
from graph_db.api.edges import router as edges_router
from graph_db.api.edges import _db as _edges_db_dep
from graph_db.api.traversal import router as traversal_router
from graph_db.api.traversal import _db as _traversal_db_dep
from graph_db.base import GraphDatabase
from graph_db.config import GraphDBConfig

logger = logging.getLogger("graph_db.api")

# ---------------------------------------------------------------------------
# Global DB instance shared across requests
# ---------------------------------------------------------------------------

_db_instance: GraphDatabase | None = None
_db_config: GraphDBConfig | None = None


def _try_connect(config: GraphDBConfig, retries: int = 5, delay: float = 3.0) -> bool:
    """Try to connect to the database with retries."""
    from graph_db.config import connect
    global _db_instance
    for attempt in range(1, retries + 1):
        try:
            _db_instance = connect(config)
            logger.info("Database connected on attempt %d", attempt)
            return True
        except Exception as e:
            logger.warning(
                "Database connection attempt %d/%d failed: %s",
                attempt, retries, e,
            )
            if attempt < retries:
                time.sleep(delay)
    return False


def get_db() -> GraphDatabase:
    """FastAPI dependency that provides the GraphDatabase instance.

    If the connection was lost, attempts to reconnect once before failing.
    """
    global _db_instance
    if _db_instance is not None and _db_instance.is_connected():
        return _db_instance
    # Try to reconnect
    if _db_config is not None:
        if _try_connect(_db_config, retries=1, delay=0):
            return _db_instance  # type: ignore
    raise HTTPException(status_code=503, detail="Database not connected. Please retry later.")


# ---------------------------------------------------------------------------
# Lifespan: connect on startup, close on shutdown
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _db_instance, _db_config
    _db_config = GraphDBConfig.from_env()
    _try_connect(_db_config, retries=10, delay=3.0)

    yield
    if _db_instance is not None:
        _db_instance.close()
        _db_instance = None


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Graph Database API",
    description=(
        "A generic, database-agnostic REST API for graph database operations.\n\n"
        "Supports Node/Edge CRUD, graph traversal, Cypher query execution, "
        "batch operations, and schema management.\n\n"
        "Configure the database connection via environment variables:\n"
        "- `GRAPH_DB_URI` (default: bolt://localhost:7687)\n"
        "- `GRAPH_DB_USERNAME` (default: neo4j)\n"
        "- `GRAPH_DB_PASSWORD`\n"
        "- `GRAPH_DB_DATABASE` (default: neo4j)\n"
        "- `GRAPH_DB_BACKEND` (default: neo4j)\n"
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(nodes_router)
app.include_router(edges_router)
app.include_router(traversal_router)

# Override the stub _db dependency in every router with the real get_db
for _dep in (_nodes_db_dep, _edges_db_dep, _traversal_db_dep):
    app.dependency_overrides[_dep] = get_db


@app.get("/health", tags=["System"], summary="Health check")
def health():
    """Check if the API and database connection are healthy."""
    connected = _db_instance is not None and _db_instance.is_connected()
    return {"status": "ok" if connected else "disconnected", "connected": connected}
