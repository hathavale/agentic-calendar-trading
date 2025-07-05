// Application Data - will be loaded from Flask API
let applicationData = {};

// Application State
let currentTheme = 'light';
let currentFilter = 'all';
let profitLossChart = null;

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing application...');
    loadApplicationData().then(() => {
        initializeTheme();
        initializeTabs();
        initializeStocksTable();
        initializeCalendarSpreads();
        initializeSettings();
        initializeSymbolsInput();
        bindEventListeners();
        
        // Initialize chart after a short delay to ensure DOM is ready
        setTimeout(() => {
            initializeProfitLossChart();
        }, 100);
        
        // Simulate real-time updates
        setInterval(updateSystemStatus, 30000);
        
        console.log('Application initialized successfully');
    });
});

// Load data from Flask API
async function loadApplicationData() {
    try {
        const response = await fetch('/api/data');
        applicationData = await response.json();
        console.log('Application data loaded successfully');
    } catch (error) {
        console.error('Error loading application data:', error);
        // Fallback to embedded data if API fails
        applicationData = {
            // Fallback data structure...
        };
    }
}

// Theme Management
function initializeTheme() {
    const themeToggle = document.getElementById('theme-toggle');
    const themeIcon = document.getElementById('theme-icon');
    
    if (themeToggle && themeIcon) {
        document.documentElement.setAttribute('data-color-scheme', currentTheme);
        updateThemeIcon();
    }
}

function toggleTheme() {
    currentTheme = currentTheme === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-color-scheme', currentTheme);
    updateThemeIcon();
    console.log('Theme switched to:', currentTheme);
}

function updateThemeIcon() {
    const themeIcon = document.getElementById('theme-icon');
    if (themeIcon) {
        themeIcon.textContent = currentTheme === 'light' ? '🌙' : '☀️';
    }
}

// Tab Management
function initializeTabs() {
    const tabButtons = document.querySelectorAll('.nav-tab');
    const tabPanes = document.querySelectorAll('.tab-pane');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            const tabId = button.getAttribute('data-tab');
            switchTab(tabId);
        });
    });
}

function switchTab(tabId) {
    console.log('Switching to tab:', tabId);
    
    // Update tab buttons
    const tabButtons = document.querySelectorAll('.nav-tab');
    tabButtons.forEach(btn => btn.classList.remove('active'));
    const activeButton = document.querySelector(`[data-tab="${tabId}"]`);
    if (activeButton) {
        activeButton.classList.add('active');
    }
    
    // Update tab panes
    const tabPanes = document.querySelectorAll('.tab-pane');
    tabPanes.forEach(pane => pane.classList.remove('active'));
    const activePane = document.getElementById(tabId);
    if (activePane) {
        activePane.classList.add('active');
    }
    
    // Initialize chart when calendar tab is opened
    if (tabId === 'calendar' && !profitLossChart) {
        setTimeout(() => {
            initializeProfitLossChart();
        }, 100);
    }
}

// Stocks Table Management
function initializeStocksTable() {
    const stocksTableBody = document.getElementById('stocks-table-body');
    if (stocksTableBody) {
        populateStocksTable(applicationData.all_stocks);
    }
}

function populateStocksTable(stocks) {
    const stocksTableBody = document.getElementById('stocks-table-body');
    if (!stocksTableBody) return;
    
    stocksTableBody.innerHTML = '';
    
    const filteredStocks = filterStocks(stocks);
    
    filteredStocks.forEach(stock => {
        const row = document.createElement('tr');
        row.className = stock.qualified ? 'qualified-row' : 'unqualified-row';
        
        row.innerHTML = `
            <td><strong>${stock.symbol}</strong></td>
            <td>$${stock.current_price.toFixed(2)}</td>
            <td class="${stock.atr_percentage <= 0.05 ? 'text-success' : 'text-error'}">
                ${(stock.atr_percentage * 100).toFixed(1)}%
            </td>
            <td class="${(stock.implied_volatility >= 20 && stock.implied_volatility <= 40) ? 'text-success' : 'text-error'}">
                ${stock.implied_volatility.toFixed(1)}%
            </td>
            <td class="${stock.iv_percentile <= 50 ? 'text-success' : 'text-error'}">
                ${stock.iv_percentile.toFixed(1)}%
            </td>
            <td class="${stock.open_interest >= 1000 ? 'text-success' : 'text-error'}">
                ${stock.open_interest.toLocaleString()}
            </td>
            <td class="${stock.price_stability_30d <= 0.10 ? 'text-success' : 'text-error'}">
                ${(stock.price_stability_30d * 100).toFixed(1)}%
            </td>
            <td>
                <div class="criteria-indicator">
                    <span class="criteria-dot ${stock.criteria_met_count >= 6 ? 'pass' : 'fail'}"></span>
                    ${stock.criteria_met_count}/8
                </div>
            </td>
            <td>
                <span class="status ${stock.qualified ? 'status--success' : 'status--error'}">
                    ${stock.qualified ? 'Qualified' : 'Unqualified'}
                </span>
            </td>
        `;
        
        row.addEventListener('click', () => {
            if (stock.qualified) {
                switchTab('calendar');
            }
        });
        
        stocksTableBody.appendChild(row);
    });
}

function filterStocks(stocks) {
    switch (currentFilter) {
        case 'qualified':
            return stocks.filter(stock => stock.qualified);
        case 'unqualified':
            return stocks.filter(stock => !stock.qualified);
        default:
            return stocks;
    }
}

// Calendar Spreads Management
function initializeCalendarSpreads() {
    const spreadStrategies = document.getElementById('spread-strategies');
    if (spreadStrategies) {
        populateCalendarSpreads(applicationData.calendar_spreads);
    }
}

function populateCalendarSpreads(spreads) {
    const spreadStrategies = document.getElementById('spread-strategies');
    if (!spreadStrategies) return;
    
    spreadStrategies.innerHTML = '';
    
    spreads.forEach(spread => {
        const strategyCard = document.createElement('div');
        strategyCard.className = 'strategy-card';
        
        strategyCard.innerHTML = `
            <div class="strategy-header">
                <div class="strategy-type">${spread.strategy_type}</div>
                <div class="strategy-strike">Strike: $${spread.strike_price}</div>
            </div>
            <div class="strategy-metrics">
                <div class="metric-item">
                    <div class="metric-label">Risk/Reward</div>
                    <div class="metric-value">${spread.risk_reward_ratio.toFixed(2)}:1</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">Profit Zone Low</div>
                    <div class="metric-value">$${spread.max_profit_zone_low.toFixed(2)}</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">Profit Zone High</div>
                    <div class="metric-value">$${spread.max_profit_zone_high.toFixed(2)}</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">Breakeven Low</div>
                    <div class="metric-value">$${spread.breakeven_low.toFixed(2)}</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">Breakeven High</div>
                    <div class="metric-value">$${spread.breakeven_high.toFixed(2)}</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">Time Frame</div>
                    <div class="metric-value">${spread.front_month_days}/${spread.back_month_days} days</div>
                </div>
            </div>
        `;
        
        spreadStrategies.appendChild(strategyCard);
    });
}

// Profit/Loss Chart
function initializeProfitLossChart() {
    const canvas = document.getElementById('profitLossChart');
    if (!canvas) {
        console.error('Canvas element not found');
        return;
    }
    
    const ctx = canvas.getContext('2d');
    if (!ctx) {
        console.error('Canvas context not available');
        return;
    }
    
    // Destroy existing chart if it exists
    if (profitLossChart) {
        profitLossChart.destroy();
    }
    
    // Generate sample profit/loss data for XLF calendar spread
    const priceRange = [];
    const profitLoss = [];
    const currentPrice = 64.83;
    const strikePrice = 65;
    
    for (let price = 58; price <= 72; price += 0.5) {
        priceRange.push(price);
        
        // Simplified calendar spread P&L calculation
        let pnl = 0;
        const distanceFromStrike = Math.abs(price - strikePrice);
        
        if (distanceFromStrike <= 2) {
            // Profit zone
            pnl = 100 * (1 - (distanceFromStrike / 2));
        } else {
            // Loss zone
            pnl = -50 * (distanceFromStrike - 2);
        }
        
        profitLoss.push(Math.max(pnl, -150)); // Cap losses
    }
    
    try {
        profitLossChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: priceRange.map(p => `$${p.toFixed(1)}`),
                datasets: [{
                    label: 'Profit/Loss',
                    data: profitLoss,
                    borderColor: '#1FB8CD',
                    backgroundColor: 'rgba(31, 184, 205, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#1FB8CD',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const value = context.parsed.y;
                                return `P&L: ${value >= 0 ? '+' : ''}$${value.toFixed(0)}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Stock Price at Expiration'
                        },
                        grid: {
                            color: 'rgba(119, 124, 124, 0.2)'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Profit/Loss ($)'
                        },
                        grid: {
                            color: 'rgba(119, 124, 124, 0.2)'
                        }
                    }
                }
            }
        });
        
        console.log('Profit/Loss chart initialized successfully');
    } catch (error) {
        console.error('Error initializing chart:', error);
    }
}

// Settings Management
function initializeSettings() {
    console.log('Initializing settings...');
    
    // Initialize data source diagnostics
    initializeDataSourceStatus();
    
    if (!applicationData.screening_criteria) {
        console.warn('No screening criteria found in application data');
        return;
    }
    
    const criteria = applicationData.screening_criteria;
    console.log('Initializing settings with criteria:', criteria);
    
    const elements = {
        'atr-threshold': criteria.atr_threshold * 100,
        'iv-min': criteria.iv_range[0],
        'iv-max': criteria.iv_range[1],
        'price-min': criteria.price_range[0],
        'price-max': criteria.price_range[1],
        'iv-percentile-max': criteria.iv_percentile_max,
        'open-interest-min': criteria.open_interest_min,
        'price-stability-max': criteria.price_stability_30d * 100
    };
    
    Object.entries(elements).forEach(([id, value]) => {
        const element = document.getElementById(id);
        if (element) {
            element.value = value;
            console.log(`Set ${id} to ${value}`);
        } else {
            console.warn(`Element with id '${id}' not found`);
        }
    });
}

function applySettings() {
    const applySettingsBtn = document.getElementById('apply-settings');
    if (!applySettingsBtn) return;
    
    const originalText = applySettingsBtn.textContent;
    
    // Collect all the settings from form inputs
    const newCriteria = {
        atr_threshold: parseFloat(document.getElementById('atr-threshold')?.value || 5) / 100,
        iv_range: [
            parseInt(document.getElementById('iv-min')?.value || 20),
            parseInt(document.getElementById('iv-max')?.value || 40)
        ],
        price_range: [
            parseInt(document.getElementById('price-min')?.value || 50),
            parseInt(document.getElementById('price-max')?.value || 150)
        ],
        iv_percentile_max: parseInt(document.getElementById('iv-percentile-max')?.value || 50),
        open_interest_min: parseInt(document.getElementById('open-interest-min')?.value || 1000),
        price_stability_30d: parseFloat(document.getElementById('price-stability-max')?.value || 10) / 100
    };
    
    applySettingsBtn.textContent = 'Applying...';
    applySettingsBtn.disabled = true;
    
    // Send the updated criteria to the backend
    fetch('/api/screening-criteria', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(newCriteria)
    })
    .then(response => response.json())
    .then(data => {
        console.log('Settings updated:', data);
        
        // Update local applicationData
        Object.assign(applicationData.screening_criteria, newCriteria);
        
        applySettingsBtn.textContent = 'Applied!';
        applySettingsBtn.style.backgroundColor = 'var(--color-success)';
        
        setTimeout(() => {
            applySettingsBtn.textContent = originalText;
            applySettingsBtn.style.backgroundColor = '';
            applySettingsBtn.disabled = false;
        }, 2000);
    })
    .catch(error => {
        console.error('Error updating settings:', error);
        applySettingsBtn.textContent = 'Error';
        applySettingsBtn.style.backgroundColor = 'var(--color-error)';
        
        setTimeout(() => {
            applySettingsBtn.textContent = originalText;
            applySettingsBtn.style.backgroundColor = '';
            applySettingsBtn.disabled = false;
        }, 2000);
    });
}

function resetSettings() {
    initializeSettings();
}

// Export Functionality
function exportStocksToCSV() {
    const stocks = filterStocks(applicationData.all_stocks);
    const csvContent = [
        ['Symbol', 'Price', 'ATR%', 'IV%', 'IV Percentile', 'Open Interest', '30d Stability', 'Criteria Met', 'Status'],
        ...stocks.map(stock => [
            stock.symbol,
            stock.current_price.toFixed(2),
            (stock.atr_percentage * 100).toFixed(1),
            stock.implied_volatility.toFixed(1),
            stock.iv_percentile.toFixed(1),
            stock.open_interest,
            (stock.price_stability_30d * 100).toFixed(1),
            `${stock.criteria_met_count}/8`,
            stock.qualified ? 'Qualified' : 'Unqualified'
        ])
    ].map(row => row.join(',')).join('\n');
    
    downloadCSV(csvContent, 'stock_screening_results.csv');
}

function downloadCSV(content, filename) {
    const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    
    if (link.download !== undefined) {
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}

// Dashboard Updates
function updateDashboardStats() {
    if (!applicationData.system_stats) return;
    
    const stats = applicationData.system_stats;
    
    // Update stat cards
    const statCards = document.querySelectorAll('.stat-card .stat-value');
    if (statCards.length >= 4) {
        statCards[0].textContent = stats.total_stocks_analyzed || 0;
        statCards[1].textContent = stats.qualified_stocks || 0;
        statCards[2].textContent = `${stats.success_rate || 0}%`;
        statCards[3].textContent = `${stats.average_criteria_met || 0}/8`;
    }
    
    // Update stock highlight if there are qualified stocks
    if (applicationData.qualified_stocks && applicationData.qualified_stocks.length > 0) {
        const stock = applicationData.qualified_stocks[0];
        const stockSymbol = document.querySelector('.stock-symbol');
        const stockPrice = document.querySelector('.stock-price');
        const stockScore = document.querySelector('.stock-score');
        
        if (stockSymbol) stockSymbol.textContent = stock.symbol;
        if (stockPrice) stockPrice.textContent = `$${stock.current_price.toFixed(2)}`;
        if (stockScore) stockScore.textContent = `Score: ${stock.score.toFixed(1)}`;
    }
}

// System Status Updates
function updateSystemStatus() {
    const now = new Date();
    const statusItems = document.querySelectorAll('.status-item span:last-child');
    
    if (statusItems.length >= 2) {
        statusItems[0].textContent = now.toLocaleString('en-US', {
            month: 'long',
            day: 'numeric',
            year: 'numeric',
            hour: 'numeric',
            minute: '2-digit',
            hour12: true
        });
        
        const nextScan = new Date(now.getTime() + 30 * 60000);
        statusItems[1].textContent = nextScan.toLocaleString('en-US', {
            month: 'long',
            day: 'numeric',
            year: 'numeric',
            hour: 'numeric',
            minute: '2-digit',
            hour12: true
        });
    }
}

function refreshScan() {
    const refreshScanBtn = document.getElementById('refresh-scan');
    if (!refreshScanBtn) return;
    
    const originalText = refreshScanBtn.textContent;
    
    // Show loading state
    refreshScanBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Fetching Live Data...';
    refreshScanBtn.disabled = true;
    
    // Show loading indicator in dashboard
    showLoadingIndicator();
    
    // Call Flask API to trigger scan with live Yahoo Finance data
    fetch('/api/refresh-scan', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Live scan completed:', data);
        
        if (data.status === 'error') {
            throw new Error(data.message || 'Scan failed');
        }
        
        // Show success message with details
        refreshScanBtn.innerHTML = '<i class="fas fa-check"></i> Live Data Updated!';
        showSuccessMessage(data.message || 'Scan completed successfully');
        
        // Reload application data
        return loadApplicationData();
    })
    .then(() => {
        // Update all UI components with new data
        hideLoadingIndicator();
        initializeStocksTable();
        updateDashboardStats();
        updateSystemStatus();
        
        // Reset button after delay
        setTimeout(() => {
            refreshScanBtn.innerHTML = originalText;
            refreshScanBtn.disabled = false;
        }, 2000);
    })
    .catch(error => {
        console.error('Error during live scan:', error);
        hideLoadingIndicator();
        
        refreshScanBtn.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Error';
        showErrorMessage(`Scan failed: ${error.message}`);
        
        setTimeout(() => {
            refreshScanBtn.innerHTML = originalText;
            refreshScanBtn.disabled = false;
        }, 3000);
    });
}

// Helper functions for UI feedback
function showLoadingIndicator() {
    const dashboardGrid = document.querySelector('.dashboard-grid');
    if (dashboardGrid) {
        dashboardGrid.style.opacity = '0.6';
        dashboardGrid.style.pointerEvents = 'none';
    }
}

function hideLoadingIndicator() {
    const dashboardGrid = document.querySelector('.dashboard-grid');
    if (dashboardGrid) {
        dashboardGrid.style.opacity = '1';
        dashboardGrid.style.pointerEvents = 'auto';
    }
}

function showSuccessMessage(message) {
    showNotification(message, 'success');
}

function showErrorMessage(message) {
    showNotification(message, 'error');
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
            <span>${message}</span>
        </div>
        <button class="notification-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

// Data Source Diagnostics
function initializeDataSourceStatus() {
    // Load current data source status
    loadDataSourceStatus();
    
    // Bind diagnostic event listeners
    const testAlphaVantageBtn = document.getElementById('test-alpha-vantage');
    const fullDiagnosticsBtn = document.getElementById('run-full-diagnostics');
    const troubleshootingBtn = document.getElementById('view-troubleshooting');
    
    if (testAlphaVantageBtn) {
        testAlphaVantageBtn.addEventListener('click', testAlphaVantage);
    }
    
    if (fullDiagnosticsBtn) {
        fullDiagnosticsBtn.addEventListener('click', runFullDiagnostics);
    }
    
    if (troubleshootingBtn) {
        troubleshootingBtn.addEventListener('click', viewTroubleshooting);
    }
}

async function loadDataSourceStatus() {
    try {
        const response = await fetch('/api/data-source');
        const data = await response.json();
        
        if (data.success) {
            updateDataSourceUI(data.config);
        } else {
            console.error('Failed to load data source status:', data.error);
        }
    } catch (error) {
        console.error('Error loading data source status:', error);
    }
}

function updateDataSourceUI(config) {
    // Update header indicator
    const headerDataSource = document.getElementById('header-data-source');
    const headerSourceStatus = document.getElementById('header-source-status');
    
    if (headerDataSource) {
        headerDataSource.textContent = config.current_source === 'alpha_vantage' ? 'Alpha Vantage' : 'yfinance';
    }
    
    if (headerSourceStatus) {
        headerSourceStatus.className = `source-status ${config.api_key_present ? 'active' : 'warning'}`;
    }
    
    // Update settings panel
    const currentDataSource = document.getElementById('current-data-source');
    const alphaVantageStatus = document.getElementById('alpha-vantage-status');
    
    if (currentDataSource) {
        currentDataSource.textContent = config.current_source === 'alpha_vantage' ? 'Alpha Vantage (Primary)' : 'yfinance (Fallback)';
    }
    
    if (alphaVantageStatus) {
        const statusText = config.api_key_present ? 'API Key Present' : 'API Key Missing';
        const statusClass = config.api_key_present ? 'status--success' : 'status--warning';
        alphaVantageStatus.innerHTML = `<span class="status ${statusClass}">${statusText}</span>`;
    }
}

async function testAlphaVantage() {
    const testBtn = document.getElementById('test-alpha-vantage');
    const diagnosticResults = document.getElementById('diagnostic-results');
    const diagnosticOutput = document.getElementById('diagnostic-output');
    
    if (testBtn) {
        testBtn.disabled = true;
        testBtn.textContent = 'Testing...';
    }
    
    try {
        const response = await fetch('/api/diagnostics/simple?symbol=AAPL');
        const data = await response.json();
        
        if (diagnosticOutput) {
            if (data.success) {
                diagnosticOutput.innerHTML = `
                    <div class="diagnostic-success">
                        <h6>✅ Alpha Vantage Test Successful</h6>
                        <p>${data.message}</p>
                        <div class="diagnostic-details">
                            <p><strong>Symbol:</strong> ${data.data.symbol}</p>
                            <p><strong>Price:</strong> $${data.data.price}</p>
                            <p><strong>Change:</strong> ${data.data.change}</p>
                            <p><strong>Response Time:</strong> ${data.data.api_response_time.toFixed(2)}s</p>
                        </div>
                    </div>
                `;
            } else {
                diagnosticOutput.innerHTML = `
                    <div class="diagnostic-error">
                        <h6>❌ Alpha Vantage Test Failed</h6>
                        <p><strong>Error:</strong> ${data.error}</p>
                        ${data.recommendations ? `
                            <div class="recommendations">
                                <h6>Recommendations:</h6>
                                <ul>
                                    ${data.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                                </ul>
                            </div>
                        ` : ''}
                    </div>
                `;
            }
        }
        
        if (diagnosticResults) {
            diagnosticResults.style.display = 'block';
        }
        
    } catch (error) {
        if (diagnosticOutput) {
            diagnosticOutput.innerHTML = `
                <div class="diagnostic-error">
                    <h6>💥 Test Error</h6>
                    <p>Failed to run diagnostic test: ${error.message}</p>
                </div>
            `;
        }
        
        if (diagnosticResults) {
            diagnosticResults.style.display = 'block';
        }
    } finally {
        if (testBtn) {
            testBtn.disabled = false;
            testBtn.textContent = 'Test Alpha Vantage';
        }
    }
}

async function runFullDiagnostics() {
    const fullBtn = document.getElementById('run-full-diagnostics');
    const diagnosticResults = document.getElementById('diagnostic-results');
    const diagnosticOutput = document.getElementById('diagnostic-output');
    
    if (fullBtn) {
        fullBtn.disabled = true;
        fullBtn.textContent = 'Running...';
    }
    
    try {
        const response = await fetch('/api/diagnostics?symbol=AAPL');
        const data = await response.json();
        
        if (diagnosticOutput) {
            if (data.success) {
                const results = data.data;
                let html = `
                    <div class="diagnostic-full">
                        <h6>🔍 Full Diagnostic Report</h6>
                        <p><strong>Timestamp:</strong> ${new Date(results.timestamp).toLocaleString()}</p>
                        <p><strong>Symbol:</strong> ${results.symbol}</p>
                        
                        <div class="test-results">
                `;
                
                for (const [testName, testResult] of Object.entries(results.tests)) {
                    const statusIcon = testResult.status === 'PASS' ? '✅' : 
                                     testResult.status === 'FAIL' ? '❌' : 
                                     testResult.status === 'RATE_LIMITED' ? '⚠️' : 'ℹ️';
                    
                    html += `
                        <div class="test-result">
                            <h6>${statusIcon} ${testName.toUpperCase()}</h6>
                            <p>${testResult.message}</p>
                            ${testResult.recommendation ? `<p class="recommendation"><strong>Recommendation:</strong> ${testResult.recommendation}</p>` : ''}
                        </div>
                    `;
                }
                
                html += `
                        </div>
                        
                        <div class="config-info">
                            <h6>Current Configuration</h6>
                            <p><strong>Default Source:</strong> ${results.current_config.default_source}</p>
                            <p><strong>API Key Present:</strong> ${results.current_config.api_key_present ? 'Yes' : 'No'}</p>
                            <p><strong>Fallback Enabled:</strong> ${results.current_config.fallback_enabled ? 'Yes' : 'No'}</p>
                        </div>
                    </div>
                `;
                
                diagnosticOutput.innerHTML = html;
            } else {
                diagnosticOutput.innerHTML = `
                    <div class="diagnostic-error">
                        <h6>❌ Diagnostic Failed</h6>
                        <p>${data.error}</p>
                    </div>
                `;
            }
        }
        
        if (diagnosticResults) {
            diagnosticResults.style.display = 'block';
        }
        
    } catch (error) {
        if (diagnosticOutput) {
            diagnosticOutput.innerHTML = `
                <div class="diagnostic-error">
                    <h6>💥 Diagnostic Error</h6>
                    <p>Failed to run full diagnostics: ${error.message}</p>
                </div>
            `;
        }
        
        if (diagnosticResults) {
            diagnosticResults.style.display = 'block';
        }
    } finally {
        if (fullBtn) {
            fullBtn.disabled = false;
            fullBtn.textContent = 'Full Diagnostics';
        }
    }
}

function viewTroubleshooting() {
    // Open troubleshooting guide in a new window/tab
    const troubleshootingContent = `
        <!DOCTYPE html>
        <html>
        <head>
            <title>Alpha Vantage Troubleshooting Guide</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }
                h1, h2, h3 { color: #333; }
                .solution { background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }
                .error { color: #d32f2f; }
                .success { color: #388e3c; }
                .warning { color: #f57c00; }
                code { background: #f0f0f0; padding: 2px 4px; border-radius: 3px; }
                pre { background: #f0f0f0; padding: 10px; border-radius: 5px; overflow-x: auto; }
            </style>
        </head>
        <body>
            <h1>Alpha Vantage API Troubleshooting Guide</h1>
            
            <h2>Common Issues and Solutions</h2>
            
            <div class="solution">
                <h3>🔑 "API key not found" Error</h3>
                <p><strong>Problem:</strong> Alpha Vantage API key is missing or not set correctly.</p>
                <p><strong>Solution:</strong></p>
                <pre>export ALPHA_VANTAGE_API_KEY="your_api_key_here"</pre>
                <p>Get a free API key from: <a href="https://www.alphavantage.co/support/#api-key" target="_blank">Alpha Vantage</a></p>
            </div>
            
            <div class="solution">
                <h3>⚠️ "Rate Limited" Error</h3>
                <p><strong>Problem:</strong> Exceeded API rate limits (5 requests/minute for free tier).</p>
                <p><strong>Solution:</strong> Wait 15 minutes or upgrade to premium plan.</p>
            </div>
            
            <div class="solution">
                <h3>🌐 Connection Issues</h3>
                <p><strong>Problem:</strong> Network connectivity or firewall blocking requests.</p>
                <p><strong>Solution:</strong> Check internet connection and ensure HTTPS (443) is allowed.</p>
            </div>
            
            <div class="solution">
                <h3>🤔 "Unexpected response format"</h3>
                <p><strong>Problem:</strong> Invalid symbol or API response format changed.</p>
                <p><strong>Solution:</strong> Verify ticker symbol is valid (e.g., AAPL, MSFT, GOOGL).</p>
            </div>
            
            <h2>System Behavior</h2>
            <p>The system automatically falls back to yfinance when Alpha Vantage is unavailable:</p>
            <ol>
                <li>Alpha Vantage (Primary) - Comprehensive data</li>
                <li>yfinance (Fallback) - Basic data</li>
                <li>Sample data (Demo)</li>
            </ol>
            
            <h2>Need More Help?</h2>
            <p>Run the diagnostic tools in the Settings tab or check the application logs for detailed error information.</p>
        </body>
        </html>
    `;
    
    const newWindow = window.open('', '_blank');
    newWindow.document.write(troubleshootingContent);
    newWindow.document.close();
}

// Update bindEventListeners to include diagnostic functionality
function bindEventListeners() {
    // Theme toggle
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
    
    // Refresh scan
    const refreshScanBtn = document.getElementById('refresh-scan');
    if (refreshScanBtn) {
        refreshScanBtn.addEventListener('click', refreshScan);
    }
    
    // Export stocks
    const exportStocksBtn = document.getElementById('export-stocks');
    if (exportStocksBtn) {
        exportStocksBtn.addEventListener('click', exportStocksToCSV);
    }
    
    // Stock filter
    const stockFilter = document.getElementById('stock-filter');
    if (stockFilter) {
        stockFilter.addEventListener('change', (e) => {
            currentFilter = e.target.value;
            populateStocksTable(applicationData.all_stocks);
        });
    }
    
    // Settings buttons
    const applySettingsBtn = document.getElementById('apply-settings');
    const resetSettingsBtn = document.getElementById('reset-settings');
    
    if (applySettingsBtn) {
        applySettingsBtn.addEventListener('click', applySettings);
    }
    
    if (resetSettingsBtn) {
        resetSettingsBtn.addEventListener('click', resetSettings);
    }
    
    // Symbols management buttons
    const applyCustomSymbolsBtn = document.getElementById('apply-custom-symbols');
    const loadDefaultSymbolsBtn = document.getElementById('load-default-symbols');
    
    if (applyCustomSymbolsBtn) {
        applyCustomSymbolsBtn.addEventListener('click', applyCustomSymbols);
    }
    
    if (loadDefaultSymbolsBtn) {
        loadDefaultSymbolsBtn.addEventListener('click', loadDefaultSymbols);
    }
    
    // Symbols input keyboard shortcuts
    const symbolsInput = document.getElementById('custom-symbols-input');
    if (symbolsInput) {
        symbolsInput.addEventListener('keydown', (e) => {
            // Allow Ctrl+Enter or Cmd+Enter to apply symbols
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                e.preventDefault();
                applyCustomSymbols();
            }
        });
    }
}

// Symbols Input Management
function initializeSymbolsInput() {
    loadCurrentSymbols();
    updateSymbolsCount();
    
    // Add input event listener for real-time counting
    const symbolsInput = document.getElementById('custom-symbols-input');
    if (symbolsInput) {
        symbolsInput.addEventListener('input', updateSymbolsCount);
    }
}

async function loadCurrentSymbols() {
    try {
        const response = await fetch('/api/symbols');
        const data = await response.json();
        
        if (data.success) {
            const symbols = data.symbols || [];
            const defaultSymbols = data.default_symbols || [];
            
            // Update the input field
            const symbolsInput = document.getElementById('custom-symbols-input');
            if (symbolsInput) {
                symbolsInput.value = symbols.join(', ');
            }
            
            // Update the display
            displayActiveSymbols(symbols, defaultSymbols);
            updateSymbolsCount();
        }
    } catch (error) {
        console.error('Error loading current symbols:', error);
        showSymbolsStatus('Error loading current symbols', 'error');
    }
}

function displayActiveSymbols(symbols, defaultSymbols = []) {
    const container = document.getElementById('active-symbols-display');
    if (!container) return;
    
    container.innerHTML = '';
    
    if (symbols.length === 0) {
        container.innerHTML = '<span class="help-text">No symbols configured</span>';
        return;
    }
    
    symbols.forEach(symbol => {
        const tag = document.createElement('span');
        tag.className = `symbol-tag ${defaultSymbols.includes(symbol) ? 'default' : ''}`;
        tag.textContent = symbol;
        tag.title = defaultSymbols.includes(symbol) ? 'Default symbol' : 'Custom symbol';
        container.appendChild(tag);
    });
}

function updateSymbolsCount() {
    const symbolsInput = document.getElementById('custom-symbols-input');
    const countElement = document.getElementById('symbols-count');
    
    if (!symbolsInput || !countElement) return;
    
    const symbols = parseSymbolsInput(symbolsInput.value);
    countElement.textContent = symbols.length;
}

function parseSymbolsInput(input) {
    if (!input || typeof input !== 'string') return [];
    
    return input
        .split(',')
        .map(s => s.trim().toUpperCase())
        .filter(s => s.length > 0 && /^[A-Z]{1,10}$/.test(s));
}

async function applyCustomSymbols() {
    const symbolsInput = document.getElementById('custom-symbols-input');
    if (!symbolsInput) return;
    
    const inputValue = symbolsInput.value.trim();
    if (!inputValue) {
        showSymbolsStatus('Please enter at least one symbol', 'error');
        return;
    }
    
    const symbols = parseSymbolsInput(inputValue);
    
    if (symbols.length === 0) {
        showSymbolsStatus('No valid symbols found. Please use format: AAPL, MSFT, GOOGL', 'error');
        return;
    }
    
    if (symbols.length > 50) {
        showSymbolsStatus('Too many symbols. Please limit to 50 symbols maximum', 'error');
        return;
    }
    
    try {
        // Show loading state
        setSymbolsLoading(true);
        showSymbolsStatus('Applying custom symbols...', 'info');
        
        const response = await fetch('/api/symbols', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                symbols: symbols
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showSymbolsStatus(`Successfully applied ${data.symbols.length} custom symbols`, 'success');
            displayActiveSymbols(data.symbols, []);
            
            // Refresh the screening data after a short delay
            setTimeout(() => {
                refreshScan();
            }, 1000);
        } else {
            showSymbolsStatus(data.error || 'Failed to apply custom symbols', 'error');
        }
    } catch (error) {
        console.error('Error applying custom symbols:', error);
        showSymbolsStatus('Network error while applying symbols', 'error');
    } finally {
        setSymbolsLoading(false);
    }
}

async function loadDefaultSymbols() {
    try {
        setSymbolsLoading(true);
        showSymbolsStatus('Loading default symbols...', 'info');
        
        const response = await fetch('/api/symbols');
        const data = await response.json();
        
        if (data.success && data.default_symbols) {
            const symbolsInput = document.getElementById('custom-symbols-input');
            if (symbolsInput) {
                symbolsInput.value = data.default_symbols.join(', ');
                updateSymbolsCount();
            }
            
            // Apply the default symbols
            await applyCustomSymbols();
        } else {
            showSymbolsStatus('Failed to load default symbols', 'error');
        }
    } catch (error) {
        console.error('Error loading default symbols:', error);
        showSymbolsStatus('Network error while loading default symbols', 'error');
    } finally {
        setSymbolsLoading(false);
    }
}

function showSymbolsStatus(message, type = 'info') {
    const statusElement = document.getElementById('symbols-status');
    if (!statusElement) return;
    
    statusElement.className = `symbols-status ${type}`;
    statusElement.textContent = message;
    
    // Auto-hide success and info messages after 5 seconds
    if (type === 'success' || type === 'info') {
        setTimeout(() => {
            statusElement.style.display = 'none';
        }, 5000);
    }
}

function setSymbolsLoading(isLoading) {
    const container = document.querySelector('.symbols-input-section');
    const buttons = container?.querySelectorAll('button');
    
    if (isLoading) {
        container?.classList.add('symbols-loading');
        buttons?.forEach(btn => btn.disabled = true);
    } else {
        container?.classList.remove('symbols-loading');
        buttons?.forEach(btn => btn.disabled = false);
    }
}

// Utility Functions
function formatCurrency(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(value);
}

function formatPercentage(value) {
    return `${(value * 100).toFixed(1)}%`;
}

function formatNumber(value) {
    return new Intl.NumberFormat('en-US').format(value);
}