// Chart instances
let dataDistributionChart = null;
let riskBreakdownChart = null;

// Image Redaction Variables
let currentTool = 'blur';
let isDrawing = false;
let startX = 0;
let startY = 0;
let currentX = 0;
let currentY = 0;
let redactionCanvas = null;
let redactionCtx = null;
let originalImage = null;
let blurStrength = 15;
let redactionRectangles = [];

// Privacy score history management
function getScoreHistory() {
    const history = localStorage.getItem('privacyScoreHistory');
    return history ? JSON.parse(history) : [];
}

function saveScoreToHistory(score) {
    const history = getScoreHistory();
    history.push({
        score: score,
        timestamp: new Date().toLocaleDateString()
    });
    // Keep only last 6 scores
    if (history.length > 6) history.shift();
    localStorage.setItem('privacyScoreHistory', JSON.stringify(history));
    return history;
}

function displayScoreHistory() {
    const history = getScoreHistory();
    const chart = document.getElementById('historyChart');
    chart.innerHTML = '';

    if (history.length === 0) {
        chart.innerHTML = '<p>No history yet. Analyze more images to track your progress!</p>';
        return;
    }

    history.forEach(item => {
        const bar = document.createElement('div');
        bar.className = 'history-bar';
        bar.style.height = `${item.score}%`;
        bar.title = `Score: ${item.score} - ${item.timestamp}`;
        chart.appendChild(bar);
    });
}

// Image Redaction Functions
function initializeRedactionTool(imageFile) {
    redactionCanvas = document.getElementById('redactionCanvas');
    redactionCtx = redactionCanvas.getContext('2d');
    redactionRectangles = [];
    
    const img = new Image();
    img.onload = function() {
        originalImage = img;
        
        // Set canvas size to match image
        const maxWidth = 800;
        const scale = Math.min(maxWidth / img.width, 1);
        redactionCanvas.width = img.width * scale;
        redactionCanvas.height = img.height * scale;
        
        // Draw original image
        redactionCtx.drawImage(img, 0, 0, redactionCanvas.width, redactionCanvas.height);
        
        // Add event listeners for drawing
        setupCanvasEvents();
    };
    img.src = URL.createObjectURL(imageFile);
}

function setupCanvasEvents() {
    redactionCanvas.addEventListener('mousedown', startDrawing);
    redactionCanvas.addEventListener('mousemove', draw);
    redactionCanvas.addEventListener('mouseup', stopDrawing);
    redactionCanvas.addEventListener('mouseout', stopDrawing);
    
    // Touch events for mobile
    redactionCanvas.addEventListener('touchstart', handleTouchStart);
    redactionCanvas.addEventListener('touchmove', handleTouchMove);
    redactionCanvas.addEventListener('touchend', stopDrawing);
}

function handleTouchStart(e) {
    e.preventDefault();
    const touch = e.touches[0];
    const rect = redactionCanvas.getBoundingClientRect();
    startX = touch.clientX - rect.left;
    startY = touch.clientY - rect.top;
    isDrawing = true;
}

function handleTouchMove(e) {
    if (!isDrawing) return;
    e.preventDefault();
    const touch = e.touches[0];
    const rect = redactionCanvas.getBoundingClientRect();
    currentX = touch.clientX - rect.left;
    currentY = touch.clientY - rect.top;
    drawPreview();
}

function startDrawing(e) {
    isDrawing = true;
    const rect = redactionCanvas.getBoundingClientRect();
    startX = e.clientX - rect.left;
    startY = e.clientY - rect.top;
    currentX = startX;
    currentY = startY;
}

function draw(e) {
    if (!isDrawing) return;
    
    const rect = redactionCanvas.getBoundingClientRect();
    currentX = e.clientX - rect.left;
    currentY = e.clientY - rect.top;
    
    drawPreview();
}

function drawPreview() {
    // Redraw the original image with all existing redactions
    redrawCanvas();
    
    // Draw the current preview rectangle
    redactionCtx.strokeStyle = '#ff0000';
    redactionCtx.lineWidth = 2;
    redactionCtx.setLineDash([5, 5]);
    redactionCtx.strokeRect(startX, startY, currentX - startX, currentY - startY);
    redactionCtx.setLineDash([]);
    
    // Fill based on tool type
    if (currentTool === 'blackout') {
        redactionCtx.fillStyle = 'rgba(0, 0, 0, 0.7)';
        redactionCtx.fillRect(startX, startY, currentX - startX, currentY - startY);
    } else if (currentTool === 'opaque-blur') {
        redactionCtx.fillStyle = 'rgba(255, 255, 255, 0.3)';
        redactionCtx.fillRect(startX, startY, currentX - startX, currentY - startY);
    }
}

function stopDrawing() {
    if (!isDrawing) return;
    isDrawing = false;
    
    // Calculate the final rectangle
    const width = currentX - startX;
    const height = currentY - startY;
    
    // Only add if rectangle is large enough
    if (Math.abs(width) > 10 && Math.abs(height) > 10) {
        // Normalize coordinates (allow dragging in any direction)
        const x = Math.min(startX, currentX);
        const y = Math.min(startY, currentY);
        const w = Math.abs(width);
        const h = Math.abs(height);
        
        // Add to redactions list
        redactionRectangles.push({
            x: x,
            y: y,
            width: w,
            height: h,
            type: currentTool,
            blurStrength: blurStrength
        });
        
        // Apply the redaction
        applyRedaction(redactionRectangles[redactionRectangles.length - 1]);
    }
    
    // Redraw to remove preview
    redrawCanvas();
}

function applyRedaction(rect) {
    if (rect.type === 'blackout') {
        // Blackout - simple rectangle
        redactionCtx.fillStyle = '#000000';
        redactionCtx.fillRect(rect.x, rect.y, rect.width, rect.height);
    } else {
        // Blur effects - we need to work with image data
        const imageData = redactionCtx.getImageData(rect.x, rect.y, rect.width, rect.height);
        
        if (rect.type === 'blur') {
            // Glass blur - transparent blur
            applyBlurEffect(imageData, rect.blurStrength);
            redactionCtx.putImageData(imageData, rect.x, rect.y);
            
            // Add semi-transparent overlay
            redactionCtx.fillStyle = 'rgba(255, 255, 255, 0.1)';
            redactionCtx.fillRect(rect.x, rect.y, rect.width, rect.height);
        } else if (rect.type === 'opaque-blur') {
            // Opaque blur - stronger blur with white background
            applyBlurEffect(imageData, rect.blurStrength);
            redactionCtx.putImageData(imageData, rect.x, rect.y);
            
            // Add stronger white overlay
            redactionCtx.fillStyle = 'rgba(255, 255, 255, 0.6)';
            redactionCtx.fillRect(rect.x, rect.y, rect.width, rect.height);
        }
    }
}

function applyBlurEffect(imageData, strength) {
    const data = imageData.data;
    const width = imageData.width;
    const height = imageData.height;
    
    // Simple box blur implementation
    for (let i = 0; i < strength; i++) {
        for (let y = 1; y < height - 1; y++) {
            for (let x = 1; x < width - 1; x++) {
                const idx = (y * width + x) * 4;
                
                // Get surrounding pixels
                const top = ((y-1) * width + x) * 4;
                const bottom = ((y+1) * width + x) * 4;
                const left = (y * width + (x-1)) * 4;
                const right = (y * width + (x+1)) * 4;
                
                // Average the RGB values
                data[idx] = (data[top] + data[bottom] + data[left] + data[right]) / 4;     // R
                data[idx+1] = (data[top+1] + data[bottom+1] + data[left+1] + data[right+1]) / 4; // G
                data[idx+2] = (data[top+2] + data[bottom+2] + data[left+2] + data[right+2]) / 4; // B
                // Alpha remains the same
            }
        }
    }
}

function redrawCanvas() {
    // Clear and redraw original image
    redactionCtx.clearRect(0, 0, redactionCanvas.width, redactionCanvas.height);
    redactionCtx.drawImage(originalImage, 0, 0, redactionCanvas.width, redactionCanvas.height);
    
    // Reapply all redactions
    redactionRectangles.forEach(rect => {
        applyRedaction(rect);
    });
}

function setTool(tool) {
    currentTool = tool;
    
    // Show/hide blur options
    const blurOptions = document.getElementById('blurOptions');
    if (tool === 'blur' || tool === 'opaque-blur') {
        blurOptions.style.display = 'block';
    } else {
        blurOptions.style.display = 'none';
    }
    
    // Update button states
    document.querySelectorAll('.tool-button').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
}

function updateBlurStrength(value) {
    blurStrength = parseInt(value);
    document.getElementById('blurValue').textContent = value + 'px';
    
    // Update blur strength for all blur rectangles
    redactionRectangles.forEach(rect => {
        if (rect.type === 'blur' || rect.type === 'opaque-blur') {
            rect.blurStrength = blurStrength;
        }
    });
    
    // Redraw with new blur strength
    redrawCanvas();
}

function clearRedactions() {
    redactionRectangles = [];
    redrawCanvas();
}

function downloadRedactedImage() {
    if (!redactionCanvas) return;
    
    const link = document.createElement('a');
    link.download = 'redacted-safe-image.png';
    link.href = redactionCanvas.toDataURL();
    link.click();
}

function displayRiskScenarios(scenarios) {
    const container = document.getElementById('riskScenariosContainer');
    const warning = document.getElementById('scenarioWarning');
    container.innerHTML = '';

    if (!scenarios || scenarios.length === 0) {
        container.innerHTML = '<div class="scenario-card"><div class="scenario-text">No specific risk scenarios generated.</div></div>';
        return;
    }

    scenarios.forEach((scenario, index) => {
        const card = document.createElement('div');
        card.className = 'scenario-card';
        
        // Extract emoji and text
        const emojiMatch = scenario.match(/^([^\s]+\s)/);
        const emoji = emojiMatch ? emojiMatch[1] : '⚠️';
        const text = scenario.replace(/^([^\s]+\s)/, '');

        card.innerHTML = `
            <span class="scenario-emoji">${emoji}</span>
            <div class="scenario-text">${text}</div>
        `;
        
        container.appendChild(card);
    });

    // Update warning based on number of scenarios
    if (scenarios.length >= 2) {
        warning.innerHTML = '⚠️ Multiple risk scenarios detected - consider reviewing your post carefully';
    }
}

function updateRiskGauge(riskLevel) {
    const needle = document.getElementById('riskNeedle');
    const currentRisk = document.getElementById('currentRiskLevel');
    
    let rotation = 0;
    let riskClass = 'risk-unknown';
    
    switch(riskLevel) {
        case 'low':
            rotation = -45;
            riskClass = 'risk-low';
            break;
        case 'medium':
            rotation = 0;
            riskClass = 'risk-medium';
            break;
        case 'high':
            rotation = 45;
            riskClass = 'risk-high';
            break;
        default:
            rotation = 0;
            riskClass = 'risk-unknown';
    }
    
    needle.style.transform = `translateX(-50%) rotate(${rotation}deg)`;
    currentRisk.textContent = riskLevel.toUpperCase();
    currentRisk.className = riskClass;
}

function createDataDistributionChart(detectedData) {
    const ctx = document.getElementById('dataDistributionChart').getContext('2d');
    
    if (dataDistributionChart) {
        dataDistributionChart.destroy();
    }

    const categories = Object.keys(detectedData);
    const dataCounts = categories.map(category => detectedData[category].length);

    const nonEmptyCategories = categories.filter((category, index) => dataCounts[index] > 0);
    const nonEmptyCounts = dataCounts.filter(count => count > 0);

    dataDistributionChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: nonEmptyCategories.map(name => 
                name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
            ),
            datasets: [{
                data: nonEmptyCounts,
                backgroundColor: [
                    '#3498db', '#e74c3c', '#f39c12', '#9b59b6', '#1abc9c'
                ],
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        usePointStyle: true
                    }
                }
            },
            cutout: '60%'
        }
    });
}

function createRiskBreakdownChart(detectedData) {
    const ctx = document.getElementById('riskBreakdownChart').getContext('2d');
    
    if (riskBreakdownChart) {
        riskBreakdownChart.destroy();
    }

    const categories = Object.keys(detectedData);
    const dataCounts = categories.map(category => detectedData[category].length);

    const riskWeights = {
        'financial_info': 3,
        'medical_info': 3,
        'personal_identifiers': 2,
        'location_data': 2,
        'other_sensitive_data': 1
    };

    const weightedScores = categories.map(category => 
        detectedData[category].length * (riskWeights[category] || 1)
    );

    riskBreakdownChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: categories.map(name => 
                name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
            ),
            datasets: [{
                label: 'Risk Score (Weighted)',
                data: weightedScores,
                backgroundColor: [
                    '#e74c3c', '#e74c3c', '#f39c12', '#f39c12', '#3498db'
                ],
                borderColor: '#2c3e50',
                borderWidth: 1,
                borderRadius: 5
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: { display: true, text: 'Risk Score' },
                    grid: { color: 'rgba(0,0,0,0.1)' }
                },
                x: {
                    grid: { display: false }
                }
            }
        }
    });
}

function updateCategoryBreakdown(detectedData) {
    const container = document.getElementById('categoryBreakdown');
    container.innerHTML = '';

    let totalItems = 0;
    Object.values(detectedData).forEach(items => totalItems += items.length);

    if (totalItems === 0) {
        container.innerHTML = '<div class="category-item"><span class="category-name">No sensitive data detected</span><span class="category-count">0</span></div>';
        return;
    }

    Object.entries(detectedData).forEach(([category, items]) => {
        if (items.length > 0) {
            const item = document.createElement('div');
            item.className = 'category-item';
            
            const categoryName = category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
            const percentage = totalItems > 0 ? Math.round((items.length / totalItems) * 100) : 0;
            
            item.innerHTML = `
                <span class="category-name">${categoryName}</span>
                <div style="display: flex; align-items: center; gap: 10px;">
                    <div style="width: 100px; height: 8px; background: #ecf0f1; border-radius: 4px;">
                        <div style="width: ${percentage}%; height: 100%; background: #3498db; border-radius: 4px;"></div>
                    </div>
                    <span class="category-count">${items.length}</span>
                </div>
            `;
            
            container.appendChild(item);
        }
    });
}

function updateScoreDisplay(score) {
    const scoreValue = document.getElementById('scoreValue');
    const scoreText = document.getElementById('scoreText');
    const scoreCircle = document.getElementById('scoreCircle');

    scoreValue.textContent = score;
    
    if (score >= 80) {
        scoreCircle.style.background = 'conic-gradient(#27ae60 0% ' + score + '%, #ecf0f1 ' + score + '% 100%)';
        scoreText.innerHTML = '🎉 Excellent! Your privacy is well protected.';
    } else if (score >= 50) {
        scoreCircle.style.background = 'conic-gradient(#f39c12 0% ' + score + '%, #ecf0f1 ' + score + '% 100%)';
        scoreText.innerHTML = '⚠️ Good, but there\'s room for improvement.';
    } else {
        scoreCircle.style.background = 'conic-gradient(#e74c3c 0% ' + score + '%, #ecf0f1 ' + score + '% 100%)';
        scoreText.innerHTML = '🚨 High risk detected. Review recommendations below.';
    }

    saveScoreToHistory(score);
    displayScoreHistory();
}

async function analyzeImage() {
    const fileInput = document.getElementById('imageInput');
    const file = fileInput.files[0];
    
    if (!file) {
        showError('Please select an image file');
        return;
    }

    const formData = new FormData();
    formData.append('image', file);

    showLoading();
    hideResults();
    hideError();

    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Initialize redaction tool with the uploaded image
            initializeRedactionTool(file);
            displayResults(data);
        } else {
            showError(data.error || 'Analysis failed');
        }
    } catch (error) {
        showError('Network error: ' + error.message);
    } finally {
        hideLoading();
    }
}

function displayResults(data) {
    // Display extracted text
    document.getElementById('extractedText').textContent = data.extracted_text || 'No text extracted';

    // Display detected data
    const detectedData = data.analysis.detected_data || {};
    document.getElementById('detectedData').innerHTML = formatDetectedData(detectedData);

    // Display risk level and update gauge
    const riskLevel = data.analysis.risk_level || 'unknown';
    updateRiskGauge(riskLevel);

    // Display risk explanation
    document.getElementById('riskExplanation').textContent = data.analysis.risk_explanation || 'No explanation provided';

    // Display recommendations
    const recommendationsList = document.getElementById('recommendations');
    recommendationsList.innerHTML = '';
    (data.analysis.recommendations || []).forEach(rec => {
        const li = document.createElement('li');
        li.textContent = rec;
        recommendationsList.appendChild(li);
    });

    // Update privacy score display
    if (data.analysis.privacy_score !== undefined) {
        updateScoreDisplay(data.analysis.privacy_score);
    }

    // Display risk scenarios
    if (data.analysis.risk_scenarios) {
        displayRiskScenarios(data.analysis.risk_scenarios);
    }

    // Create interactive visualizations
    createDataDistributionChart(detectedData);
    createRiskBreakdownChart(detectedData);
    updateCategoryBreakdown(detectedData);

    showResults();
}

function formatDetectedData(data) {
    let html = '';
    for (const [category, items] of Object.entries(data)) {
        if (items && items.length > 0) {
            html += `<strong>${category.replace(/_/g, ' ').toUpperCase()}:</strong><ul>`;
            items.forEach(item => {
                html += `<li>${item}</li>`;
            });
            html += '</ul>';
        }
    }
    return html || 'No sensitive data detected';
}

function showLoading() {
    document.getElementById('loading').classList.remove('hidden');
}

function hideLoading() {
    document.getElementById('loading').classList.add('hidden');
}

function showResults() {
    document.getElementById('results').classList.remove('hidden');
}

function hideResults() {
    document.getElementById('results').classList.add('hidden');
}

function showError(message) {
    const errorDiv = document.getElementById('error');
    errorDiv.textContent = message;
    errorDiv.classList.remove('hidden');
}

function hideError() {
    document.getElementById('error').classList.add('hidden');
}

// Initialize history chart when page loads
document.addEventListener('DOMContentLoaded', function() {
    displayScoreHistory();
});