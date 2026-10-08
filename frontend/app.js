const API_BASE = "http://127.0.0.1:8000/api";
let currentRepoId = null;

const ingestSection = document.getElementById("ingest-section");
const querySection = document.getElementById("query-section");
const statusContainer = document.getElementById("status-container");
const statusText = document.getElementById("status-text");
const btnIngest = document.getElementById("btn-ingest");
const repoUrlInput = document.getElementById("repo-url");
const chatContainer = document.getElementById("chat-container");
const queryInput = document.getElementById("query-input");
const btnQuery = document.getElementById("btn-query");

btnIngest.addEventListener("click", async () => {
    const url = repoUrlInput.value.trim();
    if (!url) return;

    btnIngest.disabled = true;
    statusContainer.classList.remove("hidden");
    statusText.textContent = "Initiating ingestion pipeline...";

    try {
        const response = await fetch(`${API_BASE}/repos/ingest`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url })
        });

        if (!response.ok) {
            throw new Error(await response.text());
        }

        const data = await response.json();
        currentRepoId = data.repo_id;
        pollStatus();
    } catch (e) {
        statusText.textContent = `Error: ${e.message}`;
        btnIngest.disabled = false;
        document.querySelector(".spinner").style.display = "none";
    }
});

async function pollStatus() {
    try {
        const response = await fetch(`${API_BASE}/repos/${currentRepoId}/status`);
        const data = await response.json();

        if (data.status === "completed") {
            statusText.textContent = "Ingestion Complete! Vector Graph Ready.";
            document.querySelector(".spinner").style.display = "none";
            
            setTimeout(() => {
                ingestSection.classList.add("hidden");
                querySection.classList.remove("hidden");
                addMessage("system", "RepoSense engine connected. I've parsed the codebase into a Knowledge Graph and generated semantic embeddings. What would you like to know?");
            }, 1000);
        } else if (data.status === "failed") {
            statusText.textContent = "Ingestion failed.";
            btnIngest.disabled = false;
            document.querySelector(".spinner").style.display = "none";
        } else {
            statusText.textContent = "Parsing and embedding codebase... (This may take a minute)";
            setTimeout(pollStatus, 2000);
        }
    } catch (e) {
        statusText.textContent = `Error polling status: ${e.message}`;
        setTimeout(pollStatus, 2000);
    }
}

btnQuery.addEventListener("click", submitQuery);
queryInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") submitQuery();
});

async function submitQuery() {
    const query = queryInput.value.trim();
    if (!query) return;

    queryInput.value = "";
    btnQuery.disabled = true;
    
    addMessage("user", query);
    
    // Add loading message
    const loadingId = "msg-" + Date.now();
    addMessage("system", "<div class='spinner' style='width:16px;height:16px;border-width:2px;display:inline-block;vertical-align:middle;margin-right:10px;'></div> Searching Vector Graph...", loadingId);

    try {
        const response = await fetch(`${API_BASE}/query`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ repo_id: currentRepoId, query })
        });

        const data = await response.json();
        
        // Remove loading message
        document.getElementById(loadingId).remove();
        
        let html = `<p>${data.answer}</p>`;
        
        if (data.sources && data.sources.length > 0) {
            html += `<div style="margin-top: 1rem;">`;
            data.sources.forEach(src => {
                html += `<span class="source-badge">${src.name} (${src.file}:${src.lines})</span>`;
            });
            html += `</div>`;
        }
        
        html += `<details style="margin-top: 1rem; cursor: pointer;">
                    <summary style="font-size: 0.85rem; color: var(--text-secondary);">View Context Prompt Sent to LLM</summary>
                    <div class="prompt-details">${data.prompt}</div>
                 </details>`;
                 
        addMessage("system", html);
    } catch (e) {
        document.getElementById(loadingId).remove();
        addMessage("system", `<span style="color: #ef4444;">Query failed: ${e.message}</span>`);
    } finally {
        btnQuery.disabled = false;
        queryInput.focus();
    }
}

function addMessage(sender, htmlContent, id = null) {
    const div = document.createElement("div");
    div.className = `message ${sender}`;
    if (id) div.id = id;
    div.innerHTML = htmlContent;
    chatContainer.appendChild(div);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}
