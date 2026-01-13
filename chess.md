Core
Colors
Constants for the side to move or the color of a piece.

chess.WHITE: chess.Color= True
chess.BLACK: chess.Color= False
You can get the opposite color using not color.

Piece types
chess.PAWN: chess.PieceType= 1
chess.KNIGHT: chess.PieceType= 2
chess.BISHOP: chess.PieceType= 3
chess.ROOK: chess.PieceType= 4
chess.QUEEN: chess.PieceType= 5
chess.KING: chess.PieceType= 6
chess.piece_symbol(piece_type: chess.PieceType)→ str[source]
chess.piece_name(piece_type: chess.PieceType)→ str[source]
Squares
chess.A1: chess.Square= 0
chess.B1: chess.Square= 1
and so on to

chess.G8: chess.Square= 62
chess.H8: chess.Square= 63
chess.SQUARES= [chess.A1, chess.B1, ..., chess.G8, chess.H8]
chess.SQUARE_NAMES= ['a1', 'b1', ..., 'g8', 'h8']
chess.FILE_NAMES= ['a', 'b', ..., 'g', 'h']
chess.RANK_NAMES= ['1', '2', ..., '7', '8']
chess.parse_square(name: str)→ chess.Square[source]
Gets the square index for the given square name (e.g., a1 returns 0).

Raises
:
ValueError if the square name is invalid.

chess.square_name(square: chess.Square)→ str[source]
Gets the name of the square, like a3.

chess.square(file_index: int, rank_index: int)→ chess.Square[source]
Gets a square number by file and rank index.

chess.square_file(square: chess.Square)→ int[source]
Gets the file index of the square where 0 is the a-file.

chess.square_rank(square: chess.Square)→ int[source]
Gets the rank index of the square where 0 is the first rank.

chess.square_distance(a: chess.Square, b: chess.Square)→ int[source]
Gets the Chebyshev distance (i.e., the number of king steps) from square a to b.

chess.square_manhattan_distance(a: chess.Square, b: chess.Square)→ int[source]
Gets the Manhattan/Taxicab distance (i.e., the number of orthogonal king steps) from square a to b.

chess.square_knight_distance(a: chess.Square, b: chess.Square)→ int[source]
Gets the Knight distance (i.e., the number of knight moves) from square a to b.

chess.square_mirror(square: chess.Square)→ chess.Square[source]
Mirrors the square vertically.


Pieces
classchess.Piece(piece_type: chess.PieceType, color: chess.Color)[source]
A piece with type and color.

piece_type: PieceType
The piece type.

color: Color
The piece color.

symbol()→ str[source]
Gets the symbol P, N, B, R, Q or K for white pieces or the lower-case variants for the black pieces.

unicode_symbol(*, invert_color: bool = False)→ str[source]
Gets the Unicode character for the piece.

classmethodfrom_symbol(symbol: str)→ Piece[source]
Creates a Piece instance from a piece symbol.

Raises
:
ValueError if the symbol is invalid.

Moves
classchess.Move(from_square: chess.Square, to_square: chess.Square, promotion: chess.PieceType | None = None, drop: chess.PieceType | None = None)[source]
Represents a move from a square to a square and possibly the promotion piece type.

Drops and null moves are supported.

from_square: Square
The source square.

to_square: Square
The target square.

promotion: PieceType | None= None
The promotion piece type or None.

drop: PieceType | None= None
The drop piece type or None.

uci()→ str[source]
Gets a UCI string for the move.

For example, a move from a7 to a8 would be a7a8 or a7a8q (if the latter is a promotion to a queen).

The UCI representation of a null move is 0000.

classmethodfrom_uci(uci: str)→ Move[source]
Parses a UCI string.

Raises
:
InvalidMoveError if the UCI string is invalid.

classmethodnull()→ Move[source]
Gets a null move.

A null move just passes the turn to the other side (and possibly forfeits en passant capturing). Null moves evaluate to False in boolean contexts.

>>> import chess
>>>
>>> bool(chess.Move.null())
False


Board
chess.STARTING_FEN= 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
The FEN for the standard chess starting position.

chess.STARTING_BOARD_FEN= 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR'
The board part of the FEN for the standard chess starting position.

classchess.Board(fen: str | None = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1', *, chess960: bool = False)[source]
A BaseBoard, additional information representing a chess position, and a move stack.

Provides move generation, validation, parsing, attack generation, game end detection, and the capability to make and unmake moves.

The board is initialized to the standard chess starting position, unless otherwise specified in the optional fen argument. If fen is None, an empty board is created.

Optionally supports chess960. In Chess960, castling moves are encoded by a king move to the corresponding rook square. Use chess.Board.from_chess960_pos() to create a board with one of the Chess960 starting positions.

It’s safe to set turn, castling_rights, ep_square, halfmove_clock and fullmove_number directly.

Warning

It is possible to set up and work with invalid positions. In this case, Board implements a kind of “pseudo-chess” (useful to gracefully handle errors or to implement chess variants). Use is_valid() to detect invalid positions.

turn: Color
The side to move (chess.WHITE or chess.BLACK).

castling_rights: Bitboard
Bitmask of the rooks with castling rights.

To test for specific squares:

>>> import chess
>>>
>>> board = chess.Board()
>>> bool(board.castling_rights & chess.BB_H1)  # White can castle with the h1 rook
True
To add a specific square:

>>> board.castling_rights |= chess.BB_A1
Use set_castling_fen() to set multiple castling rights. Also see has_castling_rights(), has_kingside_castling_rights(), has_queenside_castling_rights(), has_chess960_castling_rights(), clean_castling_rights().

fullmove_number: int
Counts move pairs. Starts at 1 and is incremented after every move of the black side.

halfmove_clock: int
The number of half-moves since the last capture or pawn move.

promoted: Bitboard
A bitmask of pieces that have been promoted.

chess960: bool
Whether the board is in Chess960 mode. In Chess960 castling moves are represented as king moves to the corresponding rook square.

ep_square: Square | None
The potential en passant square on the third or sixth rank or None.

Use has_legal_en_passant() to test if en passant capturing would actually be possible on the next move.

move_stack: List[Move]
The move stack. Use Board.push(), Board.pop(), Board.peek() and Board.clear_stack() for manipulation.

propertylegal_moves: LegalMoveGenerator
A dynamic list of legal moves.

>>> import chess
>>>
>>> board = chess.Board()
>>> board.legal_moves.count()
20
>>> bool(board.legal_moves)
True
>>> move = chess.Move.from_uci("g1f3")
>>> move in board.legal_moves
True
Wraps generate_legal_moves() and is_legal().

 
propertypseudo_legal_moves: PseudoLegalMoveGenerator
A dynamic list of pseudo-legal moves, much like the legal move list.

Pseudo-legal moves might leave or put the king in check, but are otherwise valid. Null moves are not pseudo-legal. Castling moves are only included if they are completely legal.

Wraps generate_pseudo_legal_moves() and is_pseudo_legal().

reset()→ None[source]
Restores the starting position.

clear()→ None[source]
Clears the board.

Resets move stack and move counters. The side to move is white. There are no rooks or kings, so castling rights are removed.

In order to be in a valid status(), at least kings need to be put on the board.

clear_board()→ None[source]
Clears the board.

Board also clears the move stack.

clear_stack()→ None[source]
Clears the move stack.

root()→ Self[source]
Returns a copy of the root position.

ply()→ int[source]
Returns the number of half-moves since the start of the game, as indicated by fullmove_number and turn.

If moves have been pushed from the beginning, this is usually equal to len(board.move_stack). But note that a board can be set up with arbitrary starting positions, and the stack can be cleared.

checkers()→ SquareSet[source]
Gets the pieces currently giving check.

Returns a set of squares.

is_check()→ bool[source]
Tests if the current side to move is in check.

gives_check(move: Move)→ bool[source]
Probes if the given move would put the opponent in check. The move must be at least pseudo-legal.

gives_checkmate(move: Move)→ bool[source]
Probes if the given move would put the opponent in checkmate. The move must be at least pseudo-legal.

is_legal(move: Move)→ bool[source]
Check if a move is legal in the current position.

is_variant_end()→ bool[source]
Checks if the game is over due to a special variant end condition.

Note, for example, that stalemate is not considered a variant-specific end condition (this method will return False), yet it can have a special result in suicide chess (any of is_variant_loss(), is_variant_win(), is_variant_draw() might return True).

is_variant_loss()→ bool[source]
Checks if the current side to move lost due to a variant-specific condition.

is_variant_win()→ bool[source]
Checks if the current side to move won due to a variant-specific condition.

is_variant_draw()→ bool[source]
Checks if a variant-specific drawing condition is fulfilled.

is_game_over(*, claim_draw: bool = False)→ bool[source]
Check if the game is over by any rule.

The game is not considered to be over by the fifty-move rule or threefold repetition, unless claim_draw is given. Note that checking the latter can be slow.

result(*, claim_draw: bool = False)→ str[source]
Return the result of a game: 1-0, 0-1, 1/2-1/2, or *.

The game is not considered to be over by the fifty-move rule or threefold repetition, unless claim_draw is given. Note that checking the latter can be slow.

outcome(*, claim_draw: bool = False)→ Outcome | None[source]
Checks if the game is over due to checkmate, stalemate, insufficient material, the seventyfive-move rule, fivefold repetition, or a variant end condition. Returns the chess.Outcome if the game has ended, otherwise None.

Alternatively, use is_game_over() if you are not interested in who won the game and why.

The game is not considered to be over by the fifty-move rule or threefold repetition, unless claim_draw is given. Note that checking the latter can be slow.

is_checkmate()→ bool[source]
Checks if the current position is a checkmate.

is_stalemate()→ bool[source]
Checks if the current position is a stalemate.

is_insufficient_material()→ bool[source]
Checks if neither side has sufficient winning material (has_insufficient_material()).

has_insufficient_material(color: chess.Color)→ bool[source]
Checks if color has insufficient winning material.

This is guaranteed to return False if color can still win the game.

The converse does not necessarily hold: The implementation only looks at the material, including the colors of bishops, but not considering piece positions. So fortress positions or positions with forced lines may return False, even though there is no possible winning line.

is_seventyfive_moves()→ bool[source]
Since the 1st of July 2014, a game is automatically drawn (without a claim by one of the players) if the half-move clock since a capture or pawn move is equal to or greater than 150. Other means to end a game take precedence.

is_fivefold_repetition()→ bool[source]
Since the 1st of July 2014 a game is automatically drawn (without a claim by one of the players) if a position occurs for the fifth time. Originally this had to occur on consecutive alternating moves, but this has since been revised.

can_claim_draw()→ bool[source]
Checks if the player to move can claim a draw by the fifty-move rule or by threefold repetition.

Note that checking the latter can be slow.

is_fifty_moves()→ bool[source]
Checks that the clock of halfmoves since the last capture or pawn move is greater or equal to 100, and that no other means of ending the game (like checkmate) take precedence.

can_claim_fifty_moves()→ bool[source]
Checks if the player to move can claim a draw by the fifty-move rule.

In addition to is_fifty_moves(), the fifty-move rule can also be claimed if there is a legal move that achieves this condition.

can_claim_threefold_repetition()→ bool[source]
Checks if the player to move can claim a draw by threefold repetition.

Draw by threefold repetition can be claimed if the position on the board occurred for the third time or if such a repetition is reached with one of the possible legal moves.

Note that checking this can be slow: In the worst case scenario, every legal move has to be tested and the entire game has to be replayed because there is no incremental transposition table.

is_repetition(count: int = 3)→ bool[source]
Checks if the current position has repeated 3 (or a given number of) times.

Unlike can_claim_threefold_repetition(), this does not consider a repetition that can be played on the next move.

Note that checking this can be slow: In the worst case, the entire game has to be replayed because there is no incremental transposition table.

push(move: Move)→ None[source]
Updates the position with the given move and puts it onto the move stack.

>>> import chess
>>>
>>> board = chess.Board()
>>>
>>> Nf3 = chess.Move.from_uci("g1f3")
>>> board.push(Nf3)  # Make the move
>>> board.pop()  # Unmake the last move
Move.from_uci('g1f3')
Null moves just increment the move counters, switch turns and forfeit en passant capturing.

Warning

Moves are not checked for legality. It is the caller’s responsibility to ensure that the move is at least pseudo-legal or a null move.

pop()→ Move[source]
Restores the previous position and returns the last move from the stack.

Raises
:
IndexError if the move stack is empty.

peek()→ Move[source]
Gets the last move from the move stack.

Raises
:
IndexError if the move stack is empty.

find_move(from_square: chess.Square, to_square: chess.Square, promotion: chess.PieceType | None = None)→ Move[source]
Finds a matching legal move for an origin square, a target square, and an optional promotion piece type.

For pawn moves to the backrank, the promotion piece type defaults to chess.QUEEN, unless otherwise specified.

Castling moves are normalized to king moves by two steps, except in Chess960.

Raises
:
IllegalMoveError if no matching legal move is found.

has_pseudo_legal_en_passant()→ bool[source]
Checks if there is a pseudo-legal en passant capture.

has_legal_en_passant()→ bool[source]
Checks if there is a legal en passant capture.

fen(*, shredder: bool = False, en_passant: Literal['legal', 'fen', 'xfen'] = 'legal', promoted: bool | None = None)→ str[source]
Gets a FEN representation of the position.

A FEN string (e.g., rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1) consists of the board part board_fen(), the turn, the castling part (castling_rights), the en passant square (ep_square), the halfmove_clock and the fullmove_number.

Parameters
:
shredder – Use castling_shredder_fen() and encode castling rights by the file of the rook (like HAha) instead of the default castling_xfen() (like KQkq).

en_passant – By default, only fully legal en passant squares are included (has_legal_en_passant()). Pass fen to strictly follow the FEN specification (always include the en passant square after a two-step pawn move) or xfen to follow the X-FEN specification (has_pseudo_legal_en_passant()).

promoted – Mark promoted pieces like Q~. By default, this is only enabled in chess variants where this is relevant.

set_fen(fen: str)→ None[source]
Parses a FEN and sets the position from it.

Raises
:
ValueError if syntactically invalid. Use is_valid() to detect invalid positions.

set_castling_fen(castling_fen: str)→ None[source]
Sets castling rights from a string in FEN notation like Qqk.

Also clears the move stack.

Raises
:
ValueError if the castling FEN is syntactically invalid.

chess960_pos(*, ignore_turn: bool = False, ignore_castling: bool = False, ignore_counters: bool = True)→ int | None[source]
Gets the Chess960 starting position index between 0 and 956, or None if the current position is not a Chess960 starting position.

By default, white to move (ignore_turn) and full castling rights (ignore_castling) are required, but move counters (ignore_counters) are ignored.

epd(*, shredder: bool = False, en_passant: Literal['legal', 'fen', 'xfen'] = 'legal', promoted: bool | None = None, **operations: None | str | int | float | Move | Iterable[Move])→ str[source]
Gets an EPD representation of the current position.

See fen() for FEN formatting options (shredder, ep_square and promoted).

EPD operations can be given as keyword arguments. Supported operands are strings, integers, finite floats, legal moves and None. Additionally, the operation pv accepts a legal variation as a list of moves. The operations am and bm accept a list of legal moves in the current position.

The name of the field cannot be a lone dash and cannot contain spaces, newlines, carriage returns or tabs.

hmvc and fmvn are not included by default. You can use:

>>> import chess
>>>
>>> board = chess.Board()
>>> board.epd(hmvc=board.halfmove_clock, fmvn=board.fullmove_number)
'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - hmvc 0; fmvn 1;'
set_epd(epd: str)→ Dict[str, None | str | int | float | Move | List[Move]][source]
Parses the given EPD string and uses it to set the position.

If present, hmvc and fmvn are used to set the half-move clock and the full-move number. Otherwise, 0 and 1 are used.

Returns a dictionary of parsed operations. Values can be strings, integers, floats, move objects, or lists of moves.

Raises
:
ValueError if the EPD string is invalid.

san(move: Move)→ str[source]
Gets the standard algebraic notation of the given move in the context of the current position.

lan(move: Move)→ str[source]
Gets the long algebraic notation of the given move in the context of the current position.

variation_san(variation: Iterable[Move])→ str[source]
Given a sequence of moves, returns a string representing the sequence in standard algebraic notation (e.g., 1. e4 e5 2. Nf3 Nc6 or 37...Bg6 38. fxg6).

The board will not be modified as a result of calling this.

Raises
:
IllegalMoveError if any moves in the sequence are illegal.

parse_san(san: str)→ Move[source]
Uses the current position as the context to parse a move in standard algebraic notation and returns the corresponding move object.

Ambiguous moves are rejected. Overspecified moves (including long algebraic notation) are accepted. Some common syntactical deviations are also accepted.

The returned move is guaranteed to be either legal or a null move.

Raises
:
ValueError (specifically an exception specified below) if the SAN is invalid, illegal or ambiguous.

InvalidMoveError if the SAN is syntactically invalid.

IllegalMoveError if the SAN is illegal.

AmbiguousMoveError if the SAN is ambiguous.

push_san(san: str)→ Move[source]
Parses a move in standard algebraic notation, makes the move and puts it onto the move stack.

Returns the move.

Raises
:
ValueError (specifically an exception specified below) if neither legal nor a null move.

InvalidMoveError if the SAN is syntactically invalid.

IllegalMoveError if the SAN is illegal.

AmbiguousMoveError if the SAN is ambiguous.

uci(move: Move, *, chess960: bool | None = None)→ str[source]
Gets the UCI notation of the move.

chess960 defaults to the mode of the board. Pass True to force Chess960 mode.

parse_uci(uci: str)→ Move[source]
Parses the given move in UCI notation.

Supports both Chess960 and standard UCI notation.

The returned move is guaranteed to be either legal or a null move.

Raises
:
ValueError (specifically an exception specified below) if the move is invalid or illegal in the current position (but not a null move).

InvalidMoveError if the UCI is syntactically invalid.

IllegalMoveError if the UCI is illegal.

push_uci(uci: str)→ Move[source]
Parses a move in UCI notation and puts it on the move stack.

Returns the move.

Raises
:
ValueError (specifically an exception specified below) if the move is invalid or illegal in the current position (but not a null move).

InvalidMoveError if the UCI is syntactically invalid.

IllegalMoveError if the UCI is illegal.

push_xboard(san: str)→ Move
Parses a move in standard algebraic notation, makes the move and puts it onto the move stack.

Returns the move.

Raises
:
ValueError (specifically an exception specified below) if neither legal nor a null move.

InvalidMoveError if the SAN is syntactically invalid.

IllegalMoveError if the SAN is illegal.

AmbiguousMoveError if the SAN is ambiguous.

is_en_passant(move: Move)→ bool[source]
Checks if the given pseudo-legal move is an en passant capture.

is_capture(move: Move)→ bool[source]
Checks if the given pseudo-legal move is a capture.

is_zeroing(move: Move)→ bool[source]
Checks if the given pseudo-legal move is a capture or pawn move.

is_irreversible(move: Move)→ bool[source]
Checks if the given pseudo-legal move is irreversible.

In standard chess, pawn moves, captures, moves that destroy castling rights and moves that cede en passant are irreversible.

This method has false-negatives with forced lines. For example, a check that will force the king to lose castling rights is not considered irreversible. Only the actual king move is.

is_castling(move: Move)→ bool[source]
Checks if the given pseudo-legal move is a castling move.

is_kingside_castling(move: Move)→ bool[source]
Checks if the given pseudo-legal move is a kingside castling move.

is_queenside_castling(move: Move)→ bool[source]
Checks if the given pseudo-legal move is a queenside castling move.

clean_castling_rights()→ chess.Bitboard[source]
Returns valid castling rights filtered from castling_rights.

has_castling_rights(color: chess.Color)→ bool[source]
Checks if the given side has castling rights.

has_kingside_castling_rights(color: chess.Color)→ bool[source]
Checks if the given side has kingside (that is h-side in Chess960) castling rights.

has_queenside_castling_rights(color: chess.Color)→ bool[source]
Checks if the given side has queenside (that is a-side in Chess960) castling rights.

has_chess960_castling_rights()→ bool[source]
Checks if there are castling rights that are only possible in Chess960.

status()→ Status[source]
Gets a bitmask of possible problems with the position.

STATUS_VALID if all basic validity requirements are met. This does not imply that the position is actually reachable with a series of legal moves from the starting position.

Otherwise, bitwise combinations of: STATUS_NO_WHITE_KING, STATUS_NO_BLACK_KING, STATUS_TOO_MANY_KINGS, STATUS_TOO_MANY_WHITE_PAWNS, STATUS_TOO_MANY_BLACK_PAWNS, STATUS_PAWNS_ON_BACKRANK, STATUS_TOO_MANY_WHITE_PIECES, STATUS_TOO_MANY_BLACK_PIECES, STATUS_BAD_CASTLING_RIGHTS, STATUS_INVALID_EP_SQUARE, STATUS_OPPOSITE_CHECK, STATUS_EMPTY, STATUS_RACE_CHECK, STATUS_RACE_OVER, STATUS_RACE_MATERIAL, STATUS_TOO_MANY_CHECKERS, STATUS_IMPOSSIBLE_CHECK.

is_valid()→ bool[source]
Checks some basic validity requirements.

See status() for details.

transform(f: Callable[[Bitboard], Bitboard])→ Self[source]
Returns a transformed copy of the board (without move stack) by applying a bitboard transformation function.

Available transformations include chess.flip_vertical(), chess.flip_horizontal(), chess.flip_diagonal(), chess.flip_anti_diagonal(), chess.shift_down(), chess.shift_up(), chess.shift_left(), and chess.shift_right().

Alternatively, apply_transform() can be used to apply the transformation on the board.

mirror()→ Self[source]
Returns a mirrored copy of the board.

The board is mirrored vertically and piece colors are swapped, so that the position is equivalent modulo color. Also swap the “en passant” square, castling rights and turn.

Alternatively, apply_mirror() can be used to mirror the board.

copy(*, stack: bool | int = True)→ Self[source]
Creates a copy of the board.

Defaults to copying the entire move stack. Alternatively, stack can be False, or an integer to copy a limited number of moves.

classmethodempty(*, chess960: bool = False)→ BoardT[source]
Creates a new empty board. Also see clear().

classmethodfrom_epd(epd: str, *, chess960: bool = False)→ Tuple[BoardT, Dict[str, None | str | int | float | Move | List[Move]]][source]
Creates a new board from an EPD string. See set_epd().

Returns the board and the dictionary of parsed operations as a tuple.

classmethodfrom_chess960_pos(scharnagl: int)→ BoardT[source]
Creates a new board, initialized with a Chess960 starting position.

>>> import chess
>>> import random
>>>
>>> board = chess.Board.from_chess960_pos(random.randint(0, 959))
classchess.BaseBoard(board_fen: str | None = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR')[source]
A board representing the position of chess pieces. See Board for a full board with move generation.

The board is initialized with the standard chess starting position, unless otherwise specified in the optional board_fen argument. If board_fen is None, an empty board is created.

reset_board()→ None[source]
Resets pieces to the starting position.

Board also resets the move stack, but not turn, castling rights and move counters. Use chess.Board.reset() to fully restore the starting position.

clear_board()→ None[source]
Clears the board.

Board also clears the move stack.

pieces(piece_type: chess.PieceType, color: chess.Color)→ SquareSet[source]
Gets pieces of the given type and color.

Returns a set of squares.

piece_at(square: chess.Square)→ Piece | None[source]
Gets the piece at the given square.

piece_type_at(square: chess.Square)→ chess.PieceType | None[source]
Gets the piece type at the given square.

color_at(square: chess.Square)→ chess.Color | None[source]
Gets the color of the piece at the given square.

king(color: chess.Color)→ chess.Square | None[source]
Finds the king square of the given side. Returns None if there is no king of that color.

In variants with king promotions, only non-promoted kings are considered.

attacks(square: chess.Square)→ SquareSet[source]
Gets the set of attacked squares from the given square.

There will be no attacks if the square is empty. Pinned pieces are still attacking other squares.

Returns a set of squares.

is_attacked_by(color: chess.Color, square: chess.Square, occupied: chess.IntoSquareSet | None = None)→ bool[source]
Checks if the given side attacks the given square.

Pinned pieces still count as attackers. Pawns that can be captured en passant are not considered attacked.

occupied determines which squares are considered to block attacks. For example, board.occupied ^ board.pieces_mask(chess.KING, board.turn) can be used to consider X-ray attacks through the king. Defaults to board.occupied (all pieces including the king, no X-ray attacks).

attackers(color: chess.Color, square: chess.Square, occupied: chess.IntoSquareSet | None = None)→ SquareSet[source]
Gets the set of attackers of the given color for the given square.

Pinned pieces still count as attackers.

occupied determines which squares are considered to block attacks. For example, board.occupied ^ board.pieces_mask(chess.KING, board.turn) can be used to consider X-ray attacks through the king. Defaults to board.occupied (all pieces including the king, no X-ray attacks).

Returns a set of squares.

pin(color: chess.Color, square: chess.Square)→ SquareSet[source]
Detects an absolute pin (and its direction) of the given square to the king of the given color.

>>> import chess
>>>
>>> board = chess.Board("rnb1k2r/ppp2ppp/5n2/3q4/1b1P4/2N5/PP3PPP/R1BQKBNR w KQkq - 3 7")
>>> board.is_pinned(chess.WHITE, chess.C3)
True
>>> direction = board.pin(chess.WHITE, chess.C3)
>>> direction
SquareSet(0x0000_0001_0204_0810)
>>> print(direction)
. . . . . . . .
. . . . . . . .
. . . . . . . .
1 . . . . . . .
. 1 . . . . . .
. . 1 . . . . .
. . . 1 . . . .
. . . . 1 . . .
Returns a set of squares that mask the rank, file or diagonal of the pin. If there is no pin, then a mask of the entire board is returned.

is_pinned(color: chess.Color, square: chess.Square)→ bool[source]
Detects if the given square is pinned to the king of the given color.

remove_piece_at(square: chess.Square)→ Piece | None[source]
Removes the piece from the given square. Returns the Piece or None if the square was already empty.

Board also clears the move stack.

set_piece_at(square: chess.Square, piece: Piece | None, promoted: bool = False)→ None[source]
Sets a piece at the given square.

An existing piece is replaced. Setting piece to None is equivalent to remove_piece_at().

Board also clears the move stack.

board_fen(*, promoted: bool | None = False)→ str[source]
Gets the board FEN (e.g., rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR).

set_board_fen(fen: str)→ None[source]
Parses fen and sets up the board, where fen is the board part of a FEN.

Board also clears the move stack.

Raises
:
ValueError if syntactically invalid.

piece_map(*, mask: chess.Bitboard = 18446744073709551615)→ Dict[chess.Square, Piece][source]
Gets a dictionary of pieces by square index.

set_piece_map(pieces: Mapping[chess.Square, Piece])→ None[source]
Sets up the board from a dictionary of pieces by square index.

Board also clears the move stack.

set_chess960_pos(scharnagl: int)→ None[source]
Sets up a Chess960 starting position given its index between 0 and 959. Also see from_chess960_pos().

chess960_pos()→ int | None[source]
Gets the Chess960 starting position index between 0 and 959, or None.

unicode(*, invert_color: bool = False, borders: bool = False, empty_square: str = '⭘', orientation: chess.Color = True)→ str[source]
Returns a string representation of the board with Unicode pieces. Useful for pretty-printing to a terminal.

Parameters
:
invert_color – Invert color of the Unicode pieces.

borders – Show borders and a coordinate margin.

transform(f: Callable[[Bitboard], Bitboard])→ Self[source]
Returns a transformed copy of the board (without move stack) by applying a bitboard transformation function.

Available transformations include chess.flip_vertical(), chess.flip_horizontal(), chess.flip_diagonal(), chess.flip_anti_diagonal(), chess.shift_down(), chess.shift_up(), chess.shift_left(), and chess.shift_right().

Alternatively, apply_transform() can be used to apply the transformation on the board.

mirror()→ Self[source]
Returns a mirrored copy of the board (without move stack).

The board is mirrored vertically and piece colors are swapped, so that the position is equivalent modulo color.

Alternatively, apply_mirror() can be used to mirror the board.

copy()→ Self[source]
Creates a copy of the board.

classmethodempty()→ BaseBoardT[source]
Creates a new empty board. Also see clear_board().

classmethodfrom_chess960_pos(scharnagl: int)→ BaseBoardT[source]
Creates a new board, initialized with a Chess960 starting position.

>>> import chess
>>> import random
>>>
>>> board = chess.Board.from_chess960_pos(random.randint(0, 959))


Outcome
classchess.Outcome(termination: Termination, winner: chess.Color | None)[source]
Information about the outcome of an ended game, usually obtained from chess.Board.outcome().

termination: Termination
The reason for the game to have ended.

winner: chess.Color | None
The winning color or None if drawn.

result()→ str[source]
Returns 1-0, 0-1 or 1/2-1/2.

classchess.Termination(value)[source]
Enum with reasons for a game to be over.

CHECKMATE= 1
See chess.Board.is_checkmate().

STALEMATE= 2
See chess.Board.is_stalemate().

INSUFFICIENT_MATERIAL= 3
See chess.Board.is_insufficient_material().

SEVENTYFIVE_MOVES= 4
See chess.Board.is_seventyfive_moves().

FIVEFOLD_REPETITION= 5
See chess.Board.is_fivefold_repetition().

FIFTY_MOVES= 6
See chess.Board.can_claim_fifty_moves().

THREEFOLD_REPETITION= 7
See chess.Board.can_claim_threefold_repetition().

VARIANT_WIN= 8
See chess.Board.is_variant_win().

VARIANT_LOSS= 9
See chess.Board.is_variant_loss().

VARIANT_DRAW= 10
See chess.Board.is_variant_draw().

Square sets
classchess.SquareSet(squares: chess.IntoSquareSet = 0)[source]
A set of squares.

>>> import chess
>>>
>>> squares = chess.SquareSet([chess.A8, chess.A1])
>>> squares
SquareSet(0x0100_0000_0000_0001)
>>> squares = chess.SquareSet(chess.BB_A8 | chess.BB_RANK_1)
>>> squares
SquareSet(0x0100_0000_0000_00ff)
>>> print(squares)
1 . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
1 1 1 1 1 1 1 1
>>> len(squares)
9
>>> bool(squares)
True
>>> chess.B1 in squares
True
>>> for square in squares:
...     # 0 -- chess.A1
...     # 1 -- chess.B1
...     # 2 -- chess.C1
...     # 3 -- chess.D1
...     # 4 -- chess.E1
...     # 5 -- chess.F1
...     # 6 -- chess.G1
...     # 7 -- chess.H1
...     # 56 -- chess.A8
...     print(square)
...
0
1
2
3
4
5
6
7
56
>>> list(squares)
[0, 1, 2, 3, 4, 5, 6, 7, 56]
Square sets are internally represented by 64-bit integer masks of the included squares. Bitwise operations can be used to compute unions, intersections and shifts.

>>> int(squares)
72057594037928191
Also supports common set operations like issubset(), issuperset(), union(), intersection(), difference(), symmetric_difference() and copy() as well as update(), intersection_update(), difference_update(), symmetric_difference_update() and clear().

add(square: chess.Square)→ None[source]
Adds a square to the set.

discard(square: chess.Square)→ None[source]
Discards a square from the set.

isdisjoint(other: chess.IntoSquareSet)→ bool[source]
Tests if the square sets are disjoint.

issubset(other: chess.IntoSquareSet)→ bool[source]
Tests if this square set is a subset of another.

issuperset(other: chess.IntoSquareSet)→ bool[source]
Tests if this square set is a superset of another.

remove(square: chess.Square)→ None[source]
Removes a square from the set.

Raises
:
KeyError if the given square was not in the set.

pop()→ chess.Square[source]
Removes and returns a square from the set.

Raises
:
KeyError if the set is empty.

clear()→ None[source]
Removes all elements from this set.

carry_rippler()→ Iterator[chess.Bitboard][source]
Iterator over the subsets of this set.

mirror()→ SquareSet[source]
Returns a vertically mirrored copy of this square set.

tolist()→ List[bool][source]
Converts the set to a list of 64 bools.

classmethodray(a: chess.Square, b: chess.Square)→ SquareSet[source]
All squares on the rank, file or diagonal with the two squares, if they are aligned.

>>> import chess
>>>
>>> print(chess.SquareSet.ray(chess.E2, chess.B5))
. . . . . . . .
. . . . . . . .
1 . . . . . . .
. 1 . . . . . .
. . 1 . . . . .
. . . 1 . . . .
. . . . 1 . . .
. . . . . 1 . .
classmethodbetween(a: chess.Square, b: chess.Square)→ SquareSet[source]
All squares on the rank, file or diagonal between the two squares (bounds not included), if they are aligned.

>>> import chess
>>>
>>> print(chess.SquareSet.between(chess.E2, chess.B5))
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . 1 . . . . .
. . . 1 . . . .
. . . . . . . .
. . . . . . . .
classmethodfrom_square(square: chess.Square)→ SquareSet[source]
Creates a SquareSet from a single square.

>>> import chess
>>>
>>> chess.SquareSet.from_square(chess.A1) == chess.BB_A1
True
Common integer masks are:

chess.BB_EMPTY: chess.Bitboard= 0
chess.BB_ALL: chess.Bitboard= 0xFFFF_FFFF_FFFF_FFFF
Single squares:

chess.BB_SQUARES= [chess.BB_A1, chess.BB_B1, ..., chess.BB_G8, chess.BB_H8]
Ranks and files:

chess.BB_RANKS= [chess.BB_RANK_1, ..., chess.BB_RANK_8]
chess.BB_FILES= [chess.BB_FILE_A, ..., chess.BB_FILE_H]
Other masks:

chess.BB_LIGHT_SQUARES: chess.Bitboard= 0x55AA_55AA_55AA_55AA
chess.BB_DARK_SQUARES: chess.Bitboard= 0xAA55_AA55_AA55_AA55
chess.BB_BACKRANKS= chess.BB_RANK_1 | chess.BB_RANK_8
chess.BB_CORNERS= chess.BB_A1 | chess.BB_H1 | chess.BB_A8 | chess.BB_H8
chess.BB_CENTER= chess.BB_D4 | chess.BB_E4 | chess.BB_D5 | chess.BB_E5