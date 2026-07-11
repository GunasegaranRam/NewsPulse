# 🚀 AI Radio Host: V3 Developer Log

Welcome to the V3 Dev Log! This document outlines the major architectural upgrades we implemented to transition the project from a V2 functional prototype to a true production-grade Startup Product.

## The V3 Vision (Speed & Conversational Continuity)
In V2, we proved that we could synthesize a dynamic AI Radio Host in the browser. However, there were severe latency issues (re-searching Google News for every single follow-up question) and UI friction (the Microphone button wasn't fluid enough). 

For V3, we attacked these exact pain points with several massive upgrades:

## 1. Stateful Python Memory (Instant Deep Dives)
**The Problem:** In V2, when the user asked *"Tell me more about the first topic"*, the LLM extracted the keyword and passed it back to Google News. This forced a massive 15-second latency delay while the backend scraped Google again.
**The V3 Solution:** We implemented a local Dictionary Cache (`latest_news`) mapped to the user's `session_id`. Now, when the user does an initial search, all raw HTML articles are securely cached. If they ask a conversational follow-up, the system completely **skips Google News**, grabs the cached facts from RAM, and generates a deeply detailed response in a fraction of the time.

## 2. The Hybrid Rule-Based Router
**The Problem:** We rely on an LLM (`accounts/fireworks/models/gpt-oss-120b`) to act as an "Intelligent Router", deciding if a user's voice prompt is a brand new `SEARCH` or a `CONVERSATIONAL` follow-up. Occasionally, the LLM would glitch and return an empty `NoneType`, which would route ambiguous phrases like *"what is the first one"* to a literal Google News search.
**The V3 Solution:** We implemented a **Hybrid Rule-Based Fallback** (similar to how Siri/Alexa work under the hood). Before failing, the system scans the raw text for specific conversational triggers (*"first", "second", "this", "that", "more", "explain"*). If detected, it overrides the LLM and mathematically forces a `CONVERSATIONAL` deep dive route. 

## 3. Instant UI Pause & Fluid State Machine
**The Problem:** The central "God Button" had a 250ms latency delay when clicking to pause the audio, causing the UI to feel broken and unresponsive. Also, the browser's strict Web Audio API policies kept randomly muting the visualizer.
**The V3 Solution:** 
*   Removed the 250ms Javascript delay, making pausing and unpausing lightning fast via a new Single-Click/Double-Click architecture.
*   Added a proper **Play Icon** to the HTML so users explicitly know they can resume the audio.
*   Ripped out the buggy Web Audio API entirely. We now rely on native HTML5 Audio playback combined with an intelligent CSS `@keyframes` pulse animation that simulates the visualizer perfectly with zero risk of browser muting.

## 4. Comprehensive Flashcards
**The Problem:** When doing a Deep Dive, the UI flashcards were artificially constricted to just 1 sentence.
**The V3 Solution:** Rewrote the LLM System Prompt. If the Intelligent Router flags a prompt as `CONVERSATIONAL`, the AI is explicitly instructed to break the rules and return massive, highly detailed paragraphs to ensure the user gets exactly what they asked for.

## What's Next? (V4 Horizon)
To fully reach industry-leading performance, our next horizon is:
*   **WebSockets:** Streaming the text directly into the Edge TTS engine in chunks.
*   **Live Transcription:** Streaming the user's voice straight to the backend rather than waiting for them to stop talking.
