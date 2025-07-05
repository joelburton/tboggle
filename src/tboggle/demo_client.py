#!/usr/bin/env python3
"""
Demo client for TBoggle WebSocket backend.

This script demonstrates how to use both the restore_game and fill_board endpoints
of the TBoggle WebSocket backend server.

Usage:
    python src/tboggle/demo_client.py

Make sure to start the backend server first:
    python src/tboggle/backend.py
"""

import asyncio
import json
import websockets
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TBoggleClient:
    """WebSocket client for TBoggle backend."""
    
    def __init__(self, uri: str = "ws://localhost:8765"):
        self.uri = uri
        self.websocket = None
    
    async def connect(self):
        """Connect to the WebSocket server."""
        try:
            self.websocket = await websockets.connect(self.uri)
            logger.info(f"Connected to TBoggle server at {self.uri}")
        except Exception as e:
            logger.error(f"Failed to connect to server: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from the WebSocket server."""
        if self.websocket:
            await self.websocket.close()
            logger.info("Disconnected from server")
    
    async def send_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send a request to the server and return the response."""
        if not self.websocket:
            raise Exception("Not connected to server")
        
        message = {
            "endpoint": endpoint,
            "params": params
        }
        
        logger.info(f"Sending request to {endpoint}")
        await self.websocket.send(json.dumps(message))
        
        response = await self.websocket.recv()
        result = json.loads(response)
        
        if result["status"] == "error":
            logger.error(f"Server error: {result['error']}")
        else:
            logger.info(f"Request to {endpoint} successful")
        
        return result
    
    async def restore_game_demo(self):
        """Demonstrate the restore_game endpoint."""
        print("\n" + "="*60)
        print("🎲 RESTORE GAME DEMO")
        print("="*60)
        print("This demo restores a specific Boggle game using predefined dice.")
        print("The dice string represents the face of each die on the board.")
        
        params = {
            "dice_set": "4-classic",
            "height": 4,
            "width": 4,
            "scores": [0, 0, 0, 1, 1, 2, 3, 5, 11, 11, 11, 11, 11, 11, 11, 11, 11],
            "dice": "ADYERESTLPNAGIE1",  # Specific dice configuration
            "duration": 180,
            "min_legal": 3
        }
        
        print(f"\nParameters:")
        print(f"  Dice Set: {params['dice_set']}")
        print(f"  Board Size: {params['height']}x{params['width']}")
        print(f"  Dice Configuration: {params['dice']}")
        print(f"  Game Duration: {params['duration']} seconds")
        print(f"  Minimum Word Length: {params['min_legal']}")
        
        result = await self.send_request("restore_game", params)
        
        if result["status"] == "success":
            self.display_game_state(result["game_state"], "Restored Game")
        else:
            print(f"❌ Error: {result['error']}")
        
        return result
    
    async def fill_board_demo(self):
        """Demonstrate the fill_board endpoint."""
        print("\n" + "="*60)
        print("🎯 FILL BOARD DEMO")
        print("="*60)
        print("This demo generates a new random Boggle board with constraints.")
        print("The board will be optimized to meet the specified criteria.")
        
        params = {
            "dice_set": "4-classic",
            "height": 4,
            "width": 4,
            "scores": [0, 0, 0, 1, 1, 2, 3, 5, 11, 11, 11, 11, 11, 11, 11, 11, 11],
            "duration": 180,
            "min_legal": 3,
            "min_words": 30,      # At least 30 words
            "max_words": 100,     # At most 100 words
            "min_score": 50,      # At least 50 points
            "max_score": 200,     # At most 200 points
            "min_longest": 6,     # At least one 6-letter word
            "max_longest": 12,    # No words longer than 12 letters
            "random_seed": 42     # For reproducible results
        }
        
        print(f"\nParameters:")
        print(f"  Dice Set: {params['dice_set']}")
        print(f"  Board Size: {params['height']}x{params['width']}")
        print(f"  Word Count Range: {params['min_words']}-{params['max_words']}")
        print(f"  Score Range: {params['min_score']}-{params['max_score']}")
        print(f"  Longest Word Range: {params['min_longest']}-{params['max_longest']} letters")
        print(f"  Random Seed: {params['random_seed']}")
        
        result = await self.send_request("fill_board", params)
        
        if result["status"] == "success":
            self.display_game_state(result["game_state"], "Generated Board")
        else:
            print(f"❌ Error: {result['error']}")
        
        return result
    
    def display_game_state(self, game_state: Dict[str, Any], title: str):
        """Display the game state in a formatted way."""
        print(f"\n📊 {title.upper()} RESULTS")
        print("-" * 40)
        
        # Display the board
        print("🎲 Board:")
        board = game_state["board"]
        for row in board:
            print("    " + " ".join(f"{cell:>2}" for cell in row))
        
        # Display statistics
        print(f"\n📈 Statistics:")
        print(f"  Total Legal Words: {len(game_state['legal_words'])}")
        print(f"  Total Possible Score: {game_state['legal_score']}")
        print(f"  Longest Word Length: {game_state['legal_longest']}")
        print(f"  Words Found: {len(game_state['found_words'])}")
        print(f"  Current Score: {game_state['found_score']}")
        
        # Display some example words
        legal_words = game_state['legal_words']
        if legal_words:
            print(f"\n📝 Sample Legal Words:")
            # Show first 10 words, sorted by length
            sample_words = sorted(legal_words, key=len, reverse=True)[:10]
            for i, word in enumerate(sample_words, 1):
                print(f"  {i:2}. {word} ({len(word)} letters)")
            
            if len(legal_words) > 10:
                print(f"  ... and {len(legal_words) - 10} more words")
    
    async def run_demo(self):
        """Run the complete demo."""
        print("🚀 TBoggle WebSocket Client Demo")
        print("This demo showcases both endpoints of the TBoggle backend.")
        print("Make sure the backend server is running on ws://localhost:8765")
        
        try:
            await self.connect()
            
            # Demo 1: Restore a specific game
            await self.restore_game_demo()
            
            # Demo 2: Generate a new board
            await self.fill_board_demo()
            
            print("\n" + "="*60)
            print("✅ Demo completed successfully!")
            print("="*60)
            
        except (ConnectionRefusedError, OSError):
            print("\n❌ Error: Could not connect to the WebSocket server.")
            print("Make sure to start the backend server first:")
            print("  python src/tboggle/backend.py")
        except Exception as e:
            print(f"\n❌ Error: {e}")
        finally:
            await self.disconnect()


async def main():
    """Main entry point for the demo."""
    client = TBoggleClient()
    await client.run_demo()


if __name__ == "__main__":
    asyncio.run(main())