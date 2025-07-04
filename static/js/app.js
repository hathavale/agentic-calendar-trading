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
    const criteria = applicationData.screening_criteria;
    
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
        }
    });
}

function applySettings() {
    const applySettingsBtn = document.getElementById('apply-settings');
    if (!applySettingsBtn) return;
    
    const originalText = applySettingsBtn.textContent;
    
    applySettingsBtn.textContent = 'Applied!';
    applySettingsBtn.style.backgroundColor = 'var(--color-success)';
    
    setTimeout(() => {
        applySettingsBtn.textContent = originalText;
        applySettingsBtn.style.backgroundColor = '';
    }, 2000);
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
    
    refreshScanBtn.textContent = 'Scanning...';
    refreshScanBtn.disabled = true;
    
    // Call Flask API to trigger scan
    fetch('/api/refresh-scan', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        console.log('Scan completed:', data);
        // Reload application data
        loadApplicationData().then(() => {
            initializeStocksTable();
            updateSystemStatus();
        });
        
        refreshScanBtn.textContent = 'Scan Complete!';
        setTimeout(() => {
            refreshScanBtn.textContent = originalText;
            refreshScanBtn.disabled = false;
        }, 1000);
    })
    .catch(error => {
        console.error('Error during scan:', error);
        refreshScanBtn.textContent = 'Error';
        setTimeout(() => {
            refreshScanBtn.textContent = originalText;
            refreshScanBtn.disabled = false;
        }, 2000);
    });
}

// Event Listeners
function bindEventListeners() {
    const themeToggle = document.getElementById('theme-toggle');
    const stockFilter = document.getElementById('stock-filter');
    const refreshScanBtn = document.getElementById('refresh-scan');
    const exportStocksBtn = document.getElementById('export-stocks');
    const applySettingsBtn = document.getElementById('apply-settings');
    const resetSettingsBtn = document.getElementById('reset-settings');
    
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
    
    if (stockFilter) {
        stockFilter.addEventListener('change', (e) => {
            currentFilter = e.target.value;
            populateStocksTable(applicationData.all_stocks);
        });
    }
    
    if (refreshScanBtn) {
        refreshScanBtn.addEventListener('click', refreshScan);
    }
    
    if (exportStocksBtn) {
        exportStocksBtn.addEventListener('click', exportStocksToCSV);
    }
    
    if (applySettingsBtn) {
        applySettingsBtn.addEventListener('click', applySettings);
    }
    
    if (resetSettingsBtn) {
        resetSettingsBtn.addEventListener('click', resetSettings);
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