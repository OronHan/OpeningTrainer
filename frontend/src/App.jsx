import { useState, useEffect } from 'react'
import { Chessboard } from 'react-chessboard'

const API_URL = "http://127.0.0.1:8000";

// Import pieces directly so the bundler can find them in src/public
import wP from './public/pieces/wP.svg';
import wN from './public/pieces/wN.svg';
import wB from './public/pieces/wB.svg';
import wR from './public/pieces/wR.svg';
import wQ from './public/pieces/wQ.svg';
import wK from './public/pieces/wK.svg';
import bP from './public/pieces/bP.svg';
import bN from './public/pieces/bN.svg';
import bB from './public/pieces/bB.svg';
import bR from './public/pieces/bR.svg';
import bQ from './public/pieces/bQ.svg';
import bK from './public/pieces/bK.svg';

const pieceImages = {
  wP, wN, wB, wR, wQ, wK,
  bP, bN, bB, bR, bQ, bK
};

const customPieces = (() => {
  const pieces = ['wP', 'wN', 'wB', 'wR', 'wQ', 'wK', 'bP', 'bN', 'bB', 'bR', 'bQ', 'bK'];
  const returnPieces = {};
  pieces.forEach((p) => {
    returnPieces[p] = ({ squareWidth }) => (
      <div
        style={{
          width: squareWidth,
          height: squareWidth,
          backgroundImage: `url(${pieceImages[p]})`,
          backgroundSize: "100%",
        }}
      />
    );
  });
  return returnPieces;
})();

// Component to render the move list with variations in boxes
const MoveList = ({ course, currentNodeId, onNavigate }) => {
  if (!course) return null;

  // Helper to render a sequence of moves
  const renderSequence = (startNodeId) => {
    const elements = [];
    let currId = startNodeId;
    let count = 0;

    while (currId && count < 5000) { // Safety break
      count++;
      const node = course.nodes[currId];
      if (!node || !node.children || node.children.length === 0) break;

      const mainChildId = node.children[0];
      const mainMoveSan = node.expected_moves[0];
      const mainChildNode = course.nodes[mainChildId];
      
      const fenParts = node.fen.split(' ');
      const moveNum = fenParts[5];
      const isWhite = fenParts[1] === 'w';
      
      const isActive = mainChildId === currentNodeId;

      // Check for variations (alternatives to the main move)
      const variations = [];
      for (let i = 1; i < node.children.length; i++) {
        const childId = node.children[i];
        variations.push({
          childId: childId,
          moveSan: node.expected_moves[i],
          comment: course.nodes[childId]?.comment
        });
      }

      elements.push(
        <span key={mainChildId} className="move-segment">
          <span 
            className={`move-san ${isActive ? 'active' : ''}`}
            onClick={(e) => { e.stopPropagation(); onNavigate(mainChildId); }}
          >
            {isWhite && <span className="move-num">{moveNum}.</span>}
            {mainMoveSan}
          </span>
          {mainChildNode?.comment && <span className="move-comment-inline"> ({mainChildNode.comment})</span>}
          
          {variations.length > 0 && (
            <div className="variation-box">
              {variations.map(v => (
                <div key={v.childId} className="variation-line">
                  <span 
                    className={`move-san variation-start ${v.childId === currentNodeId ? 'active' : ''}`}
                    onClick={(e) => { e.stopPropagation(); onNavigate(v.childId); }}
                  >
                     {isWhite ? `${moveNum}.` : `${moveNum}...`} {v.moveSan}
                  </span>
                  {v.comment && <span className="move-comment-inline"> ({v.comment})</span>}
                  {renderSequence(v.childId)}
                </div>
              ))}
            </div>
          )}
        </span>
      );

      currId = mainChildId;
    }
    return elements;
  };

  return <div className="moves-list">{renderSequence(course.root_node)}</div>;
};

const TestView = ({ variation, userColor, gameId, onExit }) => {
  const [stepIndex, setStepIndex] = useState(0);
  const [mode, setMode] = useState('demo'); // 'demo' | 'input'
  const [currentFen, setCurrentFen] = useState("start"); // The board state shown to user
  const [feedback, setFeedback] = useState("");
  const [isCorrect, setIsCorrect] = useState(null);
  const [mistakesMade, setMistakesMade] = useState(0);

  // Helper to check whose turn it is from FEN
  const getTurn = (fen) => {
    if (!fen || fen === 'start') return 'white';
    const parts = fen.split(' ');
    return parts[1] === 'w' ? 'white' : 'black';
  };

  useEffect(() => {
    startMove(0);
  }, [variation]);

  const startMove = (index) => {
    if (index >= variation.moves.length) {
      setFeedback("Test Complete!");
      // Report completion
      if (gameId) {
        const success = mistakesMade === 0;
        fetch(`${API_URL}/report_test_complete`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            game_id: gameId, 
            node_id: variation.last_node_id,
            success: success
          })
        }).catch(console.error);
      }
      setMode('complete');
      return;
    }

    setStepIndex(index);
    
    // Determine FEN before this move
    const prevFen = index === 0 ? "start" : variation.moves[index - 1].fen;
    setCurrentFen(prevFen);

    const turn = getTurn(prevFen);
    const move = variation.moves[index];

    setIsCorrect(null);
    // Don't reset mistakesMade here, it accumulates for the session

    if (turn === userColor) {
      // User's turn
      setMode('input');
      setFeedback("Your turn");
    } else {
      // Opponent's turn (Auto-play)
      setMode('demo');
      setFeedback(`Opponent plays: ${move.san}`);
      // Delay to show the position before move
      setTimeout(() => {
        setCurrentFen(move.fen); // Make the move
        // Delay to show the result before next move
        setTimeout(() => {
          startMove(index + 1);
        }, 800);
      }, 800);
    }
  };

  const onDrop = async (source, target) => {
    if (mode !== 'input') return false;

    const targetMove = variation.moves[stepIndex];
    
    // Validate locally/statelessly
    try {
      const res = await fetch(`${API_URL}/validate_direct`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          fen: currentFen, 
          from_square: source, 
          to_square: target, 
          promotion: 'q' 
        })
      });
      const data = await res.json();

      // Compare UCI (robust) or SAN (fallback)
      const isMatch = data.uci === targetMove.uci || data.san === targetMove.san;

      if (data.valid && isMatch) {
        // Correct
        setIsCorrect(true);
        setFeedback(`Correct! ${data.san}`);
        setCurrentFen(data.new_fen); // Snap to result
        
        setTimeout(() => {
          startMove(stepIndex + 1);
        }, 1000);
        return true;
      } else {
        // Incorrect
        setIsCorrect(false);
        setMistakesMade(prev => prev + 1);
        // Report mistake
        if (gameId) {
          fetch(`${API_URL}/report_mistake`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
              game_id: gameId, fen: currentFen, played: data.uci || "unknown", expected: targetMove.uci 
            })
          }).catch(console.error);
        }
        console.log(`Mismatch: Got ${data.uci} (${data.san}), Expected ${targetMove.uci} (${targetMove.san}). Error: ${data.error}`);
        setFeedback(`Incorrect. Expected: ${targetMove.san}`);
        return false;
      }
    } catch (e) {
      console.error(e);
      return false;
    }
  };

  return (
    <div className="training-container">
      <div className="training-header">
        <h3>Test: {variation.name}</h3>
        <button onClick={onExit}>Exit Test</button>
      </div>
      <div className="training-board-wrapper">
        <Chessboard position={currentFen} onPieceDrop={onDrop} boardWidth={400} boardOrientation={userColor} />
      </div>
      <div className={`training-feedback ${isCorrect === true ? 'correct' : isCorrect === false ? 'incorrect' : ''}`}>
        {feedback}
        {mode === 'demo' && variation.moves[stepIndex]?.comment && (
          <div className="training-comment">{variation.moves[stepIndex].comment}</div>
        )}
      </div>
      <div className="training-progress">
        Move {stepIndex + 1} / {variation.moves.length}
      </div>
    </div>
  );
};

const TrainingView = ({ variation, userColor, gameId, onExit }) => {
  const [stepIndex, setStepIndex] = useState(0);
  const [currentFen, setCurrentFen] = useState("start");
  const [feedback, setFeedback] = useState("");
  const [completed, setCompleted] = useState(false);

  const getTurn = (fen) => {
    if (!fen || fen === 'start') return 'white';
    const parts = fen.split(' ');
    return parts[1] === 'w' ? 'white' : 'black';
  };

  useEffect(() => {
    startMove(0);
  }, [variation]);

  const startMove = (index) => {
    if (index >= variation.moves.length) {
      setFeedback("Training Complete!");
      if (gameId) {
        fetch(`${API_URL}/report_training_complete`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ game_id: gameId, node_id: variation.last_node_id })
        }).catch(console.error);
      }

      setCompleted(true);
      return;
    }
    setCompleted(false);
    setStepIndex(index);
    
    const prevFen = index === 0 ? "start" : variation.moves[index - 1].fen;
    setCurrentFen(prevFen);

    const turn = getTurn(prevFen);
    const move = variation.moves[index];

    if (turn === userColor) {
      setFeedback(`Play: ${move.san}`);
    } else {
      setFeedback(`Opponent plays: ${move.san}`);
      setTimeout(() => {
        setCurrentFen(move.fen);
        setTimeout(() => {
          startMove(index + 1);
        }, 800);
      }, 800);
    }
  };

  const onDrop = async (source, target) => {
    if (completed) return false;
    const turn = getTurn(currentFen);
    if (turn !== userColor) return false;

    const targetMove = variation.moves[stepIndex];
    
    try {
      const res = await fetch(`${API_URL}/validate_direct`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          fen: currentFen, 
          from_square: source, 
          to_square: target, 
          promotion: 'q' 
        })
      });
      const data = await res.json();
      const isMatch = data.uci === targetMove.uci || data.san === targetMove.san;

      if (data.valid && isMatch) {
        setCurrentFen(data.new_fen);
        setTimeout(() => {
          startMove(stepIndex + 1);
        }, 500);
        return true;
      } else {
        return false;
      }
    } catch (e) {
      console.error(e);
      return false;
    }
  };

  return (
    <div className="training-container">
      <div className="training-header">
        <h3>Training: {variation.name}</h3>
        <button onClick={onExit}>Exit Training</button>
      </div>
      <div className="training-board-wrapper">
        <Chessboard position={currentFen} onPieceDrop={onDrop} boardWidth={400} boardOrientation={userColor} />
      </div>
      <div className="training-feedback">
        {feedback}
        {variation.moves[stepIndex]?.comment && (
          <div className="training-comment">{variation.moves[stepIndex].comment}</div>
        )}
      </div>
      <div className="training-progress">
        Move {stepIndex + 1} / {variation.moves.length}
      </div>
    </div>
  );
};

// Recursive component to display variations tree
const VariationTreeItem = ({ node, onTrain, onTest }) => {
  const [expanded, setExpanded] = useState(false);

  let nameColor = '#fff';
  if (node.tested_today) nameColor = '#69db7c'; // Green
  else if (node.error_count > 0) nameColor = '#ff6b6b'; // Red
  else if (node.trained_today) nameColor = '#4dabf7'; // Blue

  return (
    <div className="variation-node">
      <div className="variation-header" onClick={() => setExpanded(!expanded)}>
        <span className="toggle-icon">{node.children.length > 0 ? (expanded ? '▼' : '▶') : '•'}</span>
        <span className="variation-name" style={{color: nameColor}}>
          {node.name}
        </span>
        {node.error_count > 0 && (
          <span className="error-badge" title={`${node.error_count} mistakes in this line`}>{node.error_count}</span>
        )}
        <span className="variation-length">({node.moves.length} moves)</span>
        <div className="variation-actions">
          <button 
            className="action-btn train-btn"
            onClick={(e) => { e.stopPropagation(); onTrain(node); }}
          >
            Train
          </button>
          <button 
            className="action-btn test-btn"
            onClick={(e) => { e.stopPropagation(); onTest(node); }}
          >
            Test
          </button>
        </div>
      </div>
      
      {expanded && (
        <div className="variation-content">
          <div className="variation-moves">
            {node.moves.map(m => m.san).join(" ")}
          </div>
          {node.children.length > 0 && (
            <div className="variation-children">
              {node.children.map((child, idx) => (
                <VariationTreeItem key={idx} node={child} onTrain={onTrain} onTest={onTest} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

const VariationsView = ({ gameId, onStartTraining, onStartTest }) => {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    setData(null);
    setError(null);
    if (!gameId) return;
    
    fetch(`${API_URL}/variations/${gameId}`)
      .then(r => {
        if (!r.ok) throw new Error("Failed to fetch variations");
        return r.json();
      })
      .then(setData)
      .catch(err => setError(err.message));
  }, [gameId]);

  if (error) return <div style={{color: 'red', padding: '20px'}}>Error loading variations: {error}</div>;
  return data ? (
    <div className="variations-container">
      <VariationTreeItem node={data} onTrain={onStartTraining} onTest={onStartTest} />
    </div>
  ) : <div>Loading variations...</div>;
};

// Basic styles for the variations tree
const variationStyles = `
  .variations-container { padding: 20px; overflow-y: auto; height: 100%; }
  .variation-node { margin-left: 20px; border-left: 1px solid #555; }
  .variation-header { 
    cursor: pointer; padding: 5px; display: flex; align-items: center; gap: 10px; 
    user-select: none;
  }
  .variation-header:hover { background-color: #333; border-radius: 4px; }
  .toggle-icon { font-size: 0.8em; color: #ccc; width: 12px; }
  .variation-name { font-weight: bold; color: #fff; }
  .error-badge { background: #ff4444; color: white; font-size: 0.7em; padding: 1px 5px; border-radius: 10px; font-weight: bold; }
  .variation-length { color: #aaa; font-size: 0.9em; }
  .variation-actions { margin-left: auto; display: flex; gap: 5px; }
  .action-btn { 
    padding: 2px 8px; font-size: 0.7em; color: white; 
    border: none; border-radius: 3px; cursor: pointer;
  }
  .train-btn { background: #2196F3; }
  .train-btn:hover { background: #45a049; }
  .test-btn { background: #4CAF50; }
  .test-btn:hover { background: #388E3C; }
  .variation-content { padding-left: 14px; }
  .variation-moves { 
    font-family: monospace; color: #ddd; background: #2a2a2a; 
    padding: 8px; border-radius: 4px; margin: 5px 0 10px 0;
    line-height: 1.4; border: 1px solid #444;
  }
  .empty-state { padding: 40px; text-align: center; color: #aaa; font-style: italic; }
  
  .training-container { padding: 20px; display: flex; flex-direction: column; align-items: center; gap: 20px; }
  .training-header { width: 100%; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #444; padding-bottom: 10px; }
  .training-feedback { font-size: 1.2em; font-weight: bold; min-height: 60px; text-align: center; }
  .training-comment { font-size: 0.8em; font-weight: normal; color: #aaa; margin-top: 5px; font-style: italic; }
`;

function App() {
  const [view, setView] = useState('home'); // 'home' | 'trainer'
  const [games, setGames] = useState([]);
  const [selectedGameId, setSelectedGameId] = useState(null);
  const [fen, setFen] = useState("start");
  const [feedback, setFeedback] = useState("");
  const [isCorrect, setIsCorrect] = useState(null);
  const [sourceSquare, setSourceSquare] = useState(null);
  const [history, setHistory] = useState(["start"]);
  const [sanHistory, setSanHistory] = useState([]);
  const [commentHistory, setCommentHistory] = useState([]);
  const [moveIndex, setMoveIndex] = useState(0);
  const [course, setCourse] = useState(null);
  const [currentNodeId, setCurrentNodeId] = useState(null);
  const [orientation, setOrientation] = useState('white');
  const [activeModule, setActiveModule] = useState('book'); // 'book' | 'variations'
  const [trainingVariation, setTrainingVariation] = useState(null); // If set, shows TrainingView
  const [testVariation, setTestVariation] = useState(null); // If set, shows TestView
  const [trainingOrientation, setTrainingOrientation] = useState('white');
  const [availableFiles, setAvailableFiles] = useState([]);

  const checkHealth = async () => {
    try {
      const res = await fetch(`${API_URL}/health`);
      if (res.ok) {
        setFeedback("");
      } else {
        setFeedback("Backend server is returning errors.");
      }
    } catch (e) {
      console.error("Health check failed:", e);
      setFeedback("Backend is unreachable. Please ensure the server is running on port 8000.");
    }
  };

  useEffect(() => {
    checkHealth();

    if (view === 'trainer') {
      fetch(`${API_URL}/games`)
        .then(res => res.json())
        .then(data => setGames(data))
        .catch(err => setFeedback("Error connecting to backend"));
    }

    if (view === 'home') {
      fetch(`${API_URL}/files`)
        .then(res => res.json())
        .then(setAvailableFiles)
        .catch(console.error);
    }
  }, [view]);

  const fetchState = async (atStart = false) => {
    try {
      const res = await fetch(`${API_URL}/state`);
      const data = await res.json();
      if (data.history && data.history.length > 0) {
        setHistory(data.history);
        setSanHistory(data.san_history || []);
        setCommentHistory(data.comment_history || []);
        const newIndex = atStart ? 0 : data.history.length - 1;
        setMoveIndex(newIndex);
        setFen(data.history[newIndex]);
        // We don't get the current node ID directly from state usually, but we can infer or it will be set by navigate
      } else {
        setFen(data.fen);
        setHistory([data.fen]);
        setSanHistory([]);
        setCommentHistory([]);
        setMoveIndex(0);
      }
      if (data.feedback) setFeedback(data.feedback);
      return data;
    } catch (e) { console.error(e); }
  };

  const handleSelectGame = async (id) => {
    setSelectedGameId(id);
    const res = await fetch(`${API_URL}/select/${id}`, { method: "POST" });
    const data = await res.json();
    setCourse(data.course);
    setCurrentNodeId(data.course.root_node);
    
    await fetchState(true);
    setFeedback("");
    setIsCorrect(null);
    setSourceSquare(null);
  };

  const handleNavigate = async (nodeId) => {
    try {
      const res = await fetch(`${API_URL}/navigate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ node_id: nodeId })
      });
      const data = await res.json();
      setFen(data.fen);
      setHistory(data.history);
      setSanHistory(data.san_history);
      setCommentHistory(data.comment_history);
      setMoveIndex(data.history.length - 1);
      setCurrentNodeId(nodeId);
    } catch (e) { console.error(e); }
  };

  const handleMoveNavigation = (index) => {
    setMoveIndex(index);
    setFen(history[index]);
  };

  const onDrop = (source, target) => {
    if (moveIndex !== history.length - 1) return false;
    handleMove(source, target);
    return true;
  };

  const onSquareClick = (square) => {
    if (moveIndex !== history.length - 1) return;
    if (!sourceSquare) {
      setSourceSquare(square);
      return;
    }
    handleMove(sourceSquare, square);
    setSourceSquare(null);
  };

  const handleMove = async (from, to) => {
    console.log("Move played:", { from, to });
    try {
      const res = await fetch(`${API_URL}/move`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ from, to, promotion: 'q' })
      });
      const data = await res.json();
      setFeedback(data.feedback);
      setIsCorrect(data.correct);
      if (data.correct) {
        setFen(data.fen);
        setHistory(prev => [...prev, data.fen]);
        setSanHistory(prev => [...prev, data.san]);
        setCommentHistory(prev => [...prev, null]); // Optimistic update, fetchState will correct
        setMoveIndex(prev => prev + 1);
        
        // Update current node ID based on the move
        if (course && currentNodeId) {
            const node = course.nodes[currentNodeId];
            const moveIndex = node.expected_moves.indexOf(data.san);
            if (moveIndex !== -1) {
                setCurrentNodeId(node.children[moveIndex]);
            }
        }
      } else {
        setTimeout(() => {
          fetchState(); // Resync with backend after incorrect move
        }, 500);
      }
    } catch (e) { setFeedback("Error making move"); }
  };

  const handleReset = async () => {
    await fetch(`${API_URL}/reset`, { method: "POST" });
    const data = await fetchState(true);
    let turn = "White";
    if (data && data.history && data.history.length > 0) {
      const parts = data.history[0].split(' ');
      if (parts.length >= 2) turn = parts[1] === 'w' ? "White" : "Black";
    }
    setFeedback(`Position reset. ${turn} to move.`);
    if (course) setCurrentNodeId(course.root_node);
    setIsCorrect(null);
  };

  const handleFlipBoard = () => {
    setOrientation(prev => prev === 'white' ? 'black' : 'white');
  };

  const resetTrainerState = () => {
    setSelectedGameId(null);
    setCourse(null);
    setCurrentNodeId(null);
    setFen("start");
    setHistory(["start"]);
    setSanHistory([]);
    setCommentHistory([]);
    setMoveIndex(0);
    setFeedback("Select a game to start");
    setIsCorrect(null);
    setSourceSquare(null);
    setActiveModule('book');
    setTrainingVariation(null);
    setTestVariation(null);
  };

  const handleLoadSample = async () => {
    setFeedback("Loading...");
    try {
      const res = await fetch(`${API_URL}/load_sample`, { method: 'POST' });
      if (!res.ok) throw new Error(`Server returned ${res.status}`);
      const data = await res.json();
      if (data.count === 0) {
        throw new Error("No games found in sample dataset.");
      }
      resetTrainerState();
      setView('trainer');
    } catch (e) {
      console.error(e);
      setFeedback(`Error loading sample: ${e.message}`);
    }
  };

  const handleLoadFile = async (filename) => {
    setFeedback(`Loading ${filename}...`);
    try {
      const res = await fetch(`${API_URL}/load_file`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename })
      });
      if (!res.ok) throw new Error("Failed to load file");
      
      resetTrainerState();
      setView('trainer');
    } catch (e) {
      setFeedback(`Error loading file: ${e.message}`);
    }
  };

  const handleUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    
    setFeedback("Uploading...");
    try {
      const res = await fetch(`${API_URL}/upload`, {
          method: 'POST',
          body: formData
      });
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ detail: `Upload failed with status: ${res.status}` }));
        throw new Error(errorData.detail || "Upload failed");
      }
      resetTrainerState();
      setView('trainer');
    } catch (e) {
      console.error(e);
      setFeedback(`Error uploading file: ${e.message}`);
    } finally {
      event.target.value = null; // Reset input so same file can be selected again
    }
  };

  // If in training mode, render only the training view in the main area
  const renderMainContent = () => {
    if (trainingVariation) {
      return <TrainingView 
        variation={trainingVariation} 
        userColor={trainingOrientation}
        gameId={selectedGameId}
        onExit={() => setTrainingVariation(null)} 
      />;
    }
    if (testVariation) {
      return <TestView 
        variation={testVariation} 
        userColor={trainingOrientation}
        gameId={selectedGameId}
        onExit={() => setTestVariation(null)} 
      />;
    }

    return (
      <>
        <div className="module-tabs">
          <button 
            className={activeModule === 'book' ? 'active-tab' : ''} 
            onClick={() => setActiveModule('book')}
          >
            Book
          </button>
          <button 
            className={activeModule === 'variations' ? 'active-tab' : ''} 
            onClick={() => setActiveModule('variations')}
          >
            Variations
          </button>
        </div>
        
        {activeModule === 'book' && (
          <>
            <div className="board-container">
              <Chessboard 
                boardWidth={560}
                position={fen || "start"}
                boardOrientation={orientation}
                customPieces={customPieces}
                onPieceDrop={onDrop}
                onSquareClick={onSquareClick}
                customSquareStyles={
                  sourceSquare ? { [sourceSquare]: { backgroundColor: 'rgba(255, 255, 0, 0.4)' } } : {}
                }
              />
            </div>
            
            <div className="status-panel">
              <div className={`feedback ${isCorrect === true ? 'correct' : isCorrect === false ? 'incorrect' : ''}`}>
                {feedback}
              </div>
              {commentHistory[moveIndex] && (
                <div className="comment-box">
                  {commentHistory[moveIndex]}
                </div>
              )}
              <div style={{ display: 'flex', justifyContent: 'center', gap: '10px', marginBottom: '10px' }}>
                <button disabled={moveIndex === 0} onClick={() => {
                  setMoveIndex(0);
                  setFen(history[0]);
                }}>&lt;&lt;</button>
                <button disabled={moveIndex === 0} onClick={() => {
                  setMoveIndex(moveIndex - 1);
                  setFen(history[moveIndex - 1]);
                }}>&lt;</button>
                <button disabled={moveIndex === history.length - 1} onClick={() => {
                  setMoveIndex(moveIndex + 1);
                  setFen(history[moveIndex + 1]);
                }}>&gt;</button>
                <button disabled={moveIndex === history.length - 1} onClick={() => {
                  setMoveIndex(history.length - 1);
                  setFen(history[history.length - 1]);
                }}>&gt;&gt;</button>
              </div>
              <div style={{ display: 'flex', justifyContent: 'center', gap: '10px' }}>
                <button onClick={handleFlipBoard}>Flip Board</button>
                <button onClick={handleReset}>Reset Position</button>
              </div>
            </div>
          </>
        )}
        {activeModule === 'variations' && (
          course ? (
            <VariationsView 
              gameId={selectedGameId} 
              onStartTraining={(node) => setTrainingVariation(node)}
              onStartTest={(node) => setTestVariation(node)}
            />
          ) : (
            <div className="empty-state">Please select a game from the sidebar to view variations.</div>
          )
        )}
      </>
    );
  };

  if (view === 'home') {
    return (
      <div className="home-container">
        <h1>Chess Opening Trainer</h1>
        {feedback && (
          <div style={{ color: '#ff6b6b', marginBottom: '20px', fontWeight: 'bold', textAlign: 'center' }}>
            {feedback}
            <br/>
            <button onClick={checkHealth} style={{marginTop: '10px', fontSize: '0.8em'}}>Retry Connection</button>
          </div>
        )}
        <div className="home-actions">
          <button onClick={handleLoadSample}>Use Sample Dataset</button>
          <label htmlFor="file-upload" className="button-label">Upload PGN File</label>
          <input id="file-upload" type="file" accept=".pgn" onChange={handleUpload} style={{display: 'none'}} />
        </div>
        
        {availableFiles.length > 0 && (
          <div style={{marginTop: '30px', width: '100%', maxWidth: '400px'}}>
            <h3 style={{borderBottom: '1px solid #ccc', paddingBottom: '10px'}}>Available Files</h3>
            <ul className="game-list" style={{maxHeight: '300px', overflowY: 'auto'}}>
              {availableFiles.map(f => (
                <li key={f} className="game-item" onClick={() => handleLoadFile(f)}>{f}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="container">
      <style>{variationStyles}</style>
      <div className="sidebar left-sidebar">
        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px'}}>
          <h2 style={{margin: 0}}>Trainer</h2>
          <button onClick={() => setView('home')} style={{padding: '4px 8px', fontSize: '0.8em'}}>Home</button>
        </div>
        
        <div style={{marginBottom: '15px', padding: '10px', background: '#f5f5f5', borderRadius: '4px'}}>
          <label style={{display: 'block', marginBottom: '5px', fontWeight: 'bold', color: '#333'}}>Training As:</label>
          <div style={{display: 'flex', gap: '10px'}}>
            <label style={{color: '#333'}}><input type="radio" name="tr_side" checked={trainingOrientation === 'white'} onChange={() => setTrainingOrientation('white')} /> White</label>
            <label style={{color: '#333'}}><input type="radio" name="tr_side" checked={trainingOrientation === 'black'} onChange={() => setTrainingOrientation('black')} /> Black</label>
          </div>
        </div>

        <ul className="game-list">
          {games.map(g => (
            <li 
              key={g.id} 
              className={`game-item ${selectedGameId === g.id ? 'active' : ''}`}
              onClick={() => handleSelectGame(g.id)}
            >
              <strong>{g.info.white} vs {g.info.black}</strong><br/>
              <small>{g.info.event} ({g.info.result})</small>
            </li>
          ))}
        </ul>
      </div>

      <div className="main-content">
        {renderMainContent()}
      </div>

      <div className="sidebar right-sidebar">
        <div className="move-history">
          <h4>Moves</h4>
          {course ? (
            <MoveList 
              course={course} 
              currentNodeId={currentNodeId}
              onNavigate={handleNavigate} 
            />
          ) : (
            <div>Select a game</div>
          )}
        </div>
      </div>
    </div>
  )
}

export default App
