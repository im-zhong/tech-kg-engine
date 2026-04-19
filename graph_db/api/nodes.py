"""Node CRUD API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from graph_db.api.schemas import (
    NodeCreate,
    NodeFind,
    NodeMerge,
    NodeResponse,
    NodeListResponse,
    NodeUpdate,
)
from graph_db.base import GraphDatabase

router = APIRouter(prefix="/nodes", tags=["Nodes"])


def _db() -> GraphDatabase:
    """Dependency placeholder — overridden in app setup."""
    raise NotImplementedError


@router.post("", response_model=NodeResponse, summary="Create a node")
def create_node(body: NodeCreate, db: GraphDatabase = Depends(_db)):
    """Create a new node with the given labels and properties."""
    try:
        node = db.create_node(body.labels, body.properties)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return NodeResponse(data=node)


@router.post("/merge", response_model=NodeResponse, summary="Merge (upsert) a node")
def merge_node(body: NodeMerge, db: GraphDatabase = Depends(_db)):
    """Merge a node by identity properties. Creates if not exists, updates if exists."""
    try:
        node = db.merge_node(body.labels, body.identity_props, body.properties)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return NodeResponse(data=node)


@router.get("/{node_id}", response_model=NodeResponse, summary="Get a node by ID")
def get_node(node_id: str, db: GraphDatabase = Depends(_db)):
    """Retrieve a single node by its database-assigned ID."""
    node = db.get_node(node_id)
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    return NodeResponse(data=node)


@router.get("", response_model=NodeListResponse, summary="List nodes by label")
def list_nodes_by_label(
    label: str,
    limit: int = 100,
    offset: int = 0,
    db: GraphDatabase = Depends(_db),
):
    """List nodes with a given label, with pagination."""
    result = db.get_nodes_by_label(label, limit=limit, offset=offset)
    return NodeListResponse(data=result)


@router.post("/find", response_model=NodeListResponse, summary="Find nodes by labels and properties")
def find_nodes(body: NodeFind, limit: int = 100, offset: int = 0, db: GraphDatabase = Depends(_db)):
    """Find nodes matching all given labels and property equality checks."""
    result = db.find_nodes(body.labels, body.properties, limit=limit, offset=offset)
    return NodeListResponse(data=result)


@router.patch("/{node_id}", response_model=NodeResponse, summary="Update a node")
def update_node(node_id: str, body: NodeUpdate, db: GraphDatabase = Depends(_db)):
    """Merge-update properties on an existing node."""
    try:
        node = db.update_node(node_id, body.properties)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return NodeResponse(data=node)


@router.delete("/{node_id}", response_model=NodeResponse, summary="Delete a node")
def delete_node(
    node_id: str,
    detach: bool = False,
    db: GraphDatabase = Depends(_db),
):
    """Delete a node. Use detach=true to also delete attached edges."""
    try:
        deleted = db.delete_node(node_id, detach=detach)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    if not deleted:
        raise HTTPException(status_code=404, detail="Node not found or already deleted")
    return NodeResponse(data=None, success=True)
