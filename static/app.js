const centralBtn = document.getElementById('central-btn');
const iconMic = document.getElementById('icon-mic');
const iconPause = document.getElementById('icon-pause');
const iconStop = document.getElementById('icon-stop');
const iconSendCentral = document.getElementById('icon-send-central');

const textInput = document.getElementById('text-input');
const inputActionBtn = document.getElementById('input-action-btn');

const statusBar = document.getElementById('status-bar');
const statusText = document.getElementById('status-text');
const grid = document.getElementById('flashcards-container');
const audioPlayer = document.getElementById('audio-player');

// Context Memory for Agentic Searches
let currentContext = [];

// Initialize Web Speech API
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

if (!SpeechRecognition) {
    alert("Speech Recognition API is not supported in this browser. Please use Google Chrome or Safari.");
}

const recognition = new SpeechRecognition();
recognition.continuous = false;
recognition.interimResults = false;

let isRecording = false;

// The Central "God Button" State Machine
function updateCentralButton() {
    // Hide all icons first
    iconMic.classList.add('hidden');
    iconPause.classList.add('hidden');
    iconStop.classList.add('hidden');
    iconSendCentral.classList.add('hidden');
    centralBtn.classList.remove('active');

    // State 1: Text exists
    if (textInput.value.trim() !== '') {
        iconSendCentral.classList.remove('hidden');
        centralBtn.title = "Send";
    } 
    // State 2: Recording
    else if (isRecording) {
        iconStop.classList.remove('hidden');
        centralBtn.classList.add('active'); // pulses red
        centralBtn.title = "Stop Recording";
    } 
    // State 3: Audio is playing
    else if (!audioPlayer.paused && audioPlayer.currentTime > 0 && !audioPlayer.ended) {
        iconPause.classList.remove('hidden');
        centralBtn.title = "Pause Audio";
    } 
    // State 4: Default Mic
    else {
        iconMic.classList.remove('hidden');
        centralBtn.title = "Click to Speak";
    }
}

centralBtn.addEventListener('click', async () => {
    // State 1: Send Text
    if (textInput.value.trim() !== '') {
        const topic = textInput.value.trim();
        await generateContent(topic);
    } 
    // State 2: Stop Recording
    else if (isRecording) {
        stopRecording();
    } 
    // State 3: Pause Audio
    else if (!audioPlayer.paused && audioPlayer.currentTime > 0 && !audioPlayer.ended) {
        audioPlayer.pause();
    } 
    // State 4: Start Recording
    else {
        startRecording();
    }
});

// Audio Player Event Listeners (Triggers State Machine)
audioPlayer.addEventListener('play', updateCentralButton);
audioPlayer.addEventListener('pause', updateCentralButton);
audioPlayer.addEventListener('ended', updateCentralButton);

// Text Input Listeners (Triggers State Machine)
textInput.addEventListener('input', () => {
    updateCentralButton();
    // Handle the Clear 'X' button inside the text box
    if (textInput.value.trim() !== '') {
        inputActionBtn.classList.remove('hidden');
    } else {
        inputActionBtn.classList.add('hidden');
    }
});

// Clear Button Logic
inputActionBtn.addEventListener('click', () => {
    textInput.value = '';
    inputActionBtn.classList.add('hidden');
    updateCentralButton();
});

textInput.addEventListener('keypress', async (e) => {
    if (e.key === 'Enter' && textInput.value.trim() !== '') {
        const topic = textInput.value.trim();
        await generateContent(topic);
    }
});

// Microphone Logic (Click to Toggle)
function startRecording() {
    isRecording = true;
    updateCentralButton();
    showStatus('Listening...');
    recognition.start();
}

function stopRecording() {
    if(isRecording) {
        isRecording = false;
        updateCentralButton();
        recognition.stop();
    }
}

recognition.onresult = async (event) => {
    const transcript = event.results[0][0].transcript;
    console.log("Transcribed:", transcript);
    
    // Stop recording immediately so UI resets from pulsing red
    stopRecording();
    
    // Automatically trigger generate
    await generateContent(transcript);
};

recognition.onerror = (event) => {
    console.error("Speech Recognition Error:", event.error);
    if(event.error !== 'no-speech') {
        showStatus('Mic error: ' + event.error);
        setTimeout(hideStatus, 5000);
    } else {
        hideStatus();
    }
    isRecording = false;
    updateCentralButton();
};


// Core Generation Logic
async function generateContent(topic) {
    showStatus(`Researching: "${topic}"...`);
    grid.innerHTML = ''; // Clear old cards
    audioPlayer.pause();
    
    try {
        const response = await fetch('/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                topic: topic,
                context: currentContext.length > 0 ? currentContext : null
            })
        });
        
        if (!response.ok) throw new Error("Failed to generate content");
        
        const data = await response.json();
        
        // Update context memory
        currentContext = data.flashcards.map(card => card.headline);
        
        // Render flashcards
        data.flashcards.forEach(card => {
            const el = document.createElement('div');
            el.className = 'flashcard';
            el.innerHTML = `
                <div class="headline">${card.headline}</div>
                <div class="key-stat">${card.key_stat}</div>
                <div class="summary">${card.short_summary}</div>
            `;
            // Trigger a full deep dive on this specific topic!
            el.onclick = () => {
                // Clear text input since we don't want it lingering
                textInput.value = "";
                textInput.dispatchEvent(new Event('input'));
                generateContent("Deep dive into: " + card.headline);
            };
            grid.appendChild(el);
        });
        
        hideStatus();
        
        // Play audio
        audioPlayer.src = data.audio_url;
        audioPlayer.play();
        
    } catch (e) {
        console.error(e);
        showStatus('Error generating content. Check terminal for details.');
        setTimeout(hideStatus, 3000);
    }
}

function showStatus(text) {
    statusText.innerText = text;
    statusBar.classList.remove('hidden');
}

function hideStatus() {
    statusBar.classList.add('hidden');
}

// Initial state load
updateCentralButton();
