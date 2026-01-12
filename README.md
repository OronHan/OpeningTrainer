# Chess Opening Trainer

A web-based application designed to help chess players learn, practice, and test themselves on opening repertoires from PGN files.


<img width="1694" height="1065" alt="image" src="https://github.com/user-attachments/assets/5b8204dc-775c-438d-a37a-fd7f9c2e1188" />

<img width="993" height="469" alt="image" src="https://github.com/user-attachments/assets/cc4b4593-ef5e-4352-aa76-8eed43c32c6a" />

<img width="426" height="661" alt="image" src="https://github.com/user-attachments/assets/d573142e-e37f-47d5-bd12-03753371017c" />



## Features

*   **PGN-based Repertoires**: Add your own PGN files to the `files` folder or use the provided samples to start training.
*   **Interactive Chessboard**: Play through opening lines on a beautiful, interactive chessboard powered by `react-chessboard`.
*   **Two Main Modes**:
    *   **Book Mode**: Explore the moves of a selected game. The application provides instant feedback on whether your move is part of the line.
    *   **Variations Mode**: View a tree of all opening variations within your PGN file. See which lines you've trained, tested, or made mistakes in.
*   **Dedicated Training Modules**:
    *   **Train**: A guided walkthrough of a specific variation. The application shows you the correct move to play.
    *   **Test**: A quiz mode where you must remember the moves for a variation. The app tracks your mistakes to help you identify weak spots.
    *   **Practice Bot**: A dynamic mode that selects random lines for you to play against. It handles transpositions by switching lines if you play a valid alternative.
    *   **Fix Errors**: A targeted session that helps you review and correct mistakes made in previous sessions.
*   **Mistake Tracking**: The application logs mistakes made during tests, helping you focus your training on lines you struggle with.
*   **User-Friendly Interface**: Flip the board, navigate between moves, and see comments from your PGN file.
*   **Backend Support**: Comes with a Python backend to handle game logic, PGN parsing, and state management.

## Technology Stack

*   **Frontend**: React.js
*   **Backend**: Python 
*   **UI Components**: `react-chessboard` for the interactive board.

## Setup and Installation

To run this project locally, you will need to set up both the backend and the frontend.

### Prerequisites

*   Python 3.7+
*   Node.js and npm

### Windows Quick Start

1.  Run `fix_backend.bat` to set up the Python environment and install dependencies.
2.  Run `run.bat` to start the application.

### Manual Setup (Mac/Linux)

### 1. Backend Setup

The backend server handles the chess logic and PGN file processing.

```bash
# 1. Navigate to the project's root directory
cd OpeningTrainer

# 2. Create a Python virtual environment
# On Windows:
python -m venv venv
venv\\Scripts\\activate

# On macOS/Linux:
python3 -m venv venv
source venv/bin/activate

# 3. Install the required Python packages
pip install -r requirements.txt

# 4. Run the backend server
# (Assuming the main file is `main.py` and the app instance is `app`)
uvicorn main:app --reload --port 8000
```

The backend should now be running at `http://127.0.0.1:8000`.

> **Windows Users**: If you run into trouble, the `fix_backend.bat` script can automatically clean and reinstall the backend environment for you. Just double-click it and follow the prompts.

### 2. Frontend Setup

The frontend provides the user interface in your browser.

```bash
# 1. Open a new terminal and navigate to the frontend directory
cd OpeningTrainer/frontend

# 2. Install the required npm packages
npm install

# 3. Start the React development server
npm start
```

The application should automatically open in your web browser at `http://localhost:3000`.

## How to Use

1.  **Start the Application**: Run `run.bat` (Windows) or start the servers manually.
2.  **Load a Repertoire**:
    *   On the home screen, click **"Use Sample Dataset"** to load pre-packaged games.
    *   Manually place your `.pgn` files into the `files` folder. They will appear under **"Available Files"** after refreshing.
3.  **Select a Game**: Once in the trainer view, the sidebar on the left will show all the games loaded from your PGN. Click one to begin.
4.  **Choose Your Training Side**: Use the radio buttons to select whether you are training the lines for White or Black.
5.  **Explore the Book**: In the "Book" tab, you can play moves on the board. The app will tell you if the move is correct according to the selected game. Use the navigation arrows to step through the game's moves.
6.  **Train Variations**:
    *   Click the **"Variations"** tab to see a tree of all the opening lines.
    *   Find a line you want to practice and click the **"Train"** button. The app will guide you through the moves.
    *   Click the **"Test"** button to quiz yourself. The app will wait for your input and track any mistakes.
7.  **Practice Bot**:
    *   Click the **"Practice Bot"** tab to start a session with a random line. The bot adapts to your moves if you play valid alternatives.
8.  **Fix Errors**:
    *   Click the **"Fix Errors"** tab to specifically target and correct mistakes made in previous sessions.
