import asyncio
import json
import logging
import websockets
from websockets.server import WebSocketServerProtocol

from tboggle.game import Game
from tboggle.dice import DiceSet

logger = logging.getLogger(__name__)


class BoggleBackend:
    def __init__(self, host="localhost", port=8765):
        self.host = host
        self.port = port

    async def handle_message(self, websocket: WebSocketServerProtocol, path: str):
        """Handle incoming WebSocket messages."""
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    endpoint = data.get("endpoint")
                    params = data.get("params", {})
                    
                    if endpoint == "restore_game":
                        response = await self.restore_game(params)
                    elif endpoint == "fill_board":
                        response = await self.fill_board(params)
                    else:
                        response = {
                            "error": f"Unknown endpoint: {endpoint}",
                            "status": "error"
                        }
                    
                    await websocket.send(json.dumps(response))
                    
                except json.JSONDecodeError:
                    error_response = {
                        "error": "Invalid JSON format",
                        "status": "error"
                    }
                    await websocket.send(json.dumps(error_response))
                except Exception as e:
                    logger.exception("Error handling message")
                    error_response = {
                        "error": str(e),
                        "status": "error"
                    }
                    await websocket.send(json.dumps(error_response))
        except websockets.exceptions.ConnectionClosed:
            logger.info("Client disconnected")
        except Exception as e:
            logger.exception("Unexpected error in handle_message")

    async def restore_game(self, params: dict) -> dict:
        """Restore a game using the provided parameters."""
        try:
            # Extract required parameters
            dice_set_name = params.get("dice_set")
            height = params.get("height")
            width = params.get("width")
            scores = params.get("scores")
            dice = params.get("dice")
            
            # Optional parameters
            duration = params.get("duration", 120)
            min_legal = params.get("min_legal", 3)
            
            # Validate required parameters
            if not all([dice_set_name, height, width, scores, dice]):
                return {
                    "error": "Missing required parameters: dice_set, height, width, scores, dice",
                    "status": "error"
                }
            
            # Get dice set
            dice_set = DiceSet.get_by_name(dice_set_name)
            if not dice_set:
                return {
                    "error": f"Unknown dice set: {dice_set_name}",
                    "status": "error"
                }
            
            # Create game instance
            game = Game(
                dice_set=dice_set,
                height=height,
                width=width,
                scores=scores,
                duration=duration,
                min_legal=min_legal
            )
            
            # Restore the game
            game.restore_game(dice)
            
            # Return game state
            return {
                "status": "success",
                "game_state": {
                    "board": game.board,
                    "legal_words": list(game.legal.words),
                    "legal_score": game.legal.score,
                    "legal_longest": game.legal.longest,
                    "found_words": list(game.found.words),
                    "found_score": game.found.score,
                    "found_longest": game.found.longest,
                    "bad_words": list(game.bad.words),
                    "duration": game.duration,
                    "min_legal": game.min_legal,
                    "scores": game.scores
                }
            }
            
        except Exception as e:
            logger.exception("Error in restore_game")
            return {
                "error": str(e),
                "status": "error"
            }

    async def fill_board(self, params: dict) -> dict:
        """Fill a board using the provided parameters."""
        try:
            # Extract required parameters
            dice_set_name = params.get("dice_set")
            height = params.get("height")
            width = params.get("width")
            scores = params.get("scores")
            
            # Optional parameters
            duration = params.get("duration", 120)
            min_legal = params.get("min_legal", 3)
            min_words = params.get("min_words", 1)
            max_words = params.get("max_words", -1)
            min_score = params.get("min_score", 1)
            max_score = params.get("max_score", -1)
            min_longest = params.get("min_longest", 3)
            max_longest = params.get("max_longest", -1)
            max_tries = params.get("max_tries", 100000)
            random_seed = params.get("random_seed")
            
            # Validate required parameters
            if not all([dice_set_name, height, width, scores]):
                return {
                    "error": "Missing required parameters: dice_set, height, width, scores",
                    "status": "error"
                }
            
            # Get dice set
            dice_set = DiceSet.get_by_name(dice_set_name)
            if not dice_set:
                return {
                    "error": f"Unknown dice set: {dice_set_name}",
                    "status": "error"
                }
            
            # Create game instance
            game = Game(
                dice_set=dice_set,
                height=height,
                width=width,
                scores=scores,
                duration=duration,
                min_legal=min_legal
            )
            
            # Fill the board
            game.fill_board(
                min_words=min_words,
                max_words=max_words,
                min_score=min_score,
                max_score=max_score,
                min_longest=min_longest,
                max_longest=max_longest,
                max_tries=max_tries,
                random_seed=random_seed
            )
            
            # Return game state
            return {
                "status": "success",
                "game_state": {
                    "board": game.board,
                    "legal_words": list(game.legal.words),
                    "legal_score": game.legal.score,
                    "legal_longest": game.legal.longest,
                    "found_words": list(game.found.words),
                    "found_score": game.found.score,
                    "found_longest": game.found.longest,
                    "bad_words": list(game.bad.words),
                    "duration": game.duration,
                    "min_legal": game.min_legal,
                    "scores": game.scores
                }
            }
            
        except Exception as e:
            logger.exception("Error in fill_board")
            return {
                "error": str(e),
                "status": "error"
            }

    async def start_server(self):
        """Start the WebSocket server."""
        logger.info(f"Starting WebSocket server on {self.host}:{self.port}")
        async with websockets.serve(self.handle_message, self.host, self.port):
            logger.info("WebSocket server started successfully")
            await asyncio.Future()  # Run forever


async def main():
    """Main entry point for the backend server."""
    logging.basicConfig(level=logging.INFO)
    backend = BoggleBackend()
    await backend.start_server()


if __name__ == "__main__":
    asyncio.run(main())