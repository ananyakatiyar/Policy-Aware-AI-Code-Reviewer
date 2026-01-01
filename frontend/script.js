document.addEventListener('DOMContentLoaded', () => {
    // Auth Check
    const token = localStorage.getItem('token');
    const userSection = document.getElementById('userSection');
    const userAvatar = document.getElementById('userAvatar');
    const logoutBtn = document.getElementById('logoutBtn');
    
    if (!token) {
        window.location.href = '/login.html';
        return;
    } else {
        // Simple JWT decode to get user email (production should verify with /auth/me)
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            userAvatar.textContent = payload.sub.charAt(0).toUpperCase();
            userSection.style.display = 'flex';
        } catch (e) {
            console.error('Invalid token', e);
            localStorage.removeItem('token');
            window.location.href = '/login.html';
        }
    }

    logoutBtn.addEventListener('click', () => {
        localStorage.removeItem('token');
        window.location.href = '/login.html';
    });

    const runBtn = document.getElementById('runReviewBtn');
    const codeInput = document.getElementById('codeInput');
    const resultsSection = document.getElementById('resultsSection');
    const errorPanel = document.getElementById('errorPanel');
    const errorTitle = document.getElementById('errorTitle');
    const errorMessage = document.getElementById('errorMessage');
    const errorActions = document.getElementById('errorActions');
    const activePolicyCount = document.getElementById('activePolicyCount');
    const checkboxes = document.querySelectorAll('input[type="checkbox"]');
    const exportBtn = document.getElementById('exportBtn');
    let lastReviewData = null;
    let lastWasDiff = false;
    let lastOriginalCode = '';
    let lastModifiedCode = '';
    
    // Diff Mode Elements
    const diffToggle = document.getElementById('diffModeToggle');
    const originalCodeSection = document.getElementById('originalCodeSection');
    const originalCodeInput = document.getElementById('originalCodeInput');

    diffToggle.addEventListener('change', () => {
        if (diffToggle.checked) {
            originalCodeSection.style.display = 'block';
            originalCodeSection.classList.remove('hidden');
        } else {
            originalCodeSection.style.display = 'none';
            originalCodeSection.classList.add('hidden');
        }
    });

    exportBtn.addEventListener('click', async () => {
        if (!lastReviewData) {
            alert('No review data to export. Run a review first!');
            return;
        }

        exportBtn.textContent = 'Generating PDF...';
        exportBtn.disabled = true;

        try {
            const response = await fetch('/export/pdf', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(lastReviewData)
            });

            if (!response.ok) throw new Error('Export failed');

            // Handle Blob for download
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `audit_report_${new Date().toISOString().slice(0,10)}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

        } catch (error) {
            console.error(error);
            alert('Failed to generate PDF report.');
        } finally {
            exportBtn.textContent = 'Export PDF';
            exportBtn.disabled = false;
        }
    });

    // Update active policy count
    checkboxes.forEach(cb => {
        cb.addEventListener('change', () => {
            const count = document.querySelectorAll('input[type="checkbox"]:checked').length;
            activePolicyCount.textContent = count;
        });
    });

    runBtn.addEventListener('click', async () => {
        const code = codeInput.value;
        const policies = Array.from(checkboxes)
            .filter(cb => cb.checked)
            .map(cb => cb.dataset.policy);

        // UI Loading State
        setLoading(true);
        resultsSection.classList.add('hidden');

        try {
            // Prepare request
            let url = '/review';
            let body = { code, policies };

            if (diffToggle.checked) {
                url = '/review/diff';
                body = {
                    original_code: originalCodeInput.value,
                    modified_code: code,
                    policies: policies
                };
                lastWasDiff = true;
                lastOriginalCode = originalCodeInput.value;
                lastModifiedCode = code;
            }

            // Attempt to call backend
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(body)
            });

            // Handle 401 Unauthorized explicitly
            if (response.status === 401) {
                // Show error panel with login guidance and stop fallback
                showError('Unauthorized', 'Your session is not authorized. Please log in or start the server with DISABLE_AUTH=1 for local testing.');
                return;
            }

            if (!response.ok) {
                // Try to read JSON body for detailed error info (validation errors from FastAPI)
                let bodyText = '';
                try {
                    const ct = response.headers.get('content-type') || '';
                    if (ct.includes('application/json')) {
                        const j = await response.json();
                        // FastAPI returns {detail: [...] } for validation errors
                        if (j.detail) {
                            if (Array.isArray(j.detail)) {
                                bodyText = j.detail.map(d => d.msg ? `${d.loc.join('.')}: ${d.msg}` : JSON.stringify(d)).join('\n');
                            } else if (typeof j.detail === 'string') {
                                bodyText = j.detail;
                            } else {
                                bodyText = JSON.stringify(j.detail);
                            }
                        } else {
                            bodyText = JSON.stringify(j);
                        }
                    } else {
                        bodyText = await response.text();
                    }
                } catch (e) {
                    bodyText = `Status ${response.status}`;
                }

                // Show detailed message and stop for 422; otherwise continue to use fallback
                if (response.status === 422) {
                    showError('Validation Error', `Request body invalid:\n${bodyText}`.replace(/\n/g, '<br/>'));
                    return;
                }

                showError('Server Error', `Backend returned status ${response.status}. ${bodyText}`);
                // Let fallback proceed below
            } else {
                const data = await response.json();
                lastReviewData = data;
                hideError();
                renderResults(data);
                if (lastWasDiff) renderDiffPreview(lastOriginalCode, lastModifiedCode, data.violations || []);
                return;
            }

        } catch (error) {
            console.warn('Backend failed, using mock data fallback', error);
            showError('Network Error', 'Could not reach backend. Using local fallback.');
            // Fallback to Mock Data (Part 3 Requirement)
            await new Promise(r => setTimeout(r, 1500)); // Simulate delay
            const mock = getMockData();
            renderResults(mock);
            if (lastWasDiff) renderDiffPreview(lastOriginalCode, lastModifiedCode, mock.violations || []);
        } finally {
            setLoading(false);
            resultsSection.classList.remove('hidden');
            // Scroll to results
            resultsSection.scrollIntoView({ behavior: 'smooth' });
        }
    });

    function renderDiffPreview(original, modified, violations) {
        const panel = document.getElementById('diffPreviewSection');
        const origEl = document.getElementById('diffOriginal');
        const modEl = document.getElementById('diffModified');
        const fileNameEl = document.getElementById('diffFileName');
        if (!panel || !origEl || !modEl) return;

        // Populate original
        origEl.textContent = original || '';

        // Highlight modified lines that correspond to violations
        const modLines = (modified || '').split('\n');
        const violationLines = new Set((violations || []).map(v => Number(v.line)));

        // Build HTML with line numbers and highlights
        const html = modLines.map((ln, idx) => {
            const lineNo = idx + 1;
            const safe = escapeHtml(ln);
            if (violationLines.has(lineNo)) {
                return `<div style="background: rgba(255,51,51,0.08); padding:2px 6px;"><span style="opacity:0.6; font-size:0.9em; margin-right:8px;">${lineNo}</span><code>${safe}</code></div>`;
            }
            return `<div><span style="opacity:0.6; font-size:0.9em; margin-right:8px;">${lineNo}</span><code>${safe}</code></div>`;
        }).join('');

        modEl.innerHTML = html;
        fileNameEl.textContent = 'diff_preview.py';
        panel.style.display = 'block';
        panel.classList.remove('hidden');
        // Scroll to diff preview
        panel.scrollIntoView({ behavior: 'smooth' });
    }

    function showError(title, message, actionsHtml) {
        if (!errorPanel) return;
        errorTitle.textContent = title || 'Error';
        errorMessage.textContent = message || '';
        errorActions.innerHTML = actionsHtml || '<button class="primary-btn" onclick="window.location.href=\'/login.html\'">Go to Login</button>';
        errorPanel.style.display = 'block';
        errorPanel.classList.remove('hidden');
        // hide results when error is critical (e.g., 401)
        resultsSection.classList.add('hidden');
    }

    function hideError() {
        if (!errorPanel) return;
        errorPanel.style.display = 'none';
        errorPanel.classList.add('hidden');
        errorActions.innerHTML = '';
    }

    function setLoading(isLoading) {
        if (isLoading) {
            runBtn.disabled = true;
            runBtn.innerHTML = '<span class="loader"></span> Analyzing...';
        } else {
            runBtn.disabled = false;
            runBtn.innerHTML = '<span class="btn-icon">▶</span> Run AI Review <span class="sparkle-icon">✨</span>';
        }
    }

    function renderResults(data) {
        // Update Risk Score
        const scoreEl = document.getElementById('riskScore');
        const scoreDisplay = document.getElementById('riskScoreDisplay');
        const levelEl = document.getElementById('riskLevel');
        const ringEl = document.querySelector('.score-ring');
        
        scoreEl.textContent = data.risk_score;
        
        // Risk Delta
        if (data.risk_delta !== undefined && data.risk_delta !== 0) {
             const deltaEl = document.createElement('span');
             deltaEl.style.fontSize = '0.5em';
             deltaEl.style.marginLeft = '8px';
             deltaEl.style.fontWeight = 'bold';
             if (data.risk_delta > 0) {
                 deltaEl.textContent = `(+${data.risk_delta})`;
                 deltaEl.style.color = '#00ff9d';
             } else {
                 deltaEl.textContent = `(${data.risk_delta})`;
                 deltaEl.style.color = '#ff3333';
             }
             scoreEl.appendChild(deltaEl);
        }

        scoreDisplay.textContent = data.risk_score;
        levelEl.textContent = data.risk_level; // HIGH, MEDIUM, LOW

        // Color coding
        let color = '#00ff9d'; // Low
        if (data.risk_score > 40) color = '#ffb800'; // Medium
        if (data.risk_score > 70) color = '#ff3333'; // High
        
        ringEl.style.borderTopColor = color;
        ringEl.style.boxShadow = `0 0 30px ${color}33`; // 33 is alpha
        levelEl.style.color = color;
        scoreEl.style.color = color;

        // Update Summary
        document.getElementById('timestamp').textContent = data.audit.timestamp;
        
        if (data.audit.diff_metadata) {
             const dm = data.audit.diff_metadata;
             document.getElementById('violationCount').innerHTML = 
                `${data.violations.length} <span style="font-size:0.8em; color:#888;">(+${dm.lines_added} lines)</span>`;
        } else {
             document.getElementById('violationCount').textContent = data.violations.length;
        }

        // Render Violations
        const list = document.getElementById('violationsList');
        list.innerHTML = '';

        if (data.violations.length === 0) {
            list.innerHTML = '<div class="violation-card low"><div class="v-header"><div class="v-title">No issues found! Great job.</div></div></div>';
            return;
        }

        data.violations.forEach(v => {
            const card = document.createElement('div');
            card.className = `violation-card ${v.severity.toLowerCase()}`;
            if (v.status === 'FALSE_POSITIVE') {
                 card.style.opacity = '0.6';
                 card.style.textDecoration = 'line-through';
            }
            
            card.innerHTML = `
                <div class="v-header">
                    <div class="v-left">
                        <span class="icon">
                            ${v.severity === 'HIGH' ? '🔴' : v.severity === 'MEDIUM' ? '⚠️' : 'ℹ️'}
                        </span>
                        <span class="line-badge">Line ${v.line}</span>
                        <span class="badge ${v.severity.toLowerCase()}">${v.severity}</span>
                        <span class="v-title">${v.message}</span>
                        ${v.status === 'FALSE_POSITIVE' ? '<span class="badge" style="background:#666; margin-left:8px;">FALSE POSITIVE</span>' : ''}
                    </div>
                    <div class="v-right">
                        <div class="feedback-actions" style="display:flex; gap:8px; margin-right:12px;">
                            <button class="icon-btn valid-btn" title="Mark as Valid" onclick="submitFeedback('${v.id}', '${v.rule_id}', 'VALID', this)" style="background:none; border:none; cursor:pointer; font-size:1.2rem;">✅</button>
                            <button class="icon-btn fp-btn" title="Mark as False Positive" onclick="submitFeedback('${v.id}', '${v.rule_id}', 'FALSE_POSITIVE', this)" style="background:none; border:none; cursor:pointer; font-size:1.2rem;">🚫</button>
                        </div>
                        <button class="fix-btn" onclick="toggleRemediation(this)">Explain & Fix ✨</button>
                    </div>
                </div>
                <div class="remediation-container" style="display:none;">
                    <div class="remediation-panel">
                        <div class="rem-header"><span>🧠 AI Analysis</span></div>
                        
                        <div class="xai-section" style="margin-bottom: 12px;">
                            <strong style="color: var(--warning);">Why is this risky?</strong>
                            <p class="rem-desc">${v.risk_explanation || 'No explanation available.'}</p>
                        </div>
                        
                        <div class="xai-section" style="margin-bottom: 12px;">
                            <strong style="color: var(--danger);">Exploit Scenario:</strong>
                            <p class="rem-desc">${v.exploit_scenario || 'No scenario available.'}</p>
                        </div>

                        <div class="xai-section" style="margin-bottom: 12px;">
                            <strong style="color: var(--success);">How to fix:</strong>
                            <p class="rem-desc">${v.fix_recommendation || 'No fix recommendation.'}</p>
                        </div>

                        ${v.secure_code_example ? `
                        <div class="xai-section">
                            <strong style="color: var(--primary-cyan);">Secure Example:</strong>
                            <div class="code-block">${escapeHtml(v.secure_code_example)}</div>
                        </div>` : ''}
                    </div>
                </div>
            `;
            list.appendChild(card);
        });
    }

    window.submitFeedback = async (violationId, ruleId, type, btn) => {
        const card = btn.closest('.violation-card');
        const token = localStorage.getItem('token');
        
        // Optimistic UI update
        const originalOpacity = card.style.opacity;
        card.style.opacity = '0.5';
        
        try {
            const response = await fetch('/feedback', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    violation_id: violationId,
                    policy_rule_id: ruleId,
                    feedback_type: type
                })
            });
            
            if (response.ok) {
                 if (type === 'FALSE_POSITIVE') {
                     card.style.textDecoration = 'line-through';
                     // Add badge if not present
                     const title = card.querySelector('.v-title');
                     if (!card.querySelector('.badge[style*="background:#666"]')) {
                         const badge = document.createElement('span');
                         badge.className = 'badge';
                         badge.style.background = '#666';
                         badge.style.marginLeft = '8px';
                         badge.textContent = 'FALSE POSITIVE';
                         title.parentElement.appendChild(badge);
                     }
                 } else {
                     // VALID
                     card.style.textDecoration = 'none';
                     card.style.opacity = '1';
                     const badge = card.querySelector('.badge[style*="background:#666"]');
                     if (badge) badge.remove();
                 }
                 // Trigger re-run to update score
                 document.getElementById('runReviewBtn').click();
            } else {
                card.style.opacity = originalOpacity;
                alert('Failed to submit feedback');
            }
        } catch (e) {
            console.error(e);
            card.style.opacity = originalOpacity;
        }
    };

    // Expose to window for onclick handler
    window.toggleRemediation = (btnElement) => {
        const container = btnElement.closest('.violation-card').querySelector('.remediation-container');
        
        if (container.style.display === 'none') {
            container.style.display = 'block';
            container.style.animation = 'slideDown 0.3s ease-out';
            btnElement.textContent = 'Hide Details';
        } else {
            container.style.display = 'none';
            btnElement.textContent = 'Explain & Fix ✨';
        }
    };

    function escapeHtml(text) {
        return text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function getMockData() {
        return {
            risk_score: 85,
            risk_level: "High Risk",
            audit: {
                timestamp: new Date().toLocaleString(),
                file: "untitled.py"
            },
            violations: [
                { line: 4, severity: "HIGH", message: "Hardcoded secret detected", rule_id: "no_secrets" },
                { line: 9, severity: "MEDIUM", message: "Deeply nested loops detected", rule_id: "nested_loops" },
                { line: 14, severity: "MEDIUM", message: "Potentially blocking operation", rule_id: "blocking_calls" },
                { line: 20, severity: "LOW", message: "Missing error logging", rule_id: "enforce_logging" }
            ]
        };
    }
});
