from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import random
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

class PracticeStartRequest(BaseModel):
    game_id: str
    color: str

class PracticeMoveResponse(BaseModel):
    correct: bool
    fen: str
    san: str | None = None
    bot_san: str | None = None
    feedback: str
    game_over: bool = False

# Resolve recursive reference for Pydantic
try:
    VariationNode.model_rebuild()
except AttributeError:
    VariationNode.update_forward_refs()

def get_random_path(course, start_node_id):
    """Returns a list of node_ids representing a path from start_node to a leaf."""
    path = [start_node_id]
    current = start_node_id
    # Safety limit to prevent infinite loops in case of circular references (though unlikely in trees)
    for _ in range(200):
        if current not in course.nodes:
            break
        node = course.nodes[current]
        if not node.children:
            break
        next_id = random.choice(node.children)
        path.append(next_id)
        current = next_id
    return path

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

@app.post("/practice/start", response_model=StateResponse)
async def start_practice(req: PracticeStartRequest):
    if req.game_id not in store.courses:
        raise HTTPException(status_code=404, detail="Game not found")
    
    store.current_course_id = req.game_id
    store.reset_state()
    
    course = store.courses[req.game_id]
    
    # Pick a random line from root
    store.practice_line = get_random_path(course, course.root_node)
    store.practice_mistakes = 0
    store.fixing_mistake = None
    
    # If user is Black, Bot (White) must play first move
    if req.color == "black":
        if len(store.practice_line) > 1:
            next_node_id = store.practice_line[1]
            next_node = course.nodes[next_node_id]
            root_node = course.nodes[course.root_node]
            
            # Find SAN for the move
            try:
                idx = root_node.children.index(next_node_id)
                bot_san = root_node.expected_moves[idx]
                
                # Apply move
                store.current_node_id = next_node_id
                store.session_history.append(next_node.fen)
                store.session_san_history.append(bot_san)
                store.session_comment_history.append(next_node.comment)
                store.last_feedback = f"Bot played {bot_san}"
            except ValueError:
                pass

    return await get_state()

@app.post("/fix_errors/start", response_model=StateResponse)
async def start_fix_errors(req: PracticeStartRequest):
    if req.game_id not in store.courses:
        raise HTTPException(status_code=404, detail="Game not found")
    
    store.current_course_id = req.game_id
    store.reset_state()
    course = store.courses[req.game_id]
    
    # 1. Get unresolved mistakes
    mistakes = score_manager.get_unresolved_mistakes(req.game_id)
    if not mistakes:
        return StateResponse(
            fen=store.get_current_node().fen,
            side_to_move="white",
            feedback="No errors to fix! Great job."
        )
    
    # 2. Pick a mistake (e.g., the first one)
    target_mistake = mistakes[0]
    
    # 3. Find the node corresponding to this mistake's FEN
    target_node_id = None
    for node in course.nodes.values():
        # Simple FEN match (ignoring move clocks might be safer, but exact match for now)
        if node.fen == target_mistake['fen']:
            target_node_id = node.node_id
            break
    
    if not target_node_id:
        # If node not found (maybe PGN changed), skip this mistake (or handle gracefully)
        # For now, just fallback to random
        store.practice_line = get_random_path(course, course.root_node)
        store.fixing_mistake = None
        return await get_state()

    # 4. Construct path: Root -> Mistake Node -> Random Leaf
    path_to_mistake = store.find_path_to_node(req.game_id, target_node_id)
    continuation = get_random_path(course, target_node_id)
    # continuation includes target_node_id, so we slice it out to avoid duplicate
    store.practice_line = path_to_mistake + continuation[1:]
    store.fixing_mistake = target_mistake
    
    # 5. Auto-play moves up to the mistake point (handled by frontend usually, but we need to set state)
    # Actually, we want the user to play from start or from the mistake?
    # "go over every variation" implies playing the line.
    # Let's start from root.
    
    # If user is Black, Bot (White) must play first move
    if req.color == "black":
        if len(store.practice_line) > 1:
            next_node_id = store.practice_line[1]
            next_node = course.nodes[next_node_id]
            root_node = course.nodes[course.root_node]
            try:
                idx = root_node.children.index(next_node_id)
                bot_san = root_node.expected_moves[idx]
                store.current_node_id = next_node_id
                store.session_history.append(next_node.fen)
                store.session_san_history.append(bot_san)
                store.session_comment_history.append(next_node.comment)
                store.last_feedback = f"Bot played {bot_san}"
            except ValueError:
                pass

    return await get_state()

@app.post("/practice/move", response_model=PracticeMoveResponse)
async def practice_move(move_req: MoveRequest):
    current_node = store.get_current_node()
    course = store.courses[store.current_course_id]
    
    # 1. Validate legality
    is_legal, san_move, move_obj = validate_move(current_node.fen, move_req)
    
    if not is_legal:
        return PracticeMoveResponse(correct=False, fen=current_node.fen, feedback="Illegal move")

    # 2. Determine context in practice line
    try:
        current_idx = store.practice_line.index(current_node.node_id)
    except (ValueError, AttributeError):
        current_idx = -1
        store.practice_line = [current_node.node_id] # Fallback

    next_node_in_line_id = None
    if current_idx != -1 and current_idx + 1 < len(store.practice_line):
        next_node_in_line_id = store.practice_line[current_idx + 1]

    # 3. Check if move is in repertoire (children of current node)
    played_child_id = None
    for i, move_str in enumerate(current_node.expected_moves):
        if move_str == san_move:
            played_child_id = current_node.children[i]
            break
    
    if played_child_id:
        # Move is valid in repertoire
        
        # Check if this move resolves the mistake we are fixing
        if store.fixing_mistake:
            # Check FEN and Expected Move
            # We need the UCI of the move played
            if current_node.fen == store.fixing_mistake['fen']:
                # The user played 'san_move'. Is it the expected move?
                # The mistake record stores 'expected' in UCI.
                if move_obj.uci() == store.fixing_mistake['expected']:
                    score_manager.resolve_mistake(store.current_course_id, store.fixing_mistake['fen'], store.fixing_mistake['expected'])
                    # We don't clear store.fixing_mistake yet, just mark it resolved in DB
        
        # Check if it's an alternative (not the one in the current random line)
        if played_child_id != next_node_in_line_id:
            # Switch target line to follow this alternative
            new_continuation = get_random_path(course, played_child_id)
            # Splice: path up to current + new path from child
            store.practice_line = store.practice_line[:current_idx+1] + new_continuation
            # Note: new_continuation[0] is played_child_id
        
        # Apply User Move
        store.current_node_id = played_child_id
        played_node = course.nodes[played_child_id]
        store.session_history.append(played_node.fen)
        store.session_san_history.append(san_move)
        store.session_comment_history.append(played_node.comment)
        
        # 4. Bot Reply
        # We are now at played_child_id. Bot plays next move in practice_line.
        # The index of played_child_id in the (potentially new) line is current_idx + 1
        new_current_idx = current_idx + 1
        
        bot_san = None
        game_over = False
        feedback = f"Correct! {san_move}"
        
        if new_current_idx + 1 < len(store.practice_line):
            bot_next_id = store.practice_line[new_current_idx + 1]
            bot_next_node = course.nodes[bot_next_id]
            
            try:
                idx = played_node.children.index(bot_next_id)
                bot_san = played_node.expected_moves[idx]
                
                # Apply Bot Move
                store.current_node_id = bot_next_id
                store.session_history.append(bot_next_node.fen)
                store.session_san_history.append(bot_san)
                store.session_comment_history.append(bot_next_node.comment)
                
                feedback = f"Correct! Bot played {bot_san}"
                
                if new_current_idx + 1 == len(store.practice_line) - 1:
                    game_over = True
                    feedback += ". Line complete!"
                    if getattr(store, "practice_mistakes", 0) == 0:
                        score_manager.update_last_tested(store.current_course_id)
                        score_manager.record_node_test(store.current_course_id, store.practice_line[-1], True)
                    else:
                        score_manager.record_node_training(store.current_course_id, store.practice_line[-1])
            except ValueError:
                feedback = "Error finding bot move"
        else:
            game_over = True
            feedback = "Line complete!"
            if getattr(store, "practice_mistakes", 0) == 0:
                score_manager.update_last_tested(store.current_course_id)
                score_manager.record_node_test(store.current_course_id, store.practice_line[-1], True)
            else:
                score_manager.record_node_training(store.current_course_id, store.practice_line[-1])
            
        return PracticeMoveResponse(
            correct=True,
            fen=store.get_current_node().fen,
            san=san_move,
            bot_san=bot_san,
            feedback=feedback,
            game_over=game_over
        )

    else:
        # Incorrect move (not in repertoire)
        if not hasattr(store, "practice_mistakes"):
            store.practice_mistakes = 0
        store.practice_mistakes += 1
        
        expected_san = "Unknown"
        if next_node_in_line_id:
            try:
                idx = current_node.children.index(next_node_in_line_id)
                expected_san = current_node.expected_moves[idx]
                
                # Record mistake
                # We need UCI for expected move
                board = chess.Board(current_node.fen)
                expected_move_obj = board.parse_san(expected_san)
                score_manager.record_mistake(
                    store.current_course_id, 
                    current_node.fen, 
                    move_obj.uci(), 
                    expected_move_obj.uci()
                )
            except:
                pass
        
        return PracticeMoveResponse(
            correct=False,
            fen=current_node.fen,
            feedback=f"Incorrect. Expected: {expected_san}"
        )

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
    mistakes = [m for m in scores.get("mistakes", []) if not m.get('resolved', False)]
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
