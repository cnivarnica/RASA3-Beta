from .chess_tables import pawntable, knightstable, bishopstable, rookstable, queenstable, kingstable
import chess
from collections import defaultdict
import time
import random

transposition_table = {}

def evaluate_board(board):
    if board.is_checkmate():
        return -9999 if board.turn else 9999
    if board.is_stalemate() or board.is_insufficient_material():
        return 0

    wp = len(board.pieces(chess.PAWN, chess.WHITE))
    bp = len(board.pieces(chess.PAWN, chess.BLACK))
    wn = len(board.pieces(chess.KNIGHT, chess.WHITE))
    bn = len(board.pieces(chess.KNIGHT, chess.BLACK))
    wb = len(board.pieces(chess.BISHOP, chess.WHITE))
    bb = len(board.pieces(chess.BISHOP, chess.BLACK))
    wr = len(board.pieces(chess.ROOK, chess.WHITE))
    br = len(board.pieces(chess.ROOK, chess.BLACK))
    wq = len(board.pieces(chess.QUEEN, chess.WHITE))
    bq = len(board.pieces(chess.QUEEN, chess.BLACK))

    material = 100 * (wp - bp) + 320 * (wn - bn) + 330 * (wb - bb) + 500 * (wr - br) + 900 * (wq - bq)

    pawnsq = sum([pawntable[i] for i in board.pieces(chess.PAWN, chess.WHITE)])
    pawnsq -= sum([pawntable[chess.square_mirror(i)] for i in board.pieces(chess.PAWN, chess.BLACK)])
    knightsq = sum([knightstable[i] for i in board.pieces(chess.KNIGHT, chess.WHITE)])
    knightsq -= sum([knightstable[chess.square_mirror(i)] for i in board.pieces(chess.KNIGHT, chess.BLACK)])
    bishopsq = sum([bishopstable[i] for i in board.pieces(chess.BISHOP, chess.WHITE)])
    bishopsq -= sum([bishopstable[chess.square_mirror(i)] for i in board.pieces(chess.BISHOP, chess.BLACK)])
    rooksq = sum([rookstable[i] for i in board.pieces(chess.ROOK, chess.WHITE)])
    rooksq -= sum([rookstable[chess.square_mirror(i)] for i in board.pieces(chess.ROOK, chess.BLACK)])
    queensq = sum([queenstable[i] for i in board.pieces(chess.QUEEN, chess.WHITE)])
    queensq -= sum([queenstable[chess.square_mirror(i)] for i in board.pieces(chess.QUEEN, chess.BLACK)])
    kingsq = sum([kingstable[i] for i in board.pieces(chess.KING, chess.WHITE)])
    kingsq -= sum([kingstable[chess.square_mirror(i)] for i in board.pieces(chess.KING, chess.BLACK)])

    mobility = len(list(board.legal_moves))
    if not board.turn:
        mobility = -mobility

    development = 0
    if board.fullmove_number < 10:
        development += sum(1 for sq in [chess.E2, chess.D2, chess.E7, chess.D7] if board.piece_at(sq) is None)
        development += sum(1 for sq in [chess.B1, chess.G1, chess.C1, chess.F1, chess.B8, chess.G8, chess.C8, chess.F8] if board.piece_at(sq) is None)

    king_safety = 0
    for color in [chess.WHITE, chess.BLACK]:
        king_square = board.king(color)
        if king_square:
            if color == chess.WHITE:
                king_safety += sum(1 for sq in board.attacks(king_square) if board.piece_at(sq) and board.piece_at(sq).color == chess.WHITE)
            else:
                king_safety -= sum(1 for sq in board.attacks(king_square) if board.piece_at(sq) and board.piece_at(sq).color == chess.BLACK)

    eval = material + pawnsq + knightsq + bishopsq + rooksq + queensq + kingsq + mobility * 10 + development * 10 + king_safety * 50
    
    if is_endgame(board):
        eval += evaluate_endgame(board)

    return eval if board.turn else -eval

def quiescence(board, alpha, beta):
    stand_pat = evaluate_board(board)
    if stand_pat >= beta:
        return beta
    alpha = max(alpha, stand_pat)

    for move in sorted(board.legal_moves, key=lambda move: board.is_capture(move), reverse=True):
        if board.is_capture(move):
            board.push(move)
            score = -quiescence(board, -beta, -alpha)
            board.pop()
            if score >= beta:
                return beta
            alpha = max(alpha, score)
    return alpha

def order_moves(board, moves):
    def move_value(move):
        if board.is_capture(move):
            from_piece = board.piece_at(move.from_square)
            to_piece = board.piece_at(move.to_square)
            if from_piece and to_piece:
                return 10 + (to_piece.piece_type - from_piece.piece_type)
            return 10
        elif move.promotion:
            return 9
        elif board.is_check():
            return 8
        else:
            return 0
    return sorted(moves, key=move_value, reverse=True)

def minimax(board, depth, alpha, beta, maximizing_player):
    hash_key = board.board_fen() + str(depth)
    if hash_key in transposition_table:
        tt_entry = transposition_table[hash_key]
        if tt_entry['depth'] >= depth:
            return tt_entry['eval']

    if depth == 0 or board.is_game_over():
        return quiescence(board, alpha, beta)

    if maximizing_player:
        max_eval = -float('inf')
        for move in order_moves(board, board.legal_moves):
            board.push(move)
            eval = minimax(board, depth - 1, alpha, beta, False)
            board.pop()
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        transposition_table[hash_key] = {'eval': max_eval, 'depth': depth}
        return max_eval
    else:
        min_eval = float('inf')
        for move in order_moves(board, board.legal_moves):
            board.push(move)
            eval = minimax(board, depth - 1, alpha, beta, True)
            board.pop()
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        transposition_table[hash_key] = {'eval': min_eval, 'depth': depth}
        return min_eval

def evaluate_move(board, move):
    board.push(move)
    eval = evaluate_board(board)
    board.pop()
    return eval

def iterative_deepening(board, time_limit):
    depth = 1
    best_move = None
    start_time = time.time()

    while True:
        current_move = get_best_move(board, depth)
        elapsed_time = time.time() - start_time
        if elapsed_time >= time_limit:
            break
        best_move = current_move
        depth += 1

    return best_move

def get_best_move(board, time_limit=5, max_depth=100):
    best_move = None
    start_time = time.time()
    try:
        for depth in range(1, max_depth + 1):
            if time.time() - start_time > time_limit:
                break
            move = find_move(board, depth)
            if move:
                best_move = move
    except Exception as e:
        logger.error(f"Error in get_best_move: {e}")
        return random.choice(list(board.legal_moves)) if board.legal_moves else None
    return best_move

def find_move(board, depth):
    best_move = None
    alpha = float('-inf')
    beta = float('inf')
    for move in order_moves(board, board.legal_moves):
        board.push(move)
        score = -minimax(board, depth-1, -beta, -alpha, not board.turn)
        board.pop()
        if score > alpha:
            alpha = score
            best_move = move
    return best_move

def is_endgame(board):
    return len(board.pieces(chess.QUEEN, chess.WHITE)) + len(board.pieces(chess.QUEEN, chess.BLACK)) == 0 or \
           (len(board.pieces(chess.ROOK, chess.WHITE)) + len(board.pieces(chess.ROOK, chess.BLACK)) <= 2 and \
            len(board.pieces(chess.BISHOP, chess.WHITE)) + len(board.pieces(chess.BISHOP, chess.BLACK)) + \
            len(board.pieces(chess.KNIGHT, chess.WHITE)) + len(board.pieces(chess.KNIGHT, chess.BLACK)) <= 1)

def evaluate_endgame(board):
    king_centrality = sum(4 - min(3, abs(3.5 - chess.square_file(sq))) - min(3, abs(3.5 - chess.square_rank(sq))) 
                          for sq in board.pieces(chess.KING, chess.WHITE))
    king_centrality -= sum(4 - min(3, abs(3.5 - chess.square_file(sq))) - min(3, abs(3.5 - chess.square_rank(sq))) 
                           for sq in board.pieces(chess.KING, chess.BLACK))
    
    return king_centrality * 10