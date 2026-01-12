from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import chess
from typing import List
from pydantic import BaseModel
import os
from datetime import datetime, date

from .models import MoveRequest, MoveResponse, StateResponse, Course, GameListItem, SelectGameResponse, NavigateRequest
from .data_store import store
from .chess_logic import validate_move
from . import score_manager

app = FastAPI(title="Chess Opening Trainer")

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MoveInfo(BaseModel):
    san: str
    uci: str
    comment: str | None = None
    fen: str

class VariationNode(BaseModel):
    name: str
    moves: List[MoveInfo]
    children: List['VariationNode'] = []
    error_count: int = 0
    last_node_id: str = ""
    trained_today: bool = False
    tested_today: bool = False

# Resolve recursive reference for Pydantic
try:
    VariationNode.model_rebuild()
except AttributeError:
    VariationNode.update_forward_refs()

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.on_event("startup")
async def startup_event():
    # Ensure directories exist
    score_manager.ensure_directories()
    # Load sample PGN on startup
    try:
        with open("sample.pgn", "r") as f:
            pgn_content = f.read()
            store.load_course(pgn_content)
            print("Course loaded successfully.")
    except FileNotFoundError:
        print("Warning: sample.pgn not found. Please add a PGN file.")

@app.get("/games", response_model=List[GameListItem])
async def list_games():
    """Returns a list of available games/variations to play."""
    return [
        {"id": c.id, "info": c.info} 
        for c in store.courses.values()
    ]

@app.post("/select/{game_id}", response_model=SelectGameResponse)
async def select_game(game_id: str):
    if game_id not in store.courses:
        raise HTTPException(status_code=404, detail="Game not found")
    store.current_course_id = game_id
    store.reset_state()
    fen_history, san_history, comment_history = store.get_course_history(game_id)
    store.session_history = fen_history
    store.session_san_history = san_history
    store.session_comment_history = comment_history
    score_manager.update_last_studied(game_id)
    return SelectGameResponse(status="selected", game=store.courses[game_id].info, course=store.courses[game_id])

@app.post("/upload")
async def upload_pgn(file: UploadFile = File(...)):
    content = await file.read()
    # Attempt to decode, fallback to latin-1 if utf-8 fails
    try:
        pgn_content = content.decode("utf-8")
    except UnicodeDecodeError:
        pgn_content = content.decode("latin-1")

    try:
        store.load_course(pgn_content)
    except Exception as e:
        print(f"Error parsing PGN: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to parse PGN file. It may be malformed.")

    return {"status": "success", "count": len(store.courses)}

@app.post("/load_sample")
async def load_sample():
    # Re-trigger the startup logic
    await startup_event()
    return {"status": "success", "count": len(store.courses)}

@app.post("/navigate", response_model=StateResponse)
async def navigate(req: NavigateRequest):
    store.navigate_to_node(req.node_id)
    try:
        node = store.get_current_node()
        board = chess.Board(node.fen)
        side = "white" if board.turn == chess.WHITE else "black"
        current_fen = store.session_history[-1] if store.session_history else node.fen
        
        return StateResponse(
            fen=current_fen,
            side_to_move=side,
            feedback=store.last_feedback,
            history=store.session_history,
            san_history=store.session_san_history,
            comment_history=store.session_comment_history
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/state", response_model=StateResponse)
async def get_state():
    try:
        node = store.get_current_node()
        board = chess.Board(node.fen)
        side = "white" if board.turn == chess.WHITE else "black"
        current_fen = store.session_history[-1] if store.session_history else node.fen
        
        return StateResponse(
            fen=current_fen,
            side_to_move=side,
            feedback=store.last_feedback,
            history=store.session_history,
            san_history=store.session_san_history,
            comment_history=store.session_comment_history
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/move", response_model=MoveResponse)
async def make_move(move_req: MoveRequest):
    print(f"Received move request: {move_req}")
    current_node = store.get_current_node()
    
    # 1. Validate legality
    is_legal, san_move, move_obj = validate_move(current_node.fen, move_req)
    
    if not is_legal:
        print(f"Illegal move attempted: {move_req} on FEN: {current_node.fen}")
        return MoveResponse(
            correct=False,
            fen=current_node.fen,
            feedback="Illegal move",
            san=None
        )

    # 2. Check against expected moves
    # Clean SAN (remove checks/mates symbols for comparison if needed, 
    # though python-chess usually handles generation consistently)
    if san_move in current_node.expected_moves:
        # CORRECT MOVE
        store.update_progress(current_node.node_id, is_correct=True)
        
        # Advance board to find next node
        board = chess.Board(current_node.fen)
        board.push(move_obj)
        next_fen = board.fen()
        
        # Find the child node that matches this new FEN
        next_node_id = None
        if store.current_course_id:
            current_course = store.courses[store.current_course_id]
            for child_id in current_node.children:
                child = current_course.nodes[child_id]
                # We compare FENs (ignoring move clocks if necessary, but exact match is safer for now)
                # Standard FEN comparison usually works if generated by same library
                if child.fen.split(" ")[0] == next_fen.split(" ")[0]: 
                    next_node_id = child_id
                    break
        
        if next_node_id:
            store.current_node_id = next_node_id
            store.last_feedback = f"Correct! {san_move}"
            store.session_history.append(store.get_current_node().fen)
            store.session_san_history.append(san_move)
            store.session_comment_history.append(store.get_current_node().comment)
            return MoveResponse(correct=True, fen=store.get_current_node().fen, feedback=store.last_feedback, san=san_move)
        else:
            # End of line
            store.last_feedback = "Line complete!"
            store.session_history.append(next_fen)
            store.session_san_history.append(san_move)
            store.session_comment_history.append(None) # No node for end state yet
            return MoveResponse(correct=True, fen=next_fen, feedback="Line complete!", san=san_move)

    else:
        # INCORRECT MOVE (but legal)
        store.update_progress(current_node.node_id, is_correct=False)
        expected_str = ", ".join(current_node.expected_moves)
        store.last_feedback = f"Incorrect. Expected: {expected_str}"
        
        # Reset to root on failure (as per plan)
        store.reset_state()
        
        return MoveResponse(
            correct=False, 
            fen=store.get_current_node().fen, 
            feedback=store.last_feedback,
            san=san_move
        )

@app.post("/reset")
async def reset():
    store.reset_state()
    return {"status": "reset"}

class ValidateRequest(BaseModel):
    fen: str
    from_square: str
    to_square: str
    promotion: str | None = None

@app.post("/validate_direct")
async def validate_direct(req: ValidateRequest):
    """Stateless validation for training mode."""
    try:
        # MoveRequest expects 'from' and 'to' aliases (used in JSON), not from_square/to_square args directly
        move_req = MoveRequest(**{
            "from": req.from_square,
            "to": req.to_square,
            "promotion": req.promotion
        })
        is_legal, san, move_obj = validate_move(req.fen, move_req)
        if not is_legal:
            return {"valid": False, "error": "Move validation failed (illegal move or invalid FEN)"}
        
        if req.fen == "start":
            board = chess.Board()
        else:
            board = chess.Board(req.fen)
        board.push(move_obj)
        return {"valid": True, "san": san, "uci": move_obj.uci(), "new_fen": board.fen()}
    except Exception as e:
        print(f"Validation error: {e}")
        return {"valid": False, "error": str(e)}

class MistakeReport(BaseModel):
    game_id: str
    fen: str
    played: str
    expected: str

@app.post("/report_mistake")
async def report_mistake(report: MistakeReport):
    score_manager.record_mistake(report.game_id, report.fen, report.played, report.expected)
    return {"status": "recorded"}

class TestReport(BaseModel):
    game_id: str
    node_id: str
    success: bool

@app.post("/report_test_complete")
async def report_test_complete(report: TestReport):
    score_manager.update_last_tested(report.game_id)
    score_manager.record_node_test(report.game_id, report.node_id, report.success)
    return {"status": "recorded"}

class TrainingReport(BaseModel):
    game_id: str
    node_id: str

@app.post("/report_training_complete")
async def report_training_complete(report: TrainingReport):
    score_manager.record_node_training(report.game_id, report.node_id)
    return {"status": "recorded"}

class LoadFileRequest(BaseModel):
    filename: str

@app.get("/files")
async def list_files():
    if not os.path.exists(score_manager.FILES_DIR):
        return []
    return [f for f in os.listdir(score_manager.FILES_DIR) if f.endswith(".pgn")]

@app.post("/load_file")
async def load_file(req: LoadFileRequest):
    file_path = os.path.join(score_manager.FILES_DIR, req.filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    with open(file_path, "r") as f:
        content = f.read()
    
    # Clear existing courses to switch context to this file
    store.courses = {}
    try:
        store.load_course(content)
        return {"status": "success", "count": len(store.courses)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse PGN: {str(e)}")

@app.get("/variations/{game_id}", response_model=VariationNode)
async def get_variations(game_id: str):
    if game_id not in store.courses:
        raise HTTPException(status_code=404, detail="Game not found")
    
    course = store.courses[game_id]
    
    # Load scores to calculate error counts
    scores = score_manager.load_score(game_id)
    mistakes = scores.get("mistakes", [])
    mistake_counts = {}
    for m in mistakes:
        # Key is (fen, expected_move_uci)
        key = (m['fen'], m['expected'])
        mistake_counts[key] = mistake_counts.get(key, 0) + 1
    
    # Prepare date for today check
    today_start = datetime.combine(date.today(), datetime.min.time()).timestamp()

    def build_variation_tree(node_id, current_line_moves, deviation_name="Main Line", initial_errors=0):
        # Start with the moves inherited from the parent path
        moves = list(current_line_moves)
        child_variations = []
        
        curr_node_id = node_id
        current_errors = initial_errors
        
        # Traverse down the main line of this variation until we hit a leaf or branch
        while True:
            node = course.nodes[curr_node_id]
            
            if not node.children:
                break
            
            # The first child is considered the "Main" continuation for this specific line
            main_child_id = node.children[0]
            main_move_san = node.expected_moves[0]
            main_child_node = course.nodes[main_child_id]
            
            # Calculate UCI for robust comparison
            board = chess.Board(node.fen)
            try:
                main_move_obj = board.parse_san(main_move_san)
                main_uci = main_move_obj.uci()
            except:
                main_uci = ""

            # Add errors for this move (continuation of current line)
            current_errors += mistake_counts.get((node.fen, main_uci), 0)

            move_info = MoveInfo(
                san=main_move_san,
                uci=main_uci,
                comment=main_child_node.comment,
                fen=main_child_node.fen
            )
            moves.append(move_info)
            
            # Any other children (index > 0) are sidelines/deviations
            for i in range(1, len(node.children)):
                sideline_child_id = node.children[i]
                sideline_move_san = node.expected_moves[i]
                sideline_child_node = course.nodes[sideline_child_id]
                
                try:
                    sideline_move_obj = board.parse_san(sideline_move_san)
                    sideline_uci = sideline_move_obj.uci()
                except:
                    sideline_uci = ""

                # Calculate errors for the deviation move
                deviation_errors = mistake_counts.get((node.fen, sideline_uci), 0)

                sideline_move_info = MoveInfo(
                    san=sideline_move_san,
                    uci=sideline_uci,
                    comment=sideline_child_node.comment,
                    fen=sideline_child_node.fen
                )
                
                # Calculate move name (e.g., "10... Bd3")
                # ply is 0-based index. The move we just added to 'moves' is at len(moves)-1
                # The sideline is an alternative to that move, so it shares the same ply.
                ply = len(moves) - 1
                move_num = (ply // 2) + 1
                is_white = (ply % 2) == 0
                
                name_str = f"{move_num}. {sideline_move_san}" if is_white else f"{move_num}... {sideline_move_san}"
                
                # The sideline inherits moves up to the deviation point, then adds the deviation move
                sideline_start_moves = moves[:-1] + [sideline_move_info]
                
                # Recursively build the tree for the sideline
                child_var = build_variation_tree(sideline_child_id, sideline_start_moves, name_str, initial_errors=deviation_errors)
                child_variations.append(child_var)
                
                # Propagate errors up from the sideline to the parent
                current_errors += child_var.error_count
            
            # Continue down the main path of this variation
            curr_node_id = main_child_id
            
        # Check status for leaves
        is_leaf = (len(child_variations) == 0)
        trained_today = False
        tested_today = False
        
        if is_leaf:
            stats = scores.get('node_stats', {}).get(curr_node_id, {})
            last_trained = stats.get('last_trained', 0)
            last_tested = stats.get('last_tested', 0)
            last_test_success = stats.get('last_test_success', False)
            
            if last_trained >= today_start:
                trained_today = True
            if last_tested >= today_start and last_test_success:
                tested_today = True

        return VariationNode(
            name=deviation_name, 
            moves=moves, 
            children=child_variations, 
            error_count=current_errors,
            last_node_id=curr_node_id,
            trained_today=trained_today,
            tested_today=tested_today
        )

    return build_variation_tree(course.root_node, [])
