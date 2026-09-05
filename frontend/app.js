/**
 * MicroSetu (जन-सेतु) Client Application Controller
 * Manages UI State, API Communications, Audio Soundbox, Charts, and Simulations.
 */

// State Management
const STATE = {
 currentTab: 'tab-pos',
 activeMerchantId: 'MERCH_RAMESH_001',
 merchantsList: [],
 activeMerchantData: null,
 activeAmount: 35,
 cashflowChart: null,
 rbiChart: null,
 genderChart: null
};

// Initialize Application
document.addEventListener('DOMContentLoaded', async () => {
 if (window.lucide) {
 lucide.createIcons();
  }

 setupNavigation();
 setupEventListeners();
 await loadMerchants();
 await loadMacroResearchData();
});

// Tab Navigation
function setupNavigation() {
 const navBtns = document.querySelectorAll('.nav-btn');
 navBtns.forEach(btn => {
 btn.addEventListener('click', () => {
 const tabId = btn.getAttribute('data-tab');
 switchTab(tabId);
    });
  });
}

function switchTab(tabId) {
 STATE.currentTab = tabId;
  
  // Update Buttons
 document.querySelectorAll('.nav-btn').forEach(btn => {
 btn.classList.toggle('active', btn.getAttribute('data-tab') === tabId);
  });

  // Update Tab Content Panels
 document.querySelectorAll('.tab-content').forEach(panel => {
 panel.classList.toggle('active', panel.id === tabId);
  });

  // Refresh Lucide icons & charts if needed
 if (window.lucide) lucide.createIcons();

 if (tabId === 'tab-cashflow' && STATE.activeMerchantData) {
 setTimeout(renderCashflowChart, 100);
  }
}

// Load Merchants List & Populate Personas
async function loadMerchants() {
 try {
 const res = await fetch('/api/merchants');
 const data = await res.json();
 STATE.merchantsList = data.merchants || [];
 renderPersonaChips();
 if (STATE.merchantsList.length > 0) {
 await selectMerchant(STATE.merchantsList[0].merchant_id);
    }
  } catch (err) {
 console.error("Failed to load merchants:", err);
  }
}

function renderPersonaChips() {
 const container = document.getElementById('persona-chips-container');
 if (!container) return;
 container.innerHTML = '';

 STATE.merchantsList.forEach(m => {
 const chip = document.createElement('button');
 chip.className = `persona-chip ${m.merchant_id === STATE.activeMerchantId ? 'active' : ''}`;
 chip.innerHTML = `<span>${m.profile.name}</span> <small style="opacity:0.7">(${m.risk_tier.split(' ')[0]})</small>`;
 chip.addEventListener('click', () => selectMerchant(m.merchant_id));
 container.appendChild(chip);
  });
}

// Select Active Merchant & Fetch Details
async function selectMerchant(merchantId) {
 STATE.activeMerchantId = merchantId;
 renderPersonaChips();

 try {
 const res = await fetch(`/api/merchants/${merchantId}`);
 const data = await res.json();
 STATE.activeMerchantData = data;
 updateMerchantPOSView(data);
 updateUnderwritingView(data);
 updateLedgerView(data);
  } catch (err) {
 console.error("Failed to fetch merchant details:", err);
  }
}

// Update Merchant POS & Soundbox View
function updateMerchantPOSView(data) {
 const profile = data.profile;
 const uw = data.underwriting;

 document.getElementById('vendor-display-name').innerText = profile.name;
 document.getElementById('vendor-display-upi').innerText = `UPI VPA: ${profile.upi_id} | ${profile.city}`;
  
 const tierBadge = document.getElementById('vendor-pos-tier');
 tierBadge.innerText = `SetuScore: ${uw.setu_score} (${uw.risk_tier.split(' ')[0]})`;
 tierBadge.className = `score-tier-badge ${getTierBadgeClass(uw.setu_score)}`;

 drawMerchantQRCode(profile.upi_id, STATE.activeAmount);
 renderLiveTransactions(data.recent_transactions || []);
}

// Render QR Code on Canvas
function drawMerchantQRCode(vpa, amount) {
 const canvas = document.getElementById('qr-canvas');
 if (!canvas) return;
 const ctx = canvas.getContext('2d');
 const size = 180;
  
 ctx.clearRect(0, 0, size, size);
 ctx.fillStyle = '#FFFFFF';
 ctx.fillRect(0, 0, size, size);

  // Draw simulated QR Matrix
 ctx.fillStyle = '#0F172A';
  
  // Outer position markers
 drawFinderPattern(ctx, 10, 10);
 drawFinderPattern(ctx, size - 45, 10);
 drawFinderPattern(ctx, 10, size - 45);

  // Deterministic noise based on VPA and amount
 const str = `${vpa}:${amount}`;
 let hash = 0;
 for (let i = 0; i < str.length; i++) {
 hash = ((hash << 5) - hash) + str.charCodeAt(i);
 hash |= 0;
  }

 for (let r = 0; r < 24; r++) {
 for (let c = 0; c < 24; c++) {
 if ((r < 7 && c < 7) || (r < 7 && c > 16) || (r > 16 && c < 7)) continue;
 const bit = ((hash ^ (r * 31 + c * 17)) & (1 << ((r + c) % 8))) !== 0;
 if (bit) {
 ctx.fillRect(15 + c * 6.2, 15 + r * 6.2, 5, 5);
      }
    }
  }

  // Draw center UPI badge
 ctx.fillStyle = '#6366F1';
 ctx.beginPath();
 ctx.arc(size / 2, size / 2, 14, 0, Math.PI * 2);
 ctx.fill();
 ctx.fillStyle = '#FFFFFF';
 ctx.font = 'bold 12px sans-serif';
 ctx.textAlign = 'center';
 ctx.textBaseline = 'middle';
 ctx.fillText('स', size / 2, size / 2);

 document.getElementById('qr-amount-label').innerText = `Scan to Pay: ₹ ${amount.toFixed(2)}`;
}

function drawFinderPattern(ctx, x, y) {
 ctx.fillStyle = '#0F172A';
 ctx.fillRect(x, y, 35, 35);
 ctx.fillStyle = '#FFFFFF';
 ctx.fillRect(x + 5, y + 5, 25, 25);
 ctx.fillStyle = '#0F172A';
 ctx.fillRect(x + 10, y + 10, 15, 15);
}

// Render Live Transaction List
function renderLiveTransactions(txs) {
 const container = document.getElementById('live-tx-feed');
 if (!container) return;
 container.innerHTML = '';

 txs.slice(0, 15).forEach((tx, idx) => {
 const item = document.createElement('div');
 item.className = `tx-ticker-item ${idx === 0 ? 'new-tx' : ''}`;
    
 const isSuccess = tx.status === 'SUCCESS';
 item.innerHTML = `
      <div style="display: flex; align-items: center; gap: 10px;">
        <div style="width: 32px; height: 32px; border-radius: 50%; background: ${isSuccess ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)'}; display: flex; align-items: center; justify-content: center;">
          <i data-lucide="${isSuccess ? 'check-circle' : 'alert-circle'}" style="width: 18px; height: 18px; color: ${isSuccess ? 'var(--accent-emerald)' : 'var(--accent-rose)'};"></i>
        </div>
        <div>
          <div style="font-weight: 600; font-size: 13px;">${tx.payer_vpa || 'Customer UPI'} via ${tx.payer_app || 'UPI'}</div>
          <div style="font-size: 11px; color: var(--text-dim); font-family: monospace;">UTR: ${tx.utr}</div>
        </div>
      </div>
      <div style="text-align: right;">
        <div style="font-weight: 700; font-size: 14px; color: ${isSuccess ? 'var(--accent-emerald)' : 'var(--accent-rose)'};">
          ${isSuccess ? '+' : ''}₹${tx.amount.toFixed(0)}
        </div>
        <div style="font-size: 10px; color: var(--text-dim);">${new Date(tx.timestamp).toLocaleTimeString()}</div>
      </div>
    `;
 container.appendChild(item);
  });

 if (window.lucide) lucide.createIcons();
}

// Audio Soundbox Announce via Web Speech API
function triggerSoundboxAnnounce(amount, appName = "PhonePe") {
 const box = document.getElementById('soundbox-box');
 const screenAmt = document.getElementById('soundbox-screen-amt');
 const screenSub = document.getElementById('soundbox-screen-status');
 const lang = document.getElementById('voice-lang-select').value;

 screenAmt.innerText = `₹ ${amount.toFixed(2)}`;
 screenSub.innerText = `Verified on ${appName}`;

 box.classList.add('soundbox-speaking');

 let announcementText = "";
 if (lang === "hi-IN") {
 announcementText = `${appName} पर ${amount} रुपये प्राप्त हुए`;
  } else if (lang === "hinglish") {
 announcementText = `${appName} pe ${amount} rupaye mil gaye`;
  } else {
 announcementText = `Received ${amount} rupees on ${appName}`;
  }

 if ('speechSynthesis' in window) {
 window.speechSynthesis.cancel();
 const utterance = new SpeechSynthesisUtterance(announcementText);
 utterance.lang = lang === 'hi-IN' ? 'hi-IN' : 'en-IN';
 utterance.rate = 0.95;
 utterance.pitch = 1.05;

 utterance.onend = () => {
 box.classList.remove('soundbox-speaking');
    };
 utterance.onerror = () => {
 box.classList.remove('soundbox-speaking');
    };

 window.speechSynthesis.speak(utterance);
  } else {
 setTimeout(() => {
 box.classList.remove('soundbox-speaking');
    }, 2000);
  }
}

// Update Underwriting View
function updateUnderwritingView(data) {
 const uw = data.underwriting;
 const features = data.features;

 document.getElementById('underwrite-setu-score').innerText = uw.setu_score;
 const tierBadge = document.getElementById('underwrite-tier-badge');
 tierBadge.innerText = uw.risk_tier;
 tierBadge.className = `score-tier-badge ${getTierBadgeClass(uw.setu_score)}`;

 document.getElementById('underwrite-rec-text').innerText = uw.recommendation;
 document.getElementById('underwrite-tranche-name').innerText = uw.svanidhi_tranche;
 document.getElementById('underwrite-approved-limit').innerText = `₹ ${uw.approved_credit_limit.toLocaleString()}`;
 document.getElementById('underwrite-tenure').innerText = `${uw.tenure_months} Months`;
 document.getElementById('underwrite-daily-emi').innerText = `₹ ${uw.daily_micro_deduction}`;
 document.getElementById('underwrite-interest').innerText = uw.concessional_interest_rate;

  // Gauge Progress Arc (300 to 900 mapped to stroke-dashoffset)
 const scorePercent = (uw.setu_score - 300) / 600;
 const totalDash = 283;
 const targetOffset = totalDash * (1 - scorePercent);
 const arc = document.getElementById('gauge-arc-progress');
 if (arc) {
 arc.style.strokeDashoffset = targetOffset;
  }

  // Populate Positive Drivers
 const posContainer = document.getElementById('underwrite-positive-drivers');
 posContainer.innerHTML = '<div style="font-size:12px; font-weight:700; color:var(--accent-emerald); margin-bottom:6px;">POSITIVE CREDIT BOOSTERS (+):</div>';
  (uw.top_positive_drivers || []).forEach(d => {
 const card = document.createElement('div');
 card.className = 'driver-card';
 card.innerHTML = `
      <div class="driver-info">
        <h4>${d.display_name}</h4>
        <p>Observed value: <strong>${d.raw_value}</strong></p>
      </div>
      <div class="driver-pill pill-pos">+${d.points_impact} pts</div>
    `;
 posContainer.appendChild(card);
  });

  // Populate Negative Drivers
 const negContainer = document.getElementById('underwrite-negative-drivers');
 negContainer.innerHTML = '<div style="font-size:12px; font-weight:700; color:var(--accent-rose); margin-top:10px; margin-bottom:6px;">RISK FACTORS / IMPROVEMENT AREAS (-):</div>';
  (uw.top_negative_drivers || []).forEach(d => {
 const card = document.createElement('div');
 card.className = 'driver-card';
 card.innerHTML = `
      <div class="driver-info">
        <h4>${d.display_name}</h4>
        <p>Observed value: <strong>${d.raw_value}</strong></p>
      </div>
      <div class="driver-pill pill-neg">${d.points_impact} pts</div>
    `;
 negContainer.appendChild(card);
  });

  // Sync Sandbox Sliders
 if (features) {
 document.getElementById('slider-tenure').value = features.tenure_months;
 document.getElementById('val-tenure').innerText = features.tenure_months;

 document.getElementById('slider-days').value = features.active_days_per_month;
 document.getElementById('val-days').innerText = features.active_days_per_month;

 document.getElementById('slider-tx-count').value = features.daily_tx_count;
 document.getElementById('val-tx-count').innerText = features.daily_tx_count;

 document.getElementById('slider-vol').value = features.monthly_upi_volume;
 document.getElementById('val-vol').innerText = `₹${features.monthly_upi_volume.toLocaleString()}`;

 document.getElementById('slider-repeat').value = Math.round(features.repeat_customer_ratio * 100);
 document.getElementById('val-repeat').innerText = `${Math.round(features.repeat_customer_ratio * 100)}%`;

 document.getElementById('slider-volatility').value = Math.round(features.cashflow_volatility_cv * 100);
 document.getElementById('val-volatility').innerText = features.cashflow_volatility_cv;

 document.getElementById('select-soundbox').value = features.uses_audio_soundbox ? '1' : '0';
 document.getElementById('select-prior-tier').value = features.prior_svanidhi_tier || '0';
  }
}

// Update Ledger View
function updateLedgerView(data) {
 const ledger = data.ledger;
 if (!ledger) return;

 document.getElementById('ledger-total-income').innerText = `₹ ${ledger.total_income.toLocaleString()}`;
 document.getElementById('ledger-total-expense').innerText = `₹ ${ledger.total_expense.toLocaleString()}`;
 const net = ledger.net_profit;
 const netElem = document.getElementById('ledger-net-profit');
 netElem.innerText = `${net >= 0 ? '+' : ''}₹ ${net.toLocaleString()}`;
 netElem.style.color = net >= 0 ? 'var(--accent-emerald)' : 'var(--accent-rose)';
}

function getTierBadgeClass(score) {
 if (score >= 740) return 'tier-prime';
 if (score >= 640) return 'tier-near-prime';
 if (score >= 540) return 'tier-moderate';
 return 'tier-sub-prime';
}

// Render Cash Flow Forecast Chart
function renderCashflowChart() {
 const canvas = document.getElementById('cashflow-chart');
 if (!canvas || !STATE.activeMerchantData) return;

 const fc = STATE.activeMerchantData.cashflow_forecast;
 if (!fc) return;

 const labels = [];
 const historicalData = [];
 const forecastData = [];
 const lowerBounds = [];
 const upperBounds = [];

 fc.historical_data.forEach(h => {
 labels.push(h.day_name + ' ' + h.date.split('-').slice(1).join('/'));
 historicalData.push(h.revenue);
 forecastData.push(null);
 lowerBounds.push(null);
 upperBounds.push(null);
  });

  // Connect last point of historical to forecast
 const lastHist = historicalData[historicalData.length - 1];
 forecastData[historicalData.length - 1] = lastHist;
 lowerBounds[historicalData.length - 1] = lastHist;
 upperBounds[historicalData.length - 1] = lastHist;

 fc.forecast_data.forEach(f => {
 labels.push(f.day_name + ' ' + f.date.split('-').slice(1).join('/'));
 historicalData.push(null);
 forecastData.push(f.revenue);
 lowerBounds.push(f.lower_bound);
 upperBounds.push(f.upper_bound);
  });

 if (STATE.cashflowChart) {
 STATE.cashflowChart.destroy();
  }

 const ctx = canvas.getContext('2d');
 STATE.cashflowChart = new Chart(ctx, {
 type: 'line',
 data: {
 labels: labels,
 datasets: [
        {
 label: 'Historical Verified UPI Cashflow (₹)',
 data: historicalData,
 borderColor: '#10B981',
 backgroundColor: 'rgba(16, 185, 129, 0.1)',
 borderWidth: 2.5,
 tension: 0.3,
 pointRadius: 2
        },
        {
 label: 'AI 30-Day Projected Revenue (₹)',
 data: forecastData,
 borderColor: '#6366F1',
 borderDash: [5, 5],
 borderWidth: 2.5,
 tension: 0.3,
 pointRadius: 2
        },
        {
 label: '95% Upper Confidence Band',
 data: upperBounds,
 borderColor: 'transparent',
 backgroundColor: 'rgba(99, 102, 241, 0.15)',
 fill: '+1',
 pointRadius: 0
        },
        {
 label: '95% Lower Confidence Band',
 data: lowerBounds,
 borderColor: 'transparent',
 backgroundColor: 'rgba(99, 102, 241, 0.15)',
 fill: false,
 pointRadius: 0
        }
      ]
    },
 options: {
 responsive: true,
 maintainAspectRatio: false,
 plugins: {
 legend: {
 labels: { color: '#94A3B8', font: { family: 'Plus Jakarta Sans', size: 11 } }
        },
 tooltip: {
 backgroundColor: '#1E293B',
 titleColor: '#FFF',
 bodyColor: '#CBD5E1'
        }
      },
 scales: {
 x: {
 ticks: { color: '#64748B', font: { size: 10 }, maxTicksLimit: 12 },
 grid: { color: 'rgba(255,255,255,0.04)' }
        },
 y: {
 ticks: { color: '#64748B', font: { size: 10 } },
 grid: { color: 'rgba(255,255,255,0.04)' }
        }
      }
    }
  });

  // Update Summary cards
 document.getElementById('fc-projected-vol').innerText = `₹ ${fc.summary.projected_30d_turnover.toLocaleString()}`;
 document.getElementById('fc-safety-buffer').innerText = `₹ ${fc.summary.recommended_daily_working_buffer.toLocaleString()} / day`;
 document.getElementById('fc-safe-emi').innerText = `₹ ${fc.summary.safe_max_daily_emi.toLocaleString()} / day`;
}

// Load Macro Research Data & Charts
async function loadMacroResearchData() {
 try {
 const res = await fetch('/api/analytics/research-macro');
 const data = await res.json();

    // 1. RBI FI-Index Chart
 const rbiCtx = document.getElementById('rbi-chart').getContext('2d');
 const rbiData = data.rbi_fi_index_progression;
 STATE.rbiChart = new Chart(rbiCtx, {
 type: 'line',
 data: {
 labels: rbiData.map(d => d.year),
 datasets: [
          {
 label: 'Composite FI-Index',
 data: rbiData.map(d => d.composite_index),
 borderColor: '#6366F1',
 backgroundColor: '#6366F1',
 borderWidth: 3,
 pointRadius: 4
          },
          {
 label: 'Usage Sub-Index (UPI Driven)',
 data: rbiData.map(d => d.usage),
 borderColor: '#10B981',
 borderWidth: 2,
 borderDash: [4, 4],
 pointRadius: 3
          },
          {
 label: 'Access Sub-Index (Jan Dhan / PMJDY)',
 data: rbiData.map(d => d.access),
 borderColor: '#F59E0B',
 borderWidth: 2,
 pointRadius: 3
          }
        ]
      },
 options: {
 responsive: true,
 maintainAspectRatio: false,
 plugins: {
 legend: { labels: { color: '#94A3B8', font: { size: 10 } } }
        },
 scales: {
 x: { ticks: { color: '#64748B', font: { size: 10 } }, grid: { color: 'rgba(255,255,255,0.04)' } },
 y: { min: 30, max: 85, ticks: { color: '#64748B', font: { size: 10 } }, grid: { color: 'rgba(255,255,255,0.04)' } }
        }
      }
    });

    // 2. Gender Inclusion Gap Chart
 const genderCtx = document.getElementById('gender-chart').getContext('2d');
 const genderData = data.gender_digital_inclusion_gap;
 STATE.genderChart = new Chart(genderCtx, {
 type: 'bar',
 data: {
 labels: genderData.map(d => d.demographic),
 datasets: [{
 label: 'Digital Access Rate (%)',
 data: genderData.map(d => d.inclusion_pct),
 backgroundColor: genderData.map(d => d.color),
 borderRadius: 6
        }]
      },
 options: {
 responsive: true,
 maintainAspectRatio: false,
 plugins: {
 legend: { display: false }
        },
 scales: {
 x: { ticks: { color: '#94A3B8', font: { size: 10 } }, grid: { display: false } },
 y: { max: 100, ticks: { color: '#64748B', font: { size: 10 } }, grid: { color: 'rgba(255,255,255,0.04)' } }
        }
      }
    });

  } catch (err) {
 console.error("Failed to load macro research charts:", err);
  }
}

// Setup Interactive UI Event Listeners
function setupEventListeners() {
  
  // Custom Payment Amount input
 const amtInput = document.getElementById('custom-pay-amount');
 amtInput.addEventListener('input', (e) => {
 STATE.activeAmount = parseFloat(e.target.value) || 35;
 if (STATE.activeMerchantData) {
 drawMerchantQRCode(STATE.activeMerchantData.profile.upi_id, STATE.activeAmount);
    }
  });

  // Quick Amount Buttons
 document.querySelectorAll('.quick-amt-btn').forEach(btn => {
 btn.addEventListener('click', () => {
 const amt = parseFloat(btn.getAttribute('data-amt'));
 amtInput.value = amt;
 STATE.activeAmount = amt;
 if (STATE.activeMerchantData) {
 drawMerchantQRCode(STATE.activeMerchantData.profile.upi_id, STATE.activeAmount);
      }
    });
  });

  // Soundbox Test Audio button
 document.getElementById('btn-trigger-audio-test').addEventListener('click', () => {
 triggerSoundboxAnnounce(STATE.activeAmount, "PhonePe");
  });

  // Customer UPI Payment Scan simulation
 document.getElementById('btn-simulate-customer-scan').addEventListener('click', async () => {
 if (!STATE.activeMerchantData) return;
    
 triggerSoundboxAnnounce(STATE.activeAmount, "GooglePay");
    
    // Simulate transaction submission
 const res = await fetch('/api/simulate/burst', {
 method: 'POST',
 headers: { 'Content-Type': 'application/json' },
 body: JSON.stringify({
 merchant_id: STATE.activeMerchantId,
 num_transactions: 1,
 inject_fraud: false
      })
    });
    
 const result = await res.json();
 await selectMerchant(STATE.activeMerchantId);
  });

  // Voice Ledger Record & Parse
 document.getElementById('btn-submit-voice-ledger').addEventListener('click', async () => {
 const textInput = document.getElementById('voice-input-text');
 const text = textInput.value.trim();
 if (!text) return;

 try {
 const res = await fetch('/api/voice-ledger/parse', {
 method: 'POST',
 headers: { 'Content-Type': 'application/json' },
 body: JSON.stringify({
 merchant_id: STATE.activeMerchantId,
 text_transcript: text
        })
      });
 const data = await res.json();
 if (data.entry) {
 textInput.value = '';
 await selectMerchant(STATE.activeMerchantId);
      }
    } catch (err) {
 console.error("Voice ledger parse error:", err);
    }
  });

  // Sample prompt clicks
 document.querySelectorAll('.sample-prompt-chip').forEach(chip => {
 chip.addEventListener('click', () => {
 const clean = chip.innerText.replace(/"/g, '');
 document.getElementById('voice-input-text').value = clean;
    });
  });

  // Speech Recognition Mic button for voice ledger
 const micBtn = document.getElementById('btn-mic-record');
 if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
 const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
 const recognizer = new SpeechRecognition();
 recognizer.lang = 'hi-IN';
 recognizer.continuous = false;

 micBtn.addEventListener('click', () => {
 micBtn.style.background = '#EF4444';
 recognizer.start();
    });

 recognizer.onresult = (event) => {
 const transcript = event.results[0][0].transcript;
 document.getElementById('voice-input-text').value = transcript;
 micBtn.style.background = '';
    };

 recognizer.onerror = () => {
 micBtn.style.background = '';
    };
 recognizer.onend = () => {
 micBtn.style.background = '';
    };
  }

  // Interactive Sandbox Sliders
 const sliders = [
    { id: 'slider-tenure', label: 'val-tenure', suffix: ' mos' },
    { id: 'slider-days', label: 'val-days', suffix: ' days' },
    { id: 'slider-tx-count', label: 'val-tx-count', suffix: ' tx/day' },
    { id: 'slider-vol', label: 'val-vol', prefix: '₹' },
    { id: 'slider-repeat', label: 'val-repeat', suffix: '%' },
    { id: 'slider-volatility', label: 'val-volatility', factor: 0.01 }
  ];

 sliders.forEach(s => {
 const el = document.getElementById(s.id);
 if (!el) return;
 el.addEventListener('input', () => {
 const val = parseFloat(el.value);
 const display = document.getElementById(s.label);
 if (s.prefix) display.innerText = `${s.prefix}${val.toLocaleString()}`;
 else if (s.suffix) display.innerText = `${val}${s.suffix}`;
 else if (s.factor) display.innerText = (val * s.factor).toFixed(2);
 else display.innerText = val;
    });
  });

  // Recompute Underwriting Sandbox Button
 document.getElementById('btn-recompute-underwrite').addEventListener('click', async () => {
 const payload = {
 merchant_id: STATE.activeMerchantId,
 tenure_months: parseFloat(document.getElementById('slider-tenure').value),
 active_days_per_month: parseFloat(document.getElementById('slider-days').value),
 daily_tx_count: parseFloat(document.getElementById('slider-tx-count').value),
 avg_ticket_size: Math.round(parseFloat(document.getElementById('slider-vol').value) / (parseFloat(document.getElementById('slider-days').value) * parseFloat(document.getElementById('slider-tx-count').value))),
 monthly_upi_volume: parseFloat(document.getElementById('slider-vol').value),
 repeat_customer_ratio: parseFloat(document.getElementById('slider-repeat').value) / 100.0,
 cashflow_volatility_cv: parseFloat(document.getElementById('slider-volatility').value) / 100.0,
 uses_audio_soundbox: parseInt(document.getElementById('select-soundbox').value),
 failed_dispute_rate: 0.4,
 prior_svanidhi_tier: parseInt(document.getElementById('select-prior-tier').value),
 on_time_repayment_ratio: 0.98
    };

 try {
 const res = await fetch('/api/underwrite', {
 method: 'POST',
 headers: { 'Content-Type': 'application/json' },
 body: JSON.stringify(payload)
      });
 const result = await res.json();
 updateUnderwritingView({ underwriting: result, features: payload });

      // Trigger Confetti if Prime
 if (result.setu_score >= 720 && window.confetti) {
 confetti({ particleCount: 80, spread: 60, origin: { y: 0.6 } });
      }
    } catch (err) {
 console.error("Underwrite calculation error:", err);
    }
  });

  // Anti-Fraud Verification Button
 document.getElementById('btn-run-fraud-check').addEventListener('click', async () => {
 const utr = document.getElementById('fraud-input-utr').value.trim();
 const amt = parseFloat(document.getElementById('fraud-input-amt').value) || 0;
 const vpa = document.getElementById('fraud-input-vpa').value.trim();
 const appName = document.getElementById('fraud-input-app').value;

 const fontMismatch = document.getElementById('check-font-mismatch').checked;
 const futureTime = document.getElementById('check-future-time').checked;
 const isReplay = document.getElementById('check-replay-utr').checked;

 let timestampStr = new Date().toISOString();
 if (futureTime) {
 const future = new Date(Date.now() + 45 * 60 * 1000);
 timestampStr = future.toISOString();
    }

 const payload = {
 utr: isReplay ? "499999999999" : utr,
 amount: amt,
 merchant_vpa: STATE.activeMerchantData ? STATE.activeMerchantData.profile.upi_id : "rameshchai@okaxis",
 timestamp_str: timestampStr,
 payer_vpa: vpa,
 app_reported: appName,
 screenshot_metadata: {
 font_mismatch_detected: fontMismatch,
 has_pixel_artifacts: fontMismatch || appName.includes('Fake')
      }
    };

 try {
 const res = await fetch('/api/fraud-check', {
 method: 'POST',
 headers: { 'Content-Type': 'application/json' },
 body: JSON.stringify(payload)
      });
 const result = await res.json();
 renderFraudResult(result);
    } catch (err) {
 console.error("Fraud check error:", err);
    }
  });

  // Load Fraud Attack Scenario
 document.getElementById('btn-load-fraud-scenario').addEventListener('click', () => {
 document.getElementById('fraud-input-utr').value = '499999999999';
 document.getElementById('fraud-input-amt').value = '850';
 document.getElementById('fraud-input-app').value = 'FakeApk_Spoof';
 document.getElementById('fraud-input-vpa').value = 'scammer@fakeupi';
 document.getElementById('check-font-mismatch').checked = true;
 document.getElementById('check-future-time').checked = true;
  });

  // Live Burst Simulation Buttons
 document.getElementById('btn-run-burst-10').addEventListener('click', () => runSimulationBurst(10, false));
 document.getElementById('btn-run-burst-25').addEventListener('click', () => runSimulationBurst(25, false));
 document.getElementById('btn-run-burst-with-fraud').addEventListener('click', () => runSimulationBurst(15, true));

  // Sanction Letter Modal trigger
 document.getElementById('btn-generate-sanction-letter').addEventListener('click', () => {
 if (!STATE.activeMerchantData) return;
 const profile = STATE.activeMerchantData.profile;
 const uw = STATE.activeMerchantData.underwriting;

 document.getElementById('cert-vendor-name').innerText = profile.name;
 document.getElementById('cert-vendor-upi').innerText = profile.upi_id;
 document.getElementById('cert-score').innerText = `${uw.setu_score} (${uw.risk_tier.split(' ')[0]})`;
 document.getElementById('cert-sanction-amount').innerText = `₹ ${uw.approved_credit_limit.toLocaleString()}.00`;
 document.getElementById('cert-tranche-tier').innerText = uw.svanidhi_tranche;
 document.getElementById('cert-daily-sweep').innerText = `₹ ${uw.daily_micro_deduction} / day`;

 document.getElementById('sanction-modal').classList.add('open');

 if (window.confetti) {
 confetti({ particleCount: 120, spread: 80, origin: { y: 0.5 } });
    }
  });

 document.getElementById('btn-close-sanction-modal').addEventListener('click', () => {
 document.getElementById('sanction-modal').classList.remove('open');
  });
}

function renderFraudResult(res) {
 const isBlocked = res.status.includes('BLOCKED');
 const banner = document.getElementById('fraud-status-banner');
 const statusText = document.getElementById('fraud-status-text');
 const actionText = document.getElementById('fraud-action-text');
 const scoreText = document.getElementById('fraud-risk-score');
 const flagsList = document.getElementById('fraud-flags-list');

 if (isBlocked) {
 banner.style.background = 'rgba(239, 68, 68, 0.15)';
 banner.style.borderColor = 'rgba(239, 68, 68, 0.4)';
 statusText.innerText = 'ALERT: PAYMENT FRAUD DETECTED';
 statusText.style.color = 'var(--accent-rose)';
 scoreText.innerText = `${res.risk_score} / 100 (HIGH RISK)`;
 scoreText.style.color = 'var(--accent-rose)';
  } else {
 banner.style.background = 'rgba(16, 185, 129, 0.15)';
 banner.style.borderColor = 'rgba(16, 185, 129, 0.4)';
 statusText.innerText = 'PAYMENT VERIFIED GENUINE';
 statusText.style.color = 'var(--accent-emerald)';
 scoreText.innerText = `${res.risk_score} / 100 (SAFE)`;
 scoreText.style.color = 'var(--accent-emerald)';
  }

 actionText.innerText = res.action_advice;

 flagsList.innerHTML = '';
 if (res.flags.length === 0) {
 flagsList.innerHTML = '<div style="font-size:13px; color:#10B981; padding:8px;"> All security integrity checks passed. Genuine bank transaction.</div>';
  } else {
 res.flags.forEach(f => {
 const item = document.createElement('div');
 item.style.fontSize = '13px';
 item.style.padding = '8px 12px';
 item.style.borderRadius = '6px';
 item.style.marginBottom = '6px';
 item.style.background = f.severity === 'CRITICAL' ? 'rgba(239,68,68,0.15)' : 'rgba(245,158,11,0.15)';
 item.style.color = f.severity === 'CRITICAL' ? '#FCA5A5' : '#FCD34D';
 item.innerHTML = `<strong>[${f.severity}] ${f.code}:</strong> ${f.message}`;
 flagsList.appendChild(item);
    });
  }
}

// Run Simulation Burst
async function runSimulationBurst(count, injectFraud) {
 const statusBox = document.getElementById('sim-status-box');
 statusBox.style.display = 'block';
 statusBox.innerHTML = `Simulating high-traffic stream: processing ${count} UPI transactions...`;

 try {
 const res = await fetch('/api/simulate/burst', {
 method: 'POST',
 headers: { 'Content-Type': 'application/json' },
 body: JSON.stringify({
 merchant_id: STATE.activeMerchantId,
 num_transactions: count,
 inject_fraud: injectFraud
      })
    });
 const data = await res.json();

 statusBox.innerHTML = `Generated <strong>${data.simulated_count} live transactions</strong> (+₹${data.added_turnover.toLocaleString()} turnover). Recalculated SetuScore: <strong>${data.new_setu_score} (${data.new_risk_tier})</strong>`;

    // Render burst log
 const logContainer = document.getElementById('burst-tx-log');
 logContainer.innerHTML = '';
 data.transactions.forEach(tx => {
 const el = document.createElement('div');
 el.className = 'tx-ticker-item';
 const isFraud = tx.is_fraud_detected;
 el.innerHTML = `
        <div>
          <strong style="color:${isFraud ? 'var(--accent-rose)' : 'var(--accent-emerald)'};">[${tx.status}]</strong> ${tx.payer_vpa} (${tx.payer_app}) - UTR: ${tx.utr}
        </div>
        <div style="font-weight:700;">₹${tx.amount}</div>
      `;
 logContainer.appendChild(el);
    });

    // Soundbox announcement for successful payments
 if (!injectFraud) {
 triggerSoundboxAnnounce(data.transactions[0].amount, data.transactions[0].payer_app);
    }

    // Refresh state
 await selectMerchant(STATE.activeMerchantId);

  } catch (err) {
 console.error("Simulation burst error:", err);
  }
}
