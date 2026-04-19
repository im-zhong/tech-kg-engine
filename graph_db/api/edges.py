"""Edge CRUD API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from graph_db.api.schemas import (
    EdgeCreate,
    EdgeFind,
    EdgeMerge,
    EdgeResponse,
    EdgeUpdate,
    NodeListResponse,
)
from graph_db.base import GraphDatabase

router = APIRouter(prefix="/edges", tags=["Edges"])


def _db() -> GraphDatabase:
    raise NotImplementedError


@router.post("", response_model=EdgeResponse, summary="Create an edge")
def create_edge(body: EdgeCreate, db: GraphDatabase = Depends(_db)):
    """Create a directed edge from source to target."""
    edge = db.create_edge(body.source_id, body.target_id, body.edge_type, body.properties)
    return EdgeResponse(data=edge)


@router.post("/merge", response_model=EdgeResponse, summary="Merge (upsert) an edge")
def merge_edge(body: EdgeMerge, db: GraphDatabase = Depends(_db)):
    """Merge an edge by identity properties."""
    edge = db.merge_edge(
        body.source_id, body.target_id, body.edge_type,
        body.identity_props, body.properties,
    )
    return EdgeResponse(data=edge)


@router.get("/{edge_id}", response_model=EdgeResponse, summary="Get an edge by ID")
def get_edge(edge_id: str, db: GraphDatabase = Depends(_db)):
    """Retrieve a single edge by its database-assigned ID."""
    edge = db.get_edge(edge_id)
    if edge is None:
        raise HTTPException(status_code=404, detail="Edge not found")
    return EdgeResponse(data=edge)


@router.get("", response_model=NodeListResponse, summary="List edges by type")
def list_edges_by_type(
    edge_type: str,
    limit: int = 100,
    offset: int = 0,
    db: GraphDatabase = Depends(_db),
):
    """List edges of a given relationship type, with pagination."""
    result = db.get_edges_by_type(edge_type, limit=limit, offset=offset)
    return NodeListResponse(data=result)


@router.post("/find", response_model=NodeListResponse, summary="Find edges by type and properties")
def find_edges(body: EdgeFind, limit: int = 100, offset: int = 0, db: GraphDatabase = Depends(_db)):
    """Find edges matching type and property equality checks."""
    result = db.find_edges(body.edge_type, body.properties, limit=limit, offset=offset)
    return NodeListResponse(data=result)


@router.patch("/{edge_id}", response_model=EdgeResponse, summary="Update an edge")
def update_edge(edge_id: str, body: EdgeUpdate, db: GraphDatabase = Depends(_db)):
    """Merge-update properties on an existing edge."""
    edge = db.update_edge(edge_id, body.properties)
    return EdgeResponse(data=edge)


@router.delete("/{edge_id}", response_model=EdgeResponse, summary="Delete an edge")
def delete_edge(edge_id: str, db: GraphDatabase = Depends(_db)):
    """Delete an edge by ID."""
    deleted = db.delete_edge(edge_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Edge not found or already deleted")
    return EdgeResponse(data=None, success=True)
