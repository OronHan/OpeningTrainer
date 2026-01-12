import chess
import chess.pgn
import hashlib
import io
from typing import Dict, Tuple, Optional, List
import uuid
from backend.models import Course, CourseNode, GameInfo

def generate_node_id(fen: str, expected_moves: list[str]) -> str:
    """
    Generates a deterministic ID based on FEN and sorted expected moves.
    """
    # Sort moves to ensure ID is consistent regardless of move order in PGN
    sorted_moves = sorted(expected_moves)
    # Create a unique string signature
    data = f"{fen}|{'|'.join(sorted_moves)}"
    # Return first 16 chars of SHA-256 hash
    return hashlib.sha256(data.encode('utf-8')).hexdigest()[:16]

def parse_pgn_to_courses(pgn_content: str) -> List[Course]:
    """
    Parses a PGN string into a list of Course objects (one per game).
    """
    pgn = io.StringIO(pgn_content)
    
    courses = []

    while True:
        game = chess.pgn.read_game(pgn)
        if game is None:
            break
            
        nodes_map: Dict[str, CourseNode] = {}
        
        # Recursive function to build the tree for this specific game
        def process_node(game_node: chess.pgn.GameNode) -> str:
            board = game_node.board()
            fen = board.fen()
            
            # Collect all moves from variations at this point
            expected_moves = []
            for variation in game_node.variations:
                expected_moves.append(board.san(variation.move))
                
            node_id = generate_node_id(fen, expected_moves)
            
            # If node already exists (transposition within this game), return its ID
            if node_id in nodes_map:
                return node_id
                
            # Recursively process children
            child_ids = []
            for variation in game_node.variations:
                child_id = process_node(variation)
                child_ids.append(child_id)
                
            # Create and store the node
            nodes_map[node_id] = CourseNode(
                node_id=node_id,
                fen=fen,
                expected_moves=expected_moves,
                children=child_ids,
                comment=game_node.comment if game_node.comment else None
            )
            
            return node_id

        root_id = process_node(game)
        
        # Extract headers
        info = GameInfo(
            event=game.headers.get("Event", "?"),
            site=game.headers.get("Site", "?"),
            date=game.headers.get("Date", "?"),
            round=game.headers.get("Round", "?"),
            white=game.headers.get("White", "?"),
            black=game.headers.get("Black", "?"),
            result=game.headers.get("Result", "*")
        )
        
        # Generate a deterministic ID based on game info and root node
        unique_str = f"{info.event}{info.white}{info.black}{info.date}{root_id}"
        course_id = hashlib.sha256(unique_str.encode('utf-8')).hexdigest()[:16]
        
        courses.append(Course(
            id=course_id,
            info=info,
            root_node=root_id,
            nodes=nodes_map
        ))

    return courses

def validate_move(fen: str, move_req) -> Tuple[bool, str, Optional[chess.Move]]:
    """
    Validates if a move is legal and returns (is_legal, san_move, move_obj).
    """
    try:
        if fen == "start":
            board = chess.Board()
        else:
            board = chess.Board(fen)
    except ValueError:
        print(f"DEBUG: Invalid FEN: {fen}")
        return False, "", None
    
    # Check if it is a promotion move
    from_sq = chess.parse_square(move_req.from_square)
    to_sq = chess.parse_square(move_req.to_square)
    piece = board.piece_at(from_sq)
    is_promotion = False
    if piece and piece.piece_type == chess.PAWN:
        rank = chess.square_rank(to_sq)
        if (board.turn == chess.WHITE and rank == 7) or (board.turn == chess.BLACK and rank == 0):
            is_promotion = True

    # Construct UCI string
    uci_str = f"{move_req.from_square}{move_req.to_square}"
    
    # Only append promotion if it is a valid promotion character AND it is a promotion move
    if is_promotion and move_req.promotion and move_req.promotion.lower() in ['q', 'r', 'b', 'n']:
        uci_str += move_req.promotion.lower()
        
    try:
        move = chess.Move.from_uci(uci_str)
    except ValueError:
        print(f"DEBUG: Invalid UCI move string: {uci_str}")
        return False, "", None
        
    if move not in board.legal_moves:
        # Handle implicit promotion (e.g. UI sends e7e8 without q)
        # If it's a pawn moving to the last rank, try promoting to Queen by default
        if not move_req.promotion and move.from_square is not None and move.to_square is not None:
            piece = board.piece_at(move.from_square)
            if piece and piece.piece_type == chess.PAWN:
                rank = chess.square_rank(move.to_square)
                if (board.turn == chess.WHITE and rank == 7) or (board.turn == chess.BLACK and rank == 0):
                    move_q = chess.Move(move.from_square, move.to_square, promotion=chess.QUEEN)
                    if move_q in board.legal_moves:
                        move = move_q
                    else:
                        print(f"DEBUG: Move {uci_str} is illegal on FEN {fen}. Legal moves: {[m.uci() for m in board.legal_moves]}")
                        return False, "", None
                else:
                    print(f"DEBUG: Move {uci_str} is illegal. Legal moves: {[m.uci() for m in board.legal_moves]}")
                    return False, "", None
            else:
                print(f"DEBUG: Move {uci_str} is illegal. Legal moves: {[m.uci() for m in board.legal_moves]}")
                return False, "", None
        else:
            print(f"DEBUG: Move {uci_str} is illegal. Legal moves: {[m.uci() for m in board.legal_moves]}")
            return False, "", None
        
    san = board.san(move)
    return True, san, move
