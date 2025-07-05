#!/usr/bin/env python3
"""
Simple test script for the TBoggle WebSocket backend.
"""
import asyncio
import json
import websockets
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_backend():
    """Test the WebSocket backend functionality."""
    uri = "ws://localhost:8765"
    
    try:
        async with websockets.connect(uri) as websocket:
            logger.info("Connected to WebSocket server")
            
            # Test restore_game endpoint
            restore_message = {
                "endpoint": "restore_game",
                "params": {
                    "dice_set": "4-classic",
                    "height": 4,
                    "width": 4,
                    "scores": [0, 0, 0, 1, 1, 2, 3, 5, 11, 11, 11, 11, 11, 11, 11, 11, 11],
                    "dice": "ADYERESTLPNAGIE1",
                    "duration": 180,
                    "min_legal": 3
                }
            }
            
            await websocket.send(json.dumps(restore_message))
            response = await websocket.recv()
            result = json.loads(response)
            
            if result["status"] == "success":
                logger.info("restore_game test passed")
                logger.info(f"Legal words found: {len(result['game_state']['legal_words'])}")
                logger.info(f"Board: {result['game_state']['board']}")
            else:
                logger.error(f"restore_game test failed: {result}")
            
            # Test fill_board endpoint
            fill_message = {
                "endpoint": "fill_board",
                "params": {
                    "dice_set": "4-classic",
                    "height": 4,
                    "width": 4,
                    "scores": [0, 0, 0, 1, 1, 2, 3, 5, 11, 11, 11, 11, 11, 11, 11, 11, 11],
                    "duration": 180,
                    "min_legal": 3,
                    "min_words": 10,
                    "max_words": 100,
                    "random_seed": 42
                }
            }
            
            await websocket.send(json.dumps(fill_message))
            response = await websocket.recv()
            result = json.loads(response)
            
            if result["status"] == "success":
                logger.info("fill_board test passed")
                logger.info(f"Legal words found: {len(result['game_state']['legal_words'])}")
                logger.info(f"Board: {result['game_state']['board']}")
            else:
                logger.error(f"fill_board test failed: {result}")
            
            # Test invalid endpoint
            invalid_message = {
                "endpoint": "invalid_endpoint",
                "params": {}
            }
            
            await websocket.send(json.dumps(invalid_message))
            response = await websocket.recv()
            result = json.loads(response)
            
            if result["status"] == "error":
                logger.info("Invalid endpoint test passed")
            else:
                logger.error(f"Invalid endpoint test failed: {result}")
                
    except ConnectionRefusedError:
        logger.error("Could not connect to WebSocket server. Is it running?")
    except Exception as e:
        logger.error(f"Test failed with exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_backend())