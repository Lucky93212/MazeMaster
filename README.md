# MazeMaster - Retro Arcade Maze Game

A retro-style maze game where you play as a red square with a gun, trying to escape increasingly complex mazes while avoiding orange adversaries.

## Features

- **Progressive Difficulty**: Mazes get more complex as levels increase
- **Smart Adversaries**: Orange enemies that hunt you down, getting faster each level
- **Laser Combat**: Shoot enemies with your gun that can rotate in all directions
- **Explosion Effects**: Visual feedback when enemies are destroyed
- **Simple Navigation**: Move to the immediate next tunnel with a single keypress
- **Retro Aesthetics**: Pixelated graphics with classic arcade feel

## Controls

- **Arrow Keys**: Hold to move continuously in that direction
- **W/A/S/D Keys**: Rotate gun (W=up, S=down, A=left, D=right)
- **SPACE**: Shoot laser
- **R**: Restart game (when game over)
- **ESC**: Return to menu

## Gameplay

1. **Objective**: Reach the green exit square to complete each level
2. **Enemies**: Starting from level 2, orange adversaries will chase you
3. **Combat**: Shoot enemies to clear your path - new ones will spawn to replace them
4. **Scoring**: 
   - 100 points per enemy destroyed
   - 1000 × level points for completing a level

## Installation & Running

Make sure you have pygame installed:
```bash
sudo apt install python3-pygame
```

Run the game:
```bash
python3 mazemaster.py
```

## Game Mechanics

- **Simple Navigation**: No need for precise positioning - just hold a direction to move continuously
- **Gun System**: Your gun orientation is independent of movement direction
- **Enemy AI**: Adversaries use pathfinding to chase you intelligently
- **Progressive Challenge**: More enemies and faster speeds as you advance

Enjoy the retro arcade experience!
