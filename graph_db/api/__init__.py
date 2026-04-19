"""API sub-package: FastAPI routes for the graph database."""

from graph_db.api.nodes import router as nodes_router
from graph_db.api.edges import router as edges_router
from graph_db.api.traversal import router as traversal_router

__all__ = ["nodes_router", "edges_router", "traversal_router"]
