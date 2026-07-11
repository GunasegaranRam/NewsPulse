# 🚀 NewsPulse: V2 Developer Log

Welcome to the V2 Dev Log. This document serves as a historical record of our journey taking the project from a simple V1 MVP to a robust, interactive, Agentic Voice Assistant.

## The Architectural Pivot
In V1, we built the app using **Streamlit**. While Streamlit was great for a rapid MVP, it lacked the granular frontend control required to build a premium, glassmorphism UI and a true interactive Voice Agent. 

For V2, we completely pivoted the architecture:
*   **Backend:** Migrated to **FastAPI**, creating a lightning-fast, asynchronous REST API serving `/generate`.
*   **Frontend:** Built a custom **Vanilla JS, HTML, and CSS** client for maximum control over animations, state machines, and the Web Speech API.

## Major Features Built
1.  **The "God Button" State Machine:** Replaced cluttered UI controls with a single, massive central button that dynamically shape-shifts (Mic, Pause, Stop, Send) based on the exact state of the application.
2.  **Agentic Context Memory:** Implemented an `extract_intent` LLM layer. The AI now reads the Flashcards currently on your screen to deduce what you mean when you say *"Tell me about the first one"*.
3.  **True Deep Dives:** Clicking a flashcard now triggers a brand new, highly specific Google News search and generates a fresh audio broadcast focusing solely on that topic.
4.  **Premium Aesthetics:** Implemented a dark-mode glassmorphism UI with crisp layouts and a dynamic clear ('X') button.
5.  **Voice Upgrade:** Upgraded the Edge TTS engine to `en-US-ChristopherNeural` for a crisp, professional, male news-anchor voice.

## Crushing the Bugs (Lessons Learned)

During the V2 build, we encountered and solved several complex edge cases:

> [!WARNING]
> **Bug 1: The "Aborted" Microphone Error**
> *   **Cause:** We initially used a "Hold to Talk" (`mousedown`/`mouseup`) event listener for the microphone. Web browsers often crash the Web Speech API if these events fire too rapidly (e.g., a quick tap).
> *   **Solution:** Ripped out the "Hold" logic and implemented a robust **Click to Toggle** (Click Start, Click Stop) state machine.

> [!CAUTION]
> **Bug 2: The JSON "Extra Data" 500 Crash**
> *   **Cause:** When asked for a Deep Dive, the AI would generate perfect JSON flashcards, but sometimes append conversational junk (e.g., *"Hope this helps!"*) at the very end. The Python `json.loads` parser instantly choked on this and crashed the server.
> *   **Solution:** Built a surgical Python fallback catching `json.JSONDecodeError`. We now use the `e.pos` attribute to mathematically calculate exactly where the valid JSON ends, slicing off any AI hallucinations to ensure 100% backend uptime.

> [!NOTE]
> **Bug 3: The "Deep Dive Into" Keyword Glitch**
> *   **Cause:** When passing *"Deep dive into SK Hynix"* to the intent extractor, the LLM was returning the raw string instead of the pure keyword, leading to poor Google News search results.
> *   **Solution:** Updated the System Prompt to explicitly teach the AI how to scrub out conversational filler, ensuring it passes the purest keywords to Google News.

> [!TIP]
> **Bug 4: The `NoneType` Edge Case**
> *   **Cause:** Rarely, the Fireworks AI would intercept a prompt and return an entirely empty `None` response, crashing the intent extractor.
> *   **Solution:** Implemented null-safety checks (`content if content else fallback`). If the AI glitches out, the backend gracefully falls back to searching exactly what you typed instead of crashing.

## What's Next (V3 Horizon)
We have laid the groundwork for an enterprise-grade app. The newly created `v3-improvements` branch will explore:
*   Stateful Database Memory for instant Deep Dives.
*   WebSocket Streaming for zero-wait audio generation.
*   True conversational interruptions.
*   Web Audio API Visualizers.
