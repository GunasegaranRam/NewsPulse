const centralBtn = document.getElementById('central-btn');
const iconMic = document.getElementById('icon-mic');
const iconPause = document.getElementById('icon-pause');
const iconPlay = document.getElementById('icon-play');
const iconStop = document.getElementById('icon-stop');
const iconSendCentral = document.getElementById('icon-send-central');

const textInput = document.getElementById('text-input');
const inputActionBtn = document.getElementById('input-action-btn');

const statusBar = document.getElementById('status-bar');
const statusText = document.getElementById('status-text');
const grid = document.getElementById('flashcards-container');
const audioPlayer = document.getElementById('audio-player');

// Context Memory
let currentContext = [];

// Initialize Web Speech API
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

let audioUnlocked = false;
function unlockAudio() {
    if (audioUnlocked) return;
    // Play and immediately pause to unlock the audio element on iOS/Chrome
    audioPlayer.play().then(() => {
        audioPlayer.pause();
        audioPlayer.currentTime = 0;
    }).catch(() => {});
    audioUnlocked = true;
}

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
    iconPlay.classList.add('hidden');
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
    // State 4: Audio is paused
    else if (audioPlayer.paused && audioPlayer.currentTime > 0 && !audioPlayer.ended) {
        iconPlay.classList.remove('hidden');
        centralBtn.title = "Play Audio";
    }
    // State 5: Default Mic
    else {
        iconMic.classList.remove('hidden');
        centralBtn.title = "Click to Speak";
    }
}

let pressTimer;
let isHolding = false;
let clickCount = 0;
let clickTimeout;

centralBtn.addEventListener('pointerdown', (e) => {
    e.preventDefault(); // Prevent double-firing on touch
    
    // State 1: Send Text (skip hold logic)
    if (textInput.value.trim() !== '') return;
    
    isHolding = false;
    
    // Only enable hold-to-interrupt if Christopher is active
    const isChristopherActive = (!audioPlayer.paused && audioPlayer.currentTime > 0 && !audioPlayer.ended) || 
                                (audioPlayer.paused && audioPlayer.currentTime > 0 && !audioPlayer.ended);
                                
    if (isChristopherActive) {
        pressTimer = setTimeout(() => {
            isHolding = true;
            if (!audioPlayer.paused) audioPlayer.pause();
            if (!isRecording) startRecording();
        }, 300); // 300ms defines a hold
    }
});

centralBtn.addEventListener('pointerup', (e) => {
    e.preventDefault();
    clearTimeout(pressTimer);
    
    // State 1: Send Text
    if (textInput.value.trim() !== '') {
        const topic = textInput.value.trim();
        generateContent(topic);
        return;
    }
    
    // State 2: Stop Hold-to-Talk Recording
    if (isHolding) {
        isHolding = false;
        if (isRecording) stopRecording();
        return;
    }
    
    // If we reach here, it was a click (not a hold)
    const isChristopherActive = (!audioPlayer.paused && audioPlayer.currentTime > 0 && !audioPlayer.ended) || 
                                (audioPlayer.paused && audioPlayer.currentTime > 0 && !audioPlayer.ended);
                                
    if (isChristopherActive) {
        // Christopher is active: Handle Single/Double click
        clickCount++;
        if (clickCount === 1) {
            // Instant Pause on first click!
            if (!audioPlayer.paused) {
                audioPlayer.pause();
            }
            
            clickTimeout = setTimeout(() => {
                clickCount = 0; // Commit to single click
            }, 300); // 300ms window for double click
        } else if (clickCount === 2) {
            clearTimeout(clickTimeout);
            clickCount = 0;
            // Double Click -> Unpause
            if (audioPlayer.paused) {
                audioPlayer.play();
            }
        }
    } else {
        // Christopher is NOT active: Normal Click-to-Toggle
        if (isRecording) {
            stopRecording();
        } else {
            startRecording();
        }
    }
});

centralBtn.addEventListener('pointercancel', () => {
    clearTimeout(pressTimer);
    if (isHolding) {
        isHolding = false;
        if (isRecording) stopRecording();
    }
});

// Audio Player Event Listeners (Triggers State Machine)
audioPlayer.addEventListener('play', () => {
    updateCentralButton();
    centralBtn.classList.add('playing');
});
audioPlayer.addEventListener('pause', () => {
    updateCentralButton();
    centralBtn.classList.remove('playing');
});
audioPlayer.addEventListener('ended', () => {
    updateCentralButton();
    centralBtn.classList.remove('playing');
});

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

// GLOBAL AUDIO UNLOCK: Browsers strictly require a standard "click" or "touchstart" 
document.body.addEventListener('click', unlockAudio);
document.body.addEventListener('touchstart', unlockAudio);
