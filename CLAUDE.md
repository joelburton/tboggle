# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TBoggle is a terminal-based Boggle game implemented in Python using the Textual framework. The game uses a hybrid architecture with C extensions for performance-critical word finding operations and a Python frontend for the user interface.

## Core Architecture

### Key Components

- **Main Game Loop** (`boggle.py`): Textual app with TUI interface, game state management, and user input handling
- **Game Logic** (`game.py`): Core game mechanics, word validation, scoring, and board state management
- **Word Finding Engine** (`libwords.c`): High-performance C extension for finding valid words on the board using DAWG (Directed Acyclic Word Graph) data structure
- **Configuration** (`chooser.py`): Game setup interface with persistent preferences
- **Dice Systems** (`dice.py`): Multiple Boggle dice set definitions (4x4, 5x5, 6x6 variants)

### Data Flow

1. Game configuration selected via Chooser UI
2. Board generation using C extension with dice rolling and word finding
3. Main game loop handles user input and validates guesses against pre-computed word list
4. Results displayed with statistics and missed words

## Development Commands

### Building the Project
```bash
# Install in development mode (builds C extension)
pip install -e .

# Build C extension manually if needed
python setup.py build_ext --inplace
```

### Running the Game
```bash
# Run the game
tboggle

# Run directly from source
python -m tboggle.boggle
```

### Testing
```bash
# Run the main game components
python src/tboggle/game.py  # Test game logic
python src/tboggle/chooser.py  # Test configuration UI
```

## Technical Details

### C Extension Integration
- Uses ctypes to interface with `libwords.c` compiled as shared library
- DAWG dictionary loaded from `words.dat` binary file
- Word definitions stored in SQLite database (`all.sqlite3`)

### Performance Considerations
- Word finding algorithm uses recursive backtracking with bitmask optimization
- Board generation may require multiple attempts to meet min/max constraints
- Uses binary tree for duplicate word detection during board analysis

### File Structure
- `src/tboggle/`: Main Python package
- `libwords.c` + `tree.c`: C extension source
- `words.dat`: Binary DAWG dictionary
- `all.sqlite3`: Word definitions database
- `styles.css`: Textual UI styling

## Common Development Patterns

When working with this codebase:
- Game state is managed through reactive Textual widgets
- C extension functions use ctypes parameter type definitions
- Word validation happens against pre-computed legal word sets
- Board constraints are enforced during generation, not gameplay
- UI uses CSS-like styling for Textual components