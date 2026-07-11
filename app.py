import streamlit as st
import os
from agent import search_news, generate_script, generate_audio

st.set_page_config(page_title="AI Radio Host", page_icon="📻", layout="centered")

st.title("📻 Personalized AI Radio Host")
st.markdown("Powered by **Fireworks AI (Llama 3)**, **DuckDuckGo News**, and **Edge TTS**.")

# Check for API key early
if not os.environ.get("FIREWORKS_API_KEY"):
    st.warning("⚠️ FIREWORKS_API_KEY environment variable is not set. The app will fail during script generation. Please set it in your terminal before running.")

topic = st.text_input("What topic would you like to hear about today?", placeholder="e.g., SpaceX, Artificial Intelligence, Global Markets")

if st.button("Generate Broadcast"):
    if not topic:
        st.error("Please enter a topic.")
    else:
        with st.status("Generating your broadcast...", expanded=True) as status:
            try:
                # Step 1: Search News
                st.write("🔍 Searching for the latest news on Google News...")
                news_items = search_news(topic, max_results=5)
                if not news_items:
                    st.error("Could not find any recent news for that topic.")
                    status.update(label="Failed to find news.", state="error")
                    st.stop()
                
                # Step 2: Generate Script
                st.write("🧠 Writing the script using Fireworks AI...")
                script = generate_script(topic, news_items)
                
                st.markdown("**Generated Script:**")
                st.info(script)
                
                # Step 3: Generate Audio
                st.write("🎙️ Synthesizing voice...")
                audio_file = "broadcast.mp3"
                generate_audio(script, audio_file)
                
                status.update(label="Broadcast ready!", state="complete", expanded=False)
                
                st.success("✅ Audio generated successfully!")
                st.audio(audio_file, format="audio/mp3", autoplay=True)
                
            except Exception as e:
                st.error(f"An error occurred: {e}")
                status.update(label="An error occurred.", state="error")
