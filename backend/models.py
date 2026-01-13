from typing import List, Dict, Optional
from pydantic import BaseModel, Field

# --- API Request/Response Models ---

class MoveRequest(BaseModel):
    from_square: str = Field(..., alias="from") # e.g., "e2"
    to_square: str = Field(..., alias="to")     # e.g., "e4"
    promotion: Optional[str] = 'q'  # e.g., "q", "r", "b", "n"

class MoveResponse(BaseModel):
    correct: bool
    fen: str
    feedback: Optional[str] = None
    san: Optional[str] = None

class NavigateRequest(BaseModel):
    node_id: str

class StateResponse(BaseModel):
    fen: str
    side_to_move: str  # "white" or "black"
    feedback: Optional[str] = None
    history: List[str] = []
    san_history: List[str] = []
    comment_history: List[Optional[str]] = []

# --- Internal Data Models (for JSON files) ---

class GameInfo(BaseModel):
    event: str = "?"
    site: str = "?"
    date: str = "?"
    round: str = "?"
    white: str = "?"
    black: str = "?"
    result: str = "*"

class GameListItem(BaseModel):
    id: str
    info: GameInfo

class SelectGameResponse(BaseModel):
    status: str
    game: GameInfo
    course: 'Course'

class CourseNode(BaseModel):
    node_id: str
    fen: str
    expected_moves: List[str]  # SAN moves, e.g., ["e4", "d4"]
    children: List[str]        # List of child node_ids
    comment: Optional[str] = None

class Course(BaseModel):
    id: str
    info: GameInfo
    root_node: str
    nodes: Dict[str, CourseNode]

class NodeProgress(BaseModel):
    seen: int = 0
    correct: int = 0
    last_seen: Optional[str] = None

# Resolve forward reference in SelectGameResponse
try:
    SelectGameResponse.model_rebuild()
except AttributeError:
    SelectGameResponse.update_forward_refs()
