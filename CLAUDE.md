# pyunicodegame

A pygame library for TUI-style unicode graphics.

## LLM Discoverability

This library is designed to be easily understood by LLMs when imported in other projects. Maintain these conventions:

### `__init__.py` Requirements

1. **Module docstring** - Must include a QUICK START example showing minimal working code
2. **PUBLIC API section** - List all public functions/classes with one-line descriptions
3. **`__all__`** - Explicitly export the public API
4. **Function docstrings** - Each public function needs:
   - One-line description
   - Args with types and descriptions
   - Returns description
   - Example usage

### When Adding New Public API

1. Add to `__all__`
2. Add to PUBLIC API section in module docstring
3. Write comprehensive docstring with example
4. Update QUICK START if it's a core function

## Project Structure

- `src/pyunicodegame/__init__.py` - Public API, factory functions, core loop (main file LLMs read)
- `src/pyunicodegame/_window.py` - Window class implementation
- `src/pyunicodegame/_sprites.py` - Sprite, Animation, EffectSprite, EffectSpriteEmitter classes
- `src/pyunicodegame/_lighting.py` - Light class and lighting helpers
- `src/pyunicodegame/fonts/` - Bundled BDF/OTF fonts
- `examples/` - Usage examples

The PUBLIC API section in `__init__.py` lists key class methods so LLMs can discover them without reading the implementation files.
