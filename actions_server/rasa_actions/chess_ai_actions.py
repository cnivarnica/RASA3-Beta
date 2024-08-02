from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from rasa_sdk.events import SlotSet, FollowupAction
import chess
from .chess_ai import get_best_move
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

board_cache = {}

def get_or_create_board(tracker: Tracker) -> chess.Board:
    sender_id = tracker.sender_id
    if sender_id in board_cache:
        board = board_cache[sender_id]
        logger.debug(f"Retrieved existing board for {sender_id}")
    else:
        board = chess.Board()
        board_cache[sender_id] = board
        logger.debug(f"Created new board for {sender_id}")
    logger.debug(f"Current board state:\n{board}")
    return board

class ValidateChessMoveForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_chess_move_form"

    def validate_chess_move(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        logger.debug(f"Validating chess move: {slot_value}")
        if not slot_value:
            logger.warning("Received None or empty string as slot_value for chess_move")
            dispatcher.utter_message(text="No move was provided. Please enter your move in UCI format (e.g., e2e4 or e7e8q for promotion).")
            return {"chess_move": None}
        
        board = get_or_create_board(tracker)
        try:
            move = chess.Move.from_uci(slot_value)
            if move.promotion is None and board.piece_at(move.from_square) and board.piece_at(move.from_square).piece_type == chess.PAWN:
                if (board.turn == chess.WHITE and chess.square_rank(move.to_square) == 7) or \
                   (board.turn == chess.BLACK and chess.square_rank(move.to_square) == 0):
                    move.promotion = chess.QUEEN
                    logger.info(f"Automatic pawn promotion to queen: {move}")
            
            if move in board.legal_moves:
                logger.info(f"Valid move: {move}")
                return {"chess_move": move.uci()}
            else:
                logger.warning(f"Illegal move: {move}")
                dispatcher.utter_message(text=f"The move '{move}' is not a legal move. Please try again.")
                return {"chess_move": None}
        except ValueError as e:
            logger.error(f"Error parsing move: {e}")
            dispatcher.utter_message(text=f"'{slot_value}' is not a valid move format. Please use UCI format (e.g., e2e4 or e7e8q for promotion).")
            return {"chess_move": None}

class ActionChessMove(Action):
    def name(self) -> Text:
        return "action_chess_move"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain_dict: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        user_move = tracker.get_slot("chess_move")
        logger.debug(f"Executing chess move: {user_move}")
        if not user_move:
            logger.warning("No valid move provided")
            dispatcher.utter_message(text="No valid move was provided. Please try again.")
            return [FollowupAction("action_ask_for_move")]

        board = get_or_create_board(tracker)
        logger.debug(f"Board state before move:\n{board}")
        logger.debug(f"Legal moves before: {list(board.legal_moves)}")
        
        try:
            move = chess.Move.from_uci(user_move)
            if move.promotion is None and board.piece_at(move.from_square).piece_type == chess.PAWN:
                if (board.turn == chess.WHITE and chess.square_rank(move.to_square) == 8) or \
                   (board.turn == chess.BLACK and chess.square_rank(move.to_square) == 0):
                    move.promotion = chess.QUEEN
                    logger.info(f"Automatic pawn promotion to queen: {move}")

            if move in board.legal_moves:
                board.push(move)
                logger.info(f"Move executed: {move}")
                logger.debug(f"Board state after move:\n{board}")
                dispatcher.utter_message(text=f"Your move: {move}\n")

                board_cache[tracker.sender_id] = board

                return [
                    SlotSet("chess_board", board.fen()),
                    SlotSet("chess_move", None),
                    FollowupAction("action_ai_move")
                ]
            else:
                logger.warning(f"Illegal move attempted: {move}")
                dispatcher.utter_message(text=f"The move '{move}' is not a legal move. Please try again.")
                return [FollowupAction("action_ask_for_move")]
        except ValueError as e:
            logger.error(f"Error executing move: {e}")
            dispatcher.utter_message(text=f"'{user_move}' is not a valid move format. Please use UCI format (e.g., e2e4).")
            return [FollowupAction("action_ask_for_move")]

class ActionAIMove(Action):
    def name(self) -> Text:
        return "action_ai_move"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain_dict: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        board = get_or_create_board(tracker)
        logger.debug(f"Board state before AI move:\n{board}")
        logger.debug(f"Legal moves before AI move: {list(board.legal_moves)}")
        
        ai_move = get_best_move(board, time_limit=5, max_depth=3)
        logger.info(f"AI selected move: {ai_move}")
        
        if ai_move.promotion is None and board.piece_at(ai_move.from_square).piece_type == chess.PAWN:
            if (board.turn == chess.WHITE and chess.square_rank(ai_move.to_square) == 7) or \
               (board.turn == chess.BLACK and chess.square_rank(ai_move.to_square) == 0):
                ai_move.promotion = chess.QUEEN
                logger.info(f"AI automatic pawn promotion to queen: {ai_move}")
        
        if ai_move in board.legal_moves:
            board.push(ai_move)
            logger.debug(f"Board state after AI move:\n{board}")
            dispatcher.utter_message(text=f"AI move: {ai_move}\nCurrent board state:\n{board.unicode()}")

            board_cache[tracker.sender_id] = board

            return [
                SlotSet("chess_board", board.fen()),
                FollowupAction("action_check_game_over")
            ]
        else:
            logger.error(f"AI attempted illegal move: {ai_move}")
            dispatcher.utter_message(text="The AI made an illegal move. Starting a new game.")
            return [FollowupAction("action_new_chess_game")]

class ActionNewChessGame(Action):
    def name(self) -> Text:
        return "action_new_chess_game"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain_dict: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        logger.info("Starting new chess game")
        board = chess.Board()
        board_cache[tracker.sender_id] = board
        dispatcher.utter_message(text=f"New game started. Current board state:\n{board.unicode()}")
        return [
            SlotSet("chess_board", board.fen()),
            SlotSet("chess_move", None),
            SlotSet("game_over", False),
            FollowupAction("action_ask_for_move")
        ]

class ActionAskForMove(Action):
    def name(self) -> Text:
        return "action_ask_for_move"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain_dict: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        logger.debug("Asking for chess move")
        board = get_or_create_board(tracker)
        # dispatcher.utter_message(text=f"Current board state:\n{board.unicode()}\nPlease enter your move in UCI format (e.g., e2e4).")
        return [SlotSet("chess_move", None)]

class ActionCheckGameOver(Action):
    def name(self) -> Text:
        return "action_check_game_over"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain_dict: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        logger.debug("Checking if game is over")
        board = get_or_create_board(tracker)

        if board.is_game_over():
            logger.info("Game over")
            dispatcher.utter_message(text=f"Game over. Result: {board.result()}")
            board_cache.pop(tracker.sender_id, None)
            return [
                SlotSet("chess_board", None),
                SlotSet("chess_move", None),
                SlotSet("game_over", True),
                FollowupAction("action_handle_game_state")
            ]
        logger.debug("Game continues")
        return [
            SlotSet("game_over", False),
            FollowupAction("action_handle_game_state")
        ]

class ActionHandleGameState(Action):
    def name(self) -> Text:
        return "action_handle_game_state"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain_dict: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        game_over = tracker.get_slot("game_over")
        logger.debug(f"Handling game state. Game over: {game_over}")

        if game_over:
            return [FollowupAction("action_end_game")]
        else:
            return [FollowupAction("action_ask_for_move")]

class ActionEndGame(Action):
    def name(self) -> Text:
        return "action_end_game"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain_dict: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        logger.info("Ending the game")
        dispatcher.utter_message(text="\nThe game has ended. Would you like to start a new game?")
        return []