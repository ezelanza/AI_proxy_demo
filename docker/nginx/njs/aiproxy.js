// AI Proxy NJS Script
// Handles model routing and body rewriting based on supervisor headers.

function extractMessageText(message) {
    if (!message) return "";
    if (typeof message.content === 'string') return message.content;
    if (Array.isArray(message.content)) {
        return message.content.filter(p => p.type === 'text').map(p => p.text).join(' ');
    }
    return "";
}

function load_rbac(r) { return ""; }

// Function used in js_set to rewrite body
function rewriteBody(r) {
    try {
        var bodyStr = r.requestBody;
        if (!bodyStr && r.variables) {
             bodyStr = r.variables.request_body;
        }

        if (!bodyStr) {
            return ""; 
        }

        var requestBody = JSON.parse(bodyStr);
        var requestedModel = requestBody.model; 

        // Detect Complexity from Message History (The "Easy Way")
        var complexityMarker = "none";
        if (requestBody.messages && Array.isArray(requestBody.messages)) {
            // Iterate backwards to find the most recent complexity tag
            for (var i = requestBody.messages.length - 1; i >= 0; i--) {
                var content = extractMessageText(requestBody.messages[i]);
                
                if (content.indexOf("[COMPLEXITY:C]") !== -1) {
                    complexityMarker = "C";
                    break;
                }
                if (content.indexOf("[COMPLEXITY:S]") !== -1) {
                    complexityMarker = "S";
                    break;
                }
            }
        }

        // Determine Target Model
        var targetModel = "gpt-4o-mini"; // Default cheap

        if (complexityMarker === 'C') {
            targetModel = "gpt-4o"; 
        } else if (complexityMarker === 'S') {
            targetModel = "gpt-4o-mini";
        }

        // Rewrite Model: Check for "LLM_MODEL" or "LLM_model"
        if (requestedModel && (requestedModel.indexOf("LLM_MODEL") !== -1 || requestedModel.indexOf("LLM_model") !== -1)) {
            requestBody.model = targetModel;
            r.log(`[AI Proxy] REWRITE: ${requestedModel} -> ${targetModel} (Detected: ${complexityMarker})`);
        } else {
             r.log(`[AI Proxy] PASS-THROUGH: ${requestedModel}`);
        }

        return JSON.stringify(requestBody);

    } catch (e) {
        r.error("[AI Proxy] Body Rewrite Error: " + e.message);
        return r.requestBody; // Fallback to original
    }
}

export default { rewriteBody, load_rbac };
