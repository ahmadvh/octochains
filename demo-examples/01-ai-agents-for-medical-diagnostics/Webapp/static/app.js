const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('file-input');
const chatContainer = document.getElementById('chat-container');
const chatInput = document.getElementById('chat-input');
const chatBtn = document.getElementById('chat-btn');
const logCont = document.getElementById('log-container');

let session = "";

// --- 1. BOOTH SHORTCUTS ---
window.addEventListener('keydown', e => {
    if (e.key === 'Escape') {
        // Instant reload to reset the demo for the next person at the booth
        location.reload();
    }
});

// --- 2. CHAT BUBBLE SYSTEM ---
function addBubble(text, type = "system") {
    const b = document.createElement('div');
    b.className = `bubble ${type}`;
    
    // 1. Clean up markdown-style bolding
    let formattedText = text.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>');
    
    // 2. Clean up markdown-style italics
    formattedText = formattedText.replace(/\*(.*?)\*/g, '<i>$1</i>');
    
    // 3. Convert explicit newlines (\n) to HTML line breaks (<br>)
    formattedText = formattedText.replace(/\n/g, '<br>');
    
    b.innerHTML = formattedText;
    
    chatContainer.appendChild(b);
    
    // Auto-scroll to bottom
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// --- 3. UI HELPERS ---
function setProcessing(selector, isActive) {
    const elements = document.querySelectorAll(selector);
    elements.forEach(el => {
        isActive ? el.classList.add('processing') : el.classList.remove('processing');
    });
}

// --- 4. DRAG & DROP LOGIC ---
dropzone.addEventListener('click', () => fileInput.click());
dropzone.addEventListener('dragover', e => { 
    e.preventDefault(); 
    dropzone.classList.add('dragover'); 
});
dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));
dropzone.addEventListener('drop', e => { 
    e.preventDefault(); 
    if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]); 
});
fileInput.addEventListener('change', e => { 
    if (e.target.files.length) handleFile(e.target.files[0]); 
});

// --- 5. CORE ANALYSIS WORKFLOW ---
async function handleFile(file) {
    // A. Visual Cue: Stop the pulse on the 'Start Here' node
    document.getElementById('n-doc').classList.remove('pulse');
    
    // B. Clear the right panel to focus on the SVG animation
    dropzone.style.display = 'none';

    // C. Professional Pause (1.5s) to draw attention to the chart
    setTimeout(async () => {
        
        // Prepare the tray in the background (hidden by CSS transform)
        logCont.style.display = 'flex'; 
        addBubble(`Loaded: ${file.name}`, "system");

        // PHASE 1: Data Broadcast (Report -> Agents)
        document.querySelectorAll('.phase1').forEach(el => el.classList.add('active')); 
        document.querySelectorAll('.phase1 animateMotion').forEach(anim => anim.beginElement()); 

        setTimeout(() => {
            document.querySelectorAll('.phase1').forEach(el => el.classList.remove('active'));
            setProcessing('.agent', true); 
            document.getElementById('working-text').classList.add('active');
            addBubble("Consulting specialized medical agents...", "system");
        }, 2000);

        // API Call
        const fd = new FormData(); 
        fd.append("file", file);
        
        try {
            const res = await fetch('/analyze', { method: 'POST', body: fd });
            const data = await res.json();
            session = data.session_id;

            // Stop agent processing
            setProcessing('.agent', false); 
            document.getElementById('working-text').classList.remove('active');
            
            // PHASE 2: Consolidation (Agents -> Team)
            document.querySelectorAll('.phase2').forEach(el => el.classList.add('active')); 
            document.querySelectorAll('.phase2 animateMotion').forEach(anim => anim.beginElement()); 
            setProcessing('#n-llm', true);

            // D. THE BIG REVEAL (Wait for dots to hit the center)
            setTimeout(() => {
                // Stop center node processing
                setProcessing('#n-llm', false); 
                document.querySelectorAll('.phase2').forEach(el => el.classList.remove('active'));
                
                // Light up the final node
                document.getElementById('n-final').style.opacity = '1';

                // delay for 2.3 seconds
                setTimeout(() => {
                }, 2300);

                // Slide in the professional Chat Panel
                logCont.classList.add('active'); 
                
                // Post the consensus in a nice bubble
                addBubble("CONSENSUS REPORT", "system");
                addBubble(data.consensus, "team");

            }, 2000);

        } catch (e) { 
            addBubble("Connection error. Please try again.", "system"); 
            console.error(e);
        }
    }, 2000);
}

// --- 6. CHAT INTERACTION ---
async function sendMessage() {
    const msg = chatInput.value.trim(); 
    if (!msg) return;
    
    addBubble(msg, "user"); 
    chatInput.value = ""; 
    
    // Fake "Thinking" state
    const thinkingId = Date.now();
    addBubble("Team is typing...", `system thinking-${thinkingId}`);
    
    try {
        const res = await fetch('/chat', { 
            method: 'POST', 
            body: new URLSearchParams({ session_id: session, message: msg }) 
        });
        const data = await res.json();
        
        // Remove thinking message and add reply
        document.querySelector(`.thinking-${thinkingId}`).remove();
        addBubble(data.reply, "team");
    } catch (e) {
        addBubble("The team is currently unavailable.", "system");
    }
}

chatBtn.addEventListener('click', sendMessage);
chatInput.addEventListener('keypress', e => { 
    if (e.key === 'Enter') sendMessage(); 
});