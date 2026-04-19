"""Traversal, query, batch, schema, and database-info API routes."""

from __future__ import annotations

import neo4j.exceptions
from fastapi import APIRouter, Depends, HTTPException

from graph_db.api.schemas import (
    BatchEdgeCreate,
    BatchNodeCreate,
    ConstraintCreate,
    ConstraintListResponse,
    CountResponse,
    CypherQuery,
    IndexCreate,
    IndexDrop,
    IndexListResponse,
    MessageResponse,
    NeighbourQuery,
    NodeEdgesQuery,
    NodeListResponse,
    PathResponse,
    QueryResponse,
    ShortestPathQuery,
    StringListResponse,
)
from graph_db.base import GraphDatabase
from graph_db.models import PagedResult, PageInfo

router = APIRouter(tags=["Graph Operations"])


def _db() -> GraphDatabase:
    raise NotImplementedError


def _handle_db_error(e: Exception) -> HTTPException:
    """Convert database exceptions to appropriate HTTP errors."""
    if isinstance(e, ValueError):
        return HTTPException(status_code=400, detail=str(e))
    if isinstance(e, neo4j.exceptions.CypherSyntaxError):
        return HTTPException(status_code=400, detail=f"Cypher syntax error: {e.message}")
    if isinstance(e, neo4j.exceptions.ClientError):
        return HTTPException(status_code=400, detail=str(e))
    if isinstance(e, neo4j.exceptions.ConstraintError):
        return HTTPException(status_code=409, detail=str(e))
    if isinstance(e, neo4j.exceptions.DatabaseError):
        return HTTPException(status_code=404, detail=str(e))
    return HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Traversal
# ---------------------------------------------------------------------------

@router.post("/traverse/neighbours", response_model=NodeListResponse, summary="Get neighbour nodes")
def get_neighbours(body: NeighbourQuery, db: GraphDatabase = Depends(_db)):
    """Get 1-hop neighbour nodes of a given node."""
    try:
        nodes = db.get_neighbours(
            body.node_id, direction=body.direction,
            edge_type=body.edge_type, limit=body.limit,
        )
    except Exception as e:
        raise _handle_db_error(e)
    return NodeListResponse(
        data=PagedResult(
            items=nodes,
            page=PageInfo(offset=0, limit=body.limit, total=len(nodes)),
        )
    )


@router.post("/traverse/edges", response_model=NodeListResponse, summary="Get node edges")
def get_node_edges(body: NodeEdgesQuery, db: GraphDatabase = Depends(_db)):
    """Get edges connected to a node."""
    try:
        edges = db.get_node_edges(
            body.node_id, direction=body.direction,
            edge_type=body.edge_type, limit=body.limit,
        )
    except Exception as e:
        raise _handle_db_error(e)
    return NodeListResponse(
        data=PagedResult(
            items=edges,
            page=PageInfo(offset=0, limit=body.limit, total=len(edges)),
        )
    )


@router.post("/traverse/shortest-path", response_model=PathResponse, summary="Find shortest path")
def shortest_path(body: ShortestPathQuery, db: GraphDatabase = Depends(_db)):
    """Find the shortest path between two nodes."""
    try:
        path = db.shortest_path(
            body.source_id, body.target_id,
            edge_type=body.edge_type, max_depth=body.max_depth,
        )
    except Exception as e:
        raise _handle_db_error(e)
    if path is None:
        raise HTTPException(status_code=404, detail="No path found")
    return PathResponse(data=path)


# ---------------------------------------------------------------------------
# Query
# ---------------------------------------------------------------------------

@router.post("/query", response_model=QueryResponse, summary="Execute Cypher query")
def execute_query(body: CypherQuery, db: GraphDatabase = Depends(_db)):
    """Execute a raw Cypher query with optional parameters."""
    try:
        result = db.execute_query(body.query, body.params or None)
    except Exception as e:
        raise _handle_db_error(e)
    return QueryResponse(data=result)


@router.post("/query/read", response_model=QueryResponse, summary="Execute read-only Cypher")
def execute_read(body: CypherQuery, db: GraphDatabase = Depends(_db)):
    """Execute a read-only Cypher query (may be routed to read replica)."""
    try:
        result = db.execute_read(body.query, body.params or None)
    except Exception as e:
        raise _handle_db_error(e)
    return QueryResponse(data=result)


@router.post("/query/write", response_model=QueryResponse, summary="Execute write Cypher")
def execute_write(body: CypherQuery, db: GraphDatabase = Depends(_db)):
    """Execute a write Cypher query with auto-retry on transient errors."""
    try:
        result = db.execute_write(body.query, body.params or None)
    except Exception as e:
        raise _handle_db_error(e)
    return QueryResponse(data=result)


# ---------------------------------------------------------------------------
# Batch
# ---------------------------------------------------------------------------

@router.post("/batch/nodes", response_model=NodeListResponse, summary="Batch create nodes")
def batch_create_nodes(body: BatchNodeCreate, db: GraphDatabase = Depends(_db)):
    """Bulk-create nodes with UNWIND. All nodes share the same labels."""
    try:
        nodes = db.batch_create_nodes(body.items, body.labels)
    except Exception as e:
        raise _handle_db_error(e)
    return NodeListResponse(
        data=PagedResult(
            items=nodes,
            page=PageInfo(offset=0, limit=len(nodes), total=len(nodes)),
        )
    )


@router.post("/batch/edges", response_model=NodeListResponse, summary="Batch create edges")
def batch_create_edges(body: BatchEdgeCreate, db: GraphDatabase = Depends(_db)):
    """Bulk-create edges with UNWIND. All edges share the same type."""
    try:
        edges = db.batch_create_edges(body.items, body.edge_type)
    except Exception as e:
        raise _handle_db_error(e)
    return NodeListResponse(
        data=PagedResult(
            items=edges,
            page=PageInfo(offset=0, limit=len(edges), total=len(edges)),
        )
    )


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

@router.post("/schema/indexes", response_model=MessageResponse, summary="Create an index")
def create_index(body: IndexCreate, db: GraphDatabase = Depends(_db)):
    """Create a node property index (optionally unique)."""
    from graph_db.models import IndexSpec
    try:
        db.create_index(IndexSpec(**body.model_dump()))
    except Exception as e:
        raise _handle_db_error(e)
    return MessageResponse(message=f"Index created on {body.label}.{body.properties}")


@router.delete("/schema/indexes", response_model=MessageResponse, summary="Drop an index")
def drop_index(body: IndexDrop, db: GraphDatabase = Depends(_db)):
    """Drop an existing index."""
    try:
        db.drop_index(body.label, body.properties)
    except Exception as e:
        raise _handle_db_error(e)
    return MessageResponse(message=f"Index dropped on {body.label}.{body.properties}")


@router.get("/schema/indexes", response_model=IndexListResponse, summary="List indexes")
def list_indexes(label: str | None = None, db: GraphDatabase = Depends(_db)):
    """List all indexes, optionally filtered by label."""
    try:
        indexes = db.list_indexes(label)
    except Exception as e:
        raise _handle_db_error(e)
    return IndexListResponse(data=indexes)


@router.post("/schema/constraints", response_model=MessageResponse, summary="Create a constraint")
def create_constraint(body: ConstraintCreate, db: GraphDatabase = Depends(_db)):
    """Create a database constraint."""
    from graph_db.models import ConstraintSpec
    try:
        db.create_constraint(ConstraintSpec(**body.model_dump()))
    except Exception as e:
        raise _handle_db_error(e)
    return MessageResponse(message=f"Constraint '{body.name}' created")


@router.delete("/schema/constraints/{name}", response_model=MessageResponse, summary="Drop a constraint")
def drop_constraint(name: str, db: GraphDatabase = Depends(_db)):
    """Drop a constraint by name."""
    try:
        db.drop_constraint(name)
    except Exception as e:
        raise _handle_db_error(e)
    return MessageResponse(message=f"Constraint '{name}' dropped")


@router.get("/schema/constraints", response_model=ConstraintListResponse, summary="List constraints")
def list_constraints(db: GraphDatabase = Depends(_db)):
    """List all database constraints."""
    try:
        constraints = db.list_constraints()
    except Exception as e:
        raise _handle_db_error(e)
    return ConstraintListResponse(data=constraints)


# ---------------------------------------------------------------------------
# Database info
# ---------------------------------------------------------------------------

@router.get("/info/nodes/count", response_model=CountResponse, summary="Count nodes")
def node_count(label: str | None = None, db: GraphDatabase = Depends(_db)):
    """Count nodes, optionally filtered by label."""
    return CountResponse(data=db.node_count(label))


@router.get("/info/edges/count", response_model=CountResponse, summary="Count edges")
def edge_count(edge_type: str | None = None, db: GraphDatabase = Depends(_db)):
    """Count edges, optionally filtered by type."""
    return CountResponse(data=db.edge_count(edge_type))


@router.get("/info/labels", response_model=StringListResponse, summary="List labels")
def labels(db: GraphDatabase = Depends(_db)):
    """List all node labels in the database."""
    return StringListResponse(data=db.labels())


@router.get("/info/edge-types", response_model=StringListResponse, summary="List edge types")
def edge_types(db: GraphDatabase = Depends(_db)):
    """List all relationship types in the database."""
    return StringListResponse(data=db.edge_types())
