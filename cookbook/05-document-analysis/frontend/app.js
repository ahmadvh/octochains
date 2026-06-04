const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const leftPanel = document.getElementById('left-panel');
const rightPanel = document.getElementById('right-panel');
const controls = document.getElementById('controls');
const documentContent = document.getElementById('document-content');
const dispatchBtn = document.getElementById('dispatch-btn');
const feed = document.getElementById('feed');
const legendContainer = document.getElementById('agent-legend');
const tooltip = document.getElementById('insight-tooltip');

// --- State Management ---
let globalSentenceState = {}; 
let activeAgentFilters = {};
let tooltipTimeout;

const HOVER_DELAY_MS = 800; 
const CURSOR_OFFSET = 5;    

// --- Helper: Convert Hex to RGB ---
const hexToRgb = (hex) => {
    let r = parseInt(hex.slice(1, 3), 16),
        g = parseInt(hex.slice(3, 5), 16),
        b = parseInt(hex.slice(5, 7), 16);
    return `${r}, ${g}, ${b}`;
};

// --- Drag and Drop Logic ---
dropZone.addEventListener('click', () => fileInput.click());
dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('dragover'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    if (e.dataTransfer.files.length) handleFileUpload(e.dataTransfer.files[0]);
});
fileInput.addEventListener('change', (e) => {
    if (e.target.files.length) handleFileUpload(e.target.files[0]);
});

// --- API: Upload & Parse ---
async function handleFileUpload(file) {
    dropZone.innerHTML = "<p class='drop-subtitle'>Uploading and parsing document...</p>";
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('http://localhost:8000/api/upload', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        
        if (data.status === 'success') {
            dropZone.style.display = 'none';
            leftPanel.classList.add('active');
            rightPanel.classList.add('active');
            controls.style.display = 'block';

            documentContent.innerHTML = data.sentences.map(para => {
                const paraText = para.sentences.map(s => 
                    `<span class="document-sentence" id="sent-${s.sentence_id}">${s.sentence} </span>`
                ).join('');
                return `<p>${paraText}</p>`;
            }).join('');
        }
    } catch (error) {
        dropZone.innerHTML = `<p style="color: red;">Upload failed. Ensure backend is running.</p>`;
        console.error(error);
    }
}

// --- API: Trigger Multi-Agent Analysis via SSE ---
dispatchBtn.addEventListener('click', () => {
    dispatchBtn.disabled = true;
    dispatchBtn.innerText = "Analyzing concurrently...";
    feed.innerHTML = ''; 
    
    legendContainer.style.display = 'none';
    legendContainer.innerHTML = '<div style="font-weight: 600; margin-bottom: 4px;">Active Perspectives</div>';
    
    globalSentenceState = {};
    activeAgentFilters = {};

    const eventSource = new EventSource('http://localhost:8000/api/analyze');

    eventSource.onmessage = (event) => {
        const payload = JSON.parse(event.data);

        if (payload.status === 'engine_started' || payload.status === 'aggregator_started') {
            addFeedStatus(payload.message);
        } 
        else if (payload.status === 'agent_report') {
            const agentData = payload.data;
            addAgentCard(agentData);
            registerAgentInLegend(agentData.agent, agentData.color);
            processAgentHighlights(agentData.agent, agentData.color, agentData.insight, agentData.selected_sentence_ids);
        }
        else if (payload.status === 'conflict_report') {
            addConflictReport(payload.data);
        }
        else if (payload.status === 'complete') {
            eventSource.close();
            dispatchBtn.innerText = "Audit Complete";
            addFeedStatus("Workflow Terminated Successfully.");
            legendContainer.style.display = 'flex';
        }
    };

    eventSource.onerror = (error) => {
        console.error("SSE Error:", error);
        eventSource.close();
        dispatchBtn.innerText = "Dispatch Parallel Agents";
        dispatchBtn.disabled = false;
    };
});

// --- UI Rendering Helpers ---
function addFeedStatus(message) {
    const el = document.createElement('div');
    el.className = 'status-text';
    el.innerText = `> ${message}`;
    feed.appendChild(el);
    rightPanel.scrollTop = rightPanel.scrollHeight;
}

function addAgentCard(data) {
    const el = document.createElement('div');
    el.className = 'card agent-card';
    el.style.borderLeftColor = data.color;
    el.innerHTML = `
        <div class="card-title" style="color: ${data.color}; filter: brightness(0.7);">${data.agent}</div>
        <p style="font-size: 0.95rem;">${data.insight}</p>
    `;
    feed.appendChild(el);
    rightPanel.scrollTop = rightPanel.scrollHeight;
}

function addConflictReport(consensus) {
    const el = document.createElement('div');
    el.className = 'card conflict-card';
    let html = `<div class="card-title" style="color: #d93025;">Chief Justice Report</div>`;
    
    if (consensus.has_conflicts && consensus.conflicts) {
        html += `<p style="font-weight: 600; margin-bottom: 8px;">${consensus.summary}</p>`;
        consensus.conflicts.forEach(c => {
            html += `
                <div style="background: rgba(255,255,255,0.7); padding: 8px; border-radius: 4px; margin-top: 8px; border-left: 2px solid #d93025;">
                    <strong>[${c.severity}]</strong> ${c.description} <br>
                    <small style="color: var(--text-secondary)">Involved: ${c.involved_agents.join(', ')}</small>
                </div>
            `;
        });
    } else {
         html += `<p>All executive perspectives are aligned. No critical cross-domain conflicts detected.</p>`;
    }
    
    el.innerHTML = html;
    feed.appendChild(el);
    rightPanel.scrollTop = rightPanel.scrollHeight;
}

// --- Dynamic Highlighting & Legend Logic ---
function registerAgentInLegend(agentName, color) {
    if (activeAgentFilters[agentName] !== undefined) return;

    activeAgentFilters[agentName] = true;

    const label = document.createElement('label');
    label.className = 'legend-item';
    label.innerHTML = `
        <input type="checkbox" checked value="${agentName}">
        <span class="legend-color-box" style="background-color: ${color};"></span>
        ${agentName}
    `;

    label.querySelector('input').addEventListener('change', (e) => {
        activeAgentFilters[agentName] = e.target.checked;
        recalculateAllHighlights();
    });

    legendContainer.appendChild(label);
}

function processAgentHighlights(agentName, color, insight, sentenceIds) {
    if (!sentenceIds) return;

    sentenceIds.forEach(id => {
        if (!globalSentenceState[id]) globalSentenceState[id] = {};
        globalSentenceState[id][agentName] = { color, insight };
    });

    recalculateAllHighlights();
}

function recalculateAllHighlights() {
    for (const [sentenceId, agentsDict] of Object.entries(globalSentenceState)) {
        const sentenceEl = document.getElementById(`sent-${sentenceId}`);
        if (!sentenceEl) continue;

        const activeColors = [];
        for (const [agentName, data] of Object.entries(agentsDict)) {
            if (activeAgentFilters[agentName]) {
                activeColors.push(data.color);
            }
        }

        if (activeColors.length === 0) {
            sentenceEl.style.background = 'transparent';
            sentenceEl.style.borderBottomColor = 'transparent';
            sentenceEl.classList.remove('has-highlight'); 
        } 
        else if (activeColors.length === 1) {
            sentenceEl.classList.add('has-highlight'); 
            const color = activeColors[0];
            sentenceEl.style.background = `rgba(${hexToRgb(color)}, 0.3)`;
            sentenceEl.style.borderBottomColor = color;
        } 
        else {
            sentenceEl.classList.add('has-highlight'); 
            const stripeWidth = 10;
            let gradientStops = [];
            
            activeColors.forEach((color, index) => {
                const rgba = `rgba(${hexToRgb(color)}, 0.4)`;
                const start = index * stripeWidth;
                const end = (index + 1) * stripeWidth;
                gradientStops.push(`${rgba} ${start}px, ${rgba} ${end}px`);
            });

            const totalWidth = activeColors.length * stripeWidth;
            sentenceEl.style.background = `repeating-linear-gradient(45deg, ${gradientStops.join(', ')} 0, ${gradientStops.join(', ')} ${totalWidth}px)`;
            sentenceEl.style.borderBottomColor = '#444746'; 
        }
    }
}

// --- Tooltip Hover Logic (Delayed, Scrollable & Boundary-Aware) ---
documentContent.addEventListener('mouseover', (e) => {
    const sentenceEl = e.target.closest('.document-sentence');
    if (!sentenceEl) return;
    
    const sentenceId = sentenceEl.id.replace('sent-', '');
    const agentsDict = globalSentenceState[sentenceId];
    
    let activeAgentsHtml = '';
    
    if (agentsDict) {
        for (const [agentName, data] of Object.entries(agentsDict)) {
            if (activeAgentFilters[agentName]) {
                activeAgentsHtml += `
                    <div class="tooltip-agent-block">
                        <div class="tooltip-agent-name" style="color: ${data.color}; filter: brightness(0.7);">${agentName}</div>
                        <div class="tooltip-insight-text">${data.insight}</div>
                    </div>
                `;
            }
        }
    }

    if (activeAgentsHtml) {
        clearTimeout(tooltipTimeout);
        tooltip.innerHTML = activeAgentsHtml;
        
        tooltip.style.visibility = 'hidden'; 
        tooltip.style.opacity = '0';
        tooltip.classList.add('visible'); 
        
        const tooltipRect = tooltip.getBoundingClientRect();
        
        let leftPos = e.pageX + CURSOR_OFFSET;
        let topPos = e.pageY + CURSOR_OFFSET;

        if (e.clientX + CURSOR_OFFSET + tooltipRect.width > window.innerWidth) {
            leftPos = e.pageX - tooltipRect.width - CURSOR_OFFSET;
        }

        if (e.clientY + CURSOR_OFFSET + tooltipRect.height > window.innerHeight) {
            topPos = e.pageY - tooltipRect.height - CURSOR_OFFSET;
        }

        tooltip.style.left = `${leftPos}px`;
        tooltip.style.top = `${topPos}px`;
        tooltip.style.visibility = ''; 
        tooltip.style.opacity = '';
    }
});

documentContent.addEventListener('mouseout', (e) => {
    const sentenceEl = e.target.closest('.document-sentence');
    if (sentenceEl) {
        tooltipTimeout = setTimeout(() => {
            tooltip.classList.remove('visible');
        }, HOVER_DELAY_MS); 
    }
});

tooltip.addEventListener('mouseenter', () => {
    clearTimeout(tooltipTimeout);
});

tooltip.addEventListener('mouseleave', () => {
    tooltipTimeout = setTimeout(() => {
        tooltip.classList.remove('visible');
    }, HOVER_DELAY_MS); 
});