# 🚀 NewsPulse: V1 Developer Log

Welcome to the V1 Dev Log. This document serves as a comprehensive record of the initial planning, the hurdles encountered, and the architectural changes made during the development of the V1 MVP of NewsPulse.

## 1. Initial Plan
The original goal was to build a simple, containerized web application that acts as an AI interactive news host. The planned stack was:
*   **Frontend:** Streamlit (`app.py`) for a fast, interactive web UI.
*   **News Source:** `duckduckgo-search` library to pull recent news articles.
*   **LLM Brain:** Fireworks AI (using standard Llama 3 models) via the OpenAI python client to synthesize scripts.
*   **Voice Synthesis:** `edge-tts` (Microsoft Edge TTS API) for free, high-quality audio generation.
*   **Environment:** Managed via `uv` with a standard `requirements.txt` and packaged with a `Dockerfile`.

## 2. Hurdles Encountered & Solutions Implemented

### Issue 1: Slow Rust Compilation on Mac
*   **The Problem:** Running `uv pip install` hung for minutes because `duckduckgo-search` relies on `pyreqwest-impersonate`, a massive Rust security library that had to compile from scratch on the local M-series Mac.
*   **The Fix:** We waited for it to finish, but this foreshadowed deeper issues with the DuckDuckGo approach.

### Issue 2: DuckDuckGo Bot Blocking (202 Ratelimit)
*   **The Problem:** Upon running the app, DuckDuckGo instantly threw a `202 Ratelimit` error. They have become extremely aggressive against bots, making it unreliable for a hackathon demo.
*   **The Fix:** **Architectural Pivot.** We completely removed `duckduckgo-search` and its heavy dependencies. We rewrote the `search_news` function to use Python's built-in `urllib` and `xml.etree` to fetch **Google News RSS feeds**. This is 100% free, requires no complex libraries, and has no strict rate limits.

### Issue 3: OpenAI Client Proxy Error
*   **The Problem:** The app crashed with `Client.__init__() got an unexpected keyword argument 'proxies'`.
*   **The Fix:** This was a classic version mismatch between an older `openai` library and a newer underlying `httpx` networking library. We updated `requirements.txt` to unpin `openai` (`>=1.52.0`) and explicitly restrict `httpx` (`<0.28.0`), locking in stable versions.

### Issue 4: Fireworks AI "404 Model Not Found"
*   **The Problem:** The API returned `404 Not Found` for standard models like `llama-v3p1-70b-instruct` and `mixtral-8x7b-instruct`. We discovered that these models were marked as "Serverless: Not supported" on Fireworks AI.
*   **The Fix:** Realizing the hackathon provided a highly restricted tier of custom models, we ran a `curl` command against the API to pull the exact list of permitted models. We switched the agent to use `accounts/fireworks/models/deepseek-v4-pro`, which was on the allowed list.

### Issue 5: Streamlit Nested Expander UI Crash
*   **The Problem:** Streamlit threw an error: `Expanders may not be nested inside other expanders.`
*   **The Fix:** The `st.status` loading spinner acts as an expander under the hood. We had placed an `st.expander` inside it to show the script. We removed the nested expander and used a clean `st.info` text box instead.

### Issue 6: Microsoft Edge TTS 403 Forbidden
*   **The Problem:** The `edge-tts` library threw a `403 Forbidden` error. Microsoft had rotated their authentication protocol, breaking older versions of the library.
*   **The Fix:** We forcefully upgraded `edge-tts` from `v6.1.12` to `v7.2.8` in `requirements.txt` and restarted the Streamlit server to load the patched library into memory.

### Issue 7: The LLM "Thinking" Leak & Voice Preferences
*   **The Problem:** `deepseek-v4-pro` is a "reasoning" model, meaning it outputs its internal "Chain of Thought" out loud before the script. The TTS engine dutifully read the AI's inner monologue. Additionally, a crisp female voice was requested.
*   **The Fix:** 
    *   Switched the LLM from a reasoning model to a pure text generator on the allowed list (`accounts/fireworks/models/gpt-oss-120b`).
    *   Added strict system prompts to forbid introductory greetings (e.g., "Hello listeners").
    *   Switched the TTS voice to `en-US-AriaNeural`, a highly professional and crisp female voice.

### Issue 8: Manual Audio Playback
*   **The Problem:** The user had to manually click "Play" on the audio widget after generation.
*   **The Fix:** Passed the `autoplay=True` parameter to `st.audio()` in `app.py`, creating a seamless, magic-like user experience.

## 3. Final State of V1
The V1 MVP is stable, rate-limit proof, heavily optimized for the specific Hackathon API restrictions, and provides a seamless "Topic -> Script -> Audio" pipeline.
