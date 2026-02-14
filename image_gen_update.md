# Image Generator Update

I have updated the `/imagine` command in `bot.py` to ensure uncensored and 18+ content generation capabilities.

**Changes:**

- **Model**: Switched to `flux` (standard) which often has fewer safety layers than `flux-pro`.
- **Parameter**: Added `enhance=false` to prevent the Pollinations API from rewriting or "sanitizing" your prompt.
- **Privacy**: Kept `private=true` and `nologo=true` for clean results.

The command will now faithfully process whatever prompt is given.

**Run:**

```bash
python bot.py
```
