import json
import os
from datetime import datetime
from typing import Dict, Optional, List, Tuple
from backend.models import Course, NodeProgress
import chess

COURSE_FILE = "course.json"
PROGRESS_FILE = "progress.json"

class DataStore:
    def __init__(self):
        self.courses: Dict[str, Course] = {}
        self.current_course_id: Optional[str] = None
        self.progress: Dict[str, NodeProgress] = {}
        self.current_node_id: Optional[str] = None
        self.last_feedback: Optional[str] = None
        self.session_history: List[str] = []
        self.session_san_history: List[str] = []
        self.session_comment_history: List[Optional[str]] = []

    def load_course(self, pgn_content: str):
        from backend.chess_logic import parse_pgn_to_courses
        
        course_list = parse_pgn_to_courses(pgn_content)
        self.courses = {c.id: c for c in course_list}
        
        # Default to the first course if available
        if self.courses:
            first_id = list(self.courses.keys())[0]
            self.current_course_id = first_id
            self.current_node_id = self.courses[first_id].root_node
            self.session_history = [self.courses[first_id].nodes[self.current_node_id].fen]
            self.session_san_history = []
            self.session_comment_history = [self.courses[first_id].nodes[self.current_node_id].comment]
            
        self._save_courses_to_disk()
        self._load_progress()

    def get_current_node(self):
        if not self.current_course_id or not self.current_node_id:
            raise ValueError("Course not initialized")
        return self.courses[self.current_course_id].nodes[self.current_node_id]

    def get_course_history(self, course_id: str) -> Tuple[List[str], List[str], List[Optional[str]]]:
        if course_id not in self.courses:
            return [], [], []
        
        course = self.courses[course_id]
        fen_history = []
        san_history = []
        comment_history = []
        board = chess.Board()
        
        # Traverse main line (first child)
        curr_node_id = course.root_node
        while curr_node_id:
            node = course.nodes[curr_node_id]
            fen_history.append(node.fen)
            comment_history.append(node.comment)

            if node.expected_moves:
                san_move = node.expected_moves[0]
                try:
                    board.set_fen(node.fen)
                    move = board.parse_san(san_move)
                    san_history.append(board.san(move))
                except ValueError:
                    san_history.append(san_move) # Fallback

                if node.children:
                    curr_node_id = node.children[0]
                else:
                    break
            else:
                break
        return fen_history, san_history, comment_history

    def navigate_to_node(self, node_id: str):
        if not self.current_course_id:
            return
        
        course = self.courses[self.current_course_id]
        
        # Helper to find path from root to target node
        def find_path(curr_id, target_id, current_path_nodes):
            if curr_id == target_id:
                return current_path_nodes + [curr_id]
            
            node = course.nodes[curr_id]
            for child_id in node.children:
                res = find_path(child_id, target_id, current_path_nodes + [curr_id])
                if res:
                    return res
            return None

        path_node_ids = find_path(course.root_node, node_id, [])
        
        if path_node_ids:
            self.current_node_id = node_id
            self.session_history = []
            self.session_san_history = []
            self.session_comment_history = []
            
            for i, nid in enumerate(path_node_ids):
                node = course.nodes[nid]
                self.session_history.append(node.fen)
                self.session_comment_history.append(node.comment)
                
                if i > 0:
                    parent_id = path_node_ids[i-1]
                    parent = course.nodes[parent_id]
                    try:
                        idx = parent.children.index(nid)
                        san = parent.expected_moves[idx]
                        self.session_san_history.append(san)
                    except ValueError:
                        pass

    def update_progress(self, node_id: str, is_correct: bool):
        if node_id not in self.progress:
            self.progress[node_id] = NodeProgress()
        
        p = self.progress[node_id]
        p.seen += 1
        if is_correct:
            p.correct += 1
        p.last_seen = datetime.now().isoformat()
        
        self._save_progress()

    def reset_state(self):
        if self.current_course_id:
            self.current_node_id = self.courses[self.current_course_id].root_node
            self.last_feedback = None
            self.session_history = [self.courses[self.current_course_id].nodes[self.current_node_id].fen]
            self.session_san_history = []
            self.session_comment_history = [self.courses[self.current_course_id].nodes[self.current_node_id].comment]

    def _save_courses_to_disk(self):
        # Save all courses as a list or dict
        if self.courses:
            data = {cid: c.model_dump() for cid, c in self.courses.items()}
            with open(COURSE_FILE, "w") as f:
                json.dump(data, f, indent=2)

    def _load_progress(self):
        if os.path.exists(PROGRESS_FILE):
            with open(PROGRESS_FILE, "r") as f:
                data = json.load(f)
                self.progress = {k: NodeProgress(**v) for k, v in data.items()}

    def _save_progress(self):
        # Convert models to dict for JSON serialization
        data = {k: v.model_dump() for k, v in self.progress.items()}
        with open(PROGRESS_FILE, "w") as f:
            json.dump(data, f, indent=2)

# Singleton instance
store = DataStore()
