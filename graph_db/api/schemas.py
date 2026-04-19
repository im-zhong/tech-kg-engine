"""Pydantic request/response schemas for the FastAPI layer."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field

from graph_db.models import (
    ConstraintSpec,
    Edge,
    IndexSpec,
    Node,
    PagedResult,
    Path,
    QueryResult,
)


# ---------------------------------------------------------------------------
# Node schemas
# ---------------------------------------------------------------------------

class NodeCreate(BaseModel):
    labels: list[str] = Field(..., description="Node labels / types")
    properties: dict[str, Any] = Field(default_factory=dict, description="Node properties")


class NodeMerge(BaseModel):
    labels: list[str] = Field(..., description="Node labels")
    identity_props: dict[str, Any] = Field(..., description="Properties that uniquely identify the node")
    properties: dict[str, Any] = Field(default_factory=dict, description="Additional properties to set on merge")


class NodeUpdate(BaseModel):
    properties: dict[str, Any] = Field(..., description="Properties to merge-update")


class NodeDelete(BaseModel):
    detach: bool = Field(default=False, description="If true, also delete attached edges")


class NodeFind(BaseModel):
    labels: list[str] = Field(..., description="Node labels to match")
    properties: dict[str, Any] = Field(default_factory=dict, description="Property equality filters")


# ---------------------------------------------------------------------------
# Edge schemas
# ---------------------------------------------------------------------------

class EdgeCreate(BaseModel):
    source_id: Any = Field(..., description="Source node ID")
    target_id: Any = Field(..., description="Target node ID")
    edge_type: str = Field(..., description="Relationship type")
    properties: dict[str, Any] = Field(default_factory=dict, description="Edge properties")


class EdgeMerge(BaseModel):
    source_id: Any = Field(..., description="Source node ID")
    target_id: Any = Field(..., description="Target node ID")
    edge_type: str = Field(..., description="Relationship type")
    identity_props: dict[str, Any] = Field(..., description="Properties that uniquely identify the edge")
    properties: dict[str, Any] = Field(default_factory=dict, description="Additional properties to set on merge")


class EdgeUpdate(BaseModel):
    properties: dict[str, Any] = Field(..., description="Properties to merge-update")


class EdgeFind(BaseModel):
    edge_type: str = Field(..., description="Relationship type to match")
    properties: dict[str, Any] = Field(default_factory=dict, description="Property equality filters")


# ---------------------------------------------------------------------------
# Traversal schemas
# ---------------------------------------------------------------------------

class NeighbourQuery(BaseModel):
    node_id: Any = Field(..., description="Node ID to start from")
    direction: str = Field(default="both", description="Direction: in, out, or both")
    edge_type: Optional[str] = Field(default=None, description="Filter by relationship type")
    limit: int = Field(default=100, description="Max results")


class NodeEdgesQuery(BaseModel):
    node_id: Any = Field(..., description="Node ID")
    direction: str = Field(default="both", description="Direction: in, out, or both")
    edge_type: Optional[str] = Field(default=None, description="Filter by relationship type")
    limit: int = Field(default=100, description="Max results")


class ShortestPathQuery(BaseModel):
    source_id: Any = Field(..., description="Source node ID")
    target_id: Any = Field(..., description="Target node ID")
    edge_type: Optional[str] = Field(default=None, description="Filter by relationship type")
    max_depth: int = Field(default=10, description="Maximum traversal depth")


# ---------------------------------------------------------------------------
# Query schemas
# ---------------------------------------------------------------------------

class CypherQuery(BaseModel):
    query: str = Field(..., description="Cypher query string")
    params: dict[str, Any] = Field(default_factory=dict, description="Query parameters")


# ---------------------------------------------------------------------------
# Batch schemas
# ---------------------------------------------------------------------------

class BatchNodeCreate(BaseModel):
    items: list[dict[str, Any]] = Field(..., description="List of property dicts, one per node")
    labels: list[str] = Field(..., description="Labels to apply to all nodes")


class BatchEdgeCreate(BaseModel):
    items: list[dict[str, Any]] = Field(..., description="Each item must have source_id, target_id, plus optional props")
    edge_type: str = Field(..., description="Relationship type for all edges")


# ---------------------------------------------------------------------------
# Schema management schemas
# ---------------------------------------------------------------------------

class IndexCreate(BaseModel):
    label: str
    properties: list[str]
    unique: bool = False


class IndexDrop(BaseModel):
    label: str
    properties: list[str]


class ConstraintCreate(BaseModel):
    name: str
    label: str
    property: str
    kind: str = "unique"


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class NodeResponse(BaseModel):
    success: bool = True
    data: Optional[Node] = None


class EdgeResponse(BaseModel):
    success: bool = True
    data: Optional[Edge] = None


class NodeListResponse(BaseModel):
    success: bool = True
    data: Optional[PagedResult] = None


class PathResponse(BaseModel):
    success: bool = True
    data: Optional[Path] = None


class QueryResponse(BaseModel):
    success: bool = True
    data: Optional[QueryResult] = None


class BoolResponse(BaseModel):
    success: bool = True
    data: bool = False


class CountResponse(BaseModel):
    success: bool = True
    data: int = 0


class StringListResponse(BaseModel):
    success: bool = True
    data: list[str] = Field(default_factory=list)


class IndexListResponse(BaseModel):
    success: bool = True
    data: list[IndexSpec] = Field(default_factory=list)


class ConstraintListResponse(BaseModel):
    success: bool = True
    data: list[ConstraintSpec] = Field(default_factory=list)


class MessageResponse(BaseModel):
    success: bool = True
    message: str = ""
