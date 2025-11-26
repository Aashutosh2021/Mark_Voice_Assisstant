// Global variables
let selectedVersion = null;
let selectedVariant = null;
let downloadUrl = null;
let downloadInProgress = false;
let paymentVerified = false;

// Loading Animation Setup
function initializeLoadingScreen() {
    const loadingScreen = document.getElementById('loading-screen');
    const loadPercentElement = document.getElementById('load-percent');
    let currentPercent = 0;
    
    // Create audio context for sound effects - will be initialized on first user interaction
    let audioContext = null;
    
    // Initialize audio context on first interaction
    function initAudioContext() {
        if (!audioContext) {
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
        }
        return audioContext;
    }
    
    // Resume audio context if suspended
    function resumeAudioContext() {
        const ctx = initAudioContext();
        if (ctx.state === 'suspended') {
            ctx.resume().then(() => {
                console.log('Audio context resumed');
            });
        }
    }
    
    // Force audio context to resume with user gesture
    document.addEventListener('click', resumeAudioContext, { once: true });
    document.addEventListener('touchstart', resumeAudioContext, { once: true });
    document.addEventListener('keydown', resumeAudioContext, { once: true });
    
    // Play boot sequence sound
    function playBootSound() {
        try {
            const ctx = initAudioContext();
            if (!ctx) return;
            
            const now = ctx.currentTime;
            const oscillator = ctx.createOscillator();
            const gainNode = ctx.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(ctx.destination);
            
            oscillator.frequency.setValueAtTime(800, now);
            oscillator.frequency.exponentialRampToValueAtTime(200, now + 0.3);
            
            gainNode.gain.setValueAtTime(0.1, now);
            gainNode.gain.exponentialRampToValueAtTime(0.01, now + 0.3);
            
            oscillator.start(now);
            oscillator.stop(now + 0.3);
        } catch (e) {
            console.log('Audio playback not available:', e);
        }
    }
    
    // Play beep sound
    function playBeep() {
        try {
            const ctx = initAudioContext();
            if (!ctx) return;
            
            const now = ctx.currentTime;
            const oscillator = ctx.createOscillator();
            const gainNode = ctx.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(ctx.destination);
            
            oscillator.frequency.setValueAtTime(600, now);
            gainNode.gain.setValueAtTime(0.05, now);
            gainNode.gain.exponentialRampToValueAtTime(0.01, now + 0.15);
            
            oscillator.start(now);
            oscillator.stop(now + 0.15);
        } catch (e) {
            console.log('Audio playback not available:', e);
        }
    }
    
    // Play completion sound
    function playCompletionSound() {
        try {
            const ctx = initAudioContext();
            if (!ctx) return;
            
            const now = ctx.currentTime;
            const notes = [523.25, 659.25, 783.99]; // C5, E5, G5 chord
            
            notes.forEach((frequency, index) => {
                const oscillator = ctx.createOscillator();
                const gainNode = ctx.createGain();
                
                oscillator.connect(gainNode);
                gainNode.connect(ctx.destination);
                
                oscillator.frequency.setValueAtTime(frequency, now);
                gainNode.gain.setValueAtTime(0.05, now);
                gainNode.gain.exponentialRampToValueAtTime(0.01, now + 0.5);
                
                oscillator.start(now + index * 0.05);
                oscillator.stop(now + 0.5);
            });
        } catch (e) {
            console.log('Audio playback not available:', e);
        }
    }
    
    // Play initial boot sound
    playBootSound();
    
    // Simulate percentage loading
    const loadingInterval = setInterval(() => {
        currentPercent += Math.random() * 40;
        if (currentPercent > 100) currentPercent = 100;
        
        loadPercentElement.textContent = Math.floor(currentPercent);
        
        // Play beep at certain intervals
        if (Math.floor(currentPercent) % 20 === 0 && currentPercent !== 0) {
            playBeep();
        }
    }, 300);
    
    // Complete loading after 3 seconds
    setTimeout(() => {
        clearInterval(loadingInterval);
        currentPercent = 100;
        loadPercentElement.textContent = '100';
        playCompletionSound();
        
        // Fade out loading screen
        setTimeout(() => {
            loadingScreen.classList.add('fade-out');
            
            // Show main content
            setTimeout(() => {
                loadingScreen.style.display = 'none';
                showScreen('welcome-screen');
            }, 1000);
        }, 500);
    }, 3000);
}

// Updated Data Structure for MARK AI Rebranding
const versions = {
    mark1: {
        base: {
            title: "MARK AI 1 Core",
            subtitle: "Essential Windows Neural Assistant",
            features: [
                {icon: "🗣️", title: "Neural Conversation", desc: "Natural language processing for realistic human-like interaction"},
                {icon: "🔍", title: "Deep File Retrieval", desc: "Locate data points across local drives via voice"},
                {icon: "⏱️", title: "Task Automation", desc: "Streamline workflows with preset command execution"},
                {icon: "🌐", title: "Web Navigation", desc: "Voice-controlled internet research and data gathering"},
                {icon: "📅", title: "Temporal Management", desc: "Calendar synchronization and advanced reminders"}
            ],
            videos: [
                "https://www.youtube.com/embed/xxxxxxxxxxx",  
            ],
            // Filename kept consistent with backend expectations or updated if requested
            // Display logic handles the UI text.
            downloadFile: "mark_ai_windows_core_v3.0.exe", 
            fileSize: "xxx.xx MB",
            price: 19900, // ₹199 in paise
            downloadUrl: "download url"
        },
        pro: {
            title: "MARK AI 1 Pro",
            subtitle: "Advanced Windows System Controller",
            features: [
                {icon: "🖥️", title: "System Override", desc: "Direct voice control over Windows OS functions"},
                {icon: "🤖", title: "Logic Automation", desc: "Complex workflow creation via natural language"},
                {icon: "📊", title: "Data Analytics", desc: "Automated reporting and productivity insight generation"},
                {icon: "🔍", title: "Omni-Search", desc: "Deep content analysis across file systems"},
                {icon: "⌨️", title: "Input Emulation", desc: "AI-assisted keyboard and mouse control sequences"},
                {icon: "🌍", title: "Polyglot Mode", desc: "Real-time multi-language processing and translation"}
            ],
            videos: [
                "https://www.youtube.com/embed/xxxxxxxx",  
            ],
            downloadFile: "mark_ai_windows_pro_v3.0.exe",
            fileSize: "xxx.xx MB",
            price: 39900, // ₹399 in paise
            downloadUrl: "download url"
        },
        ultra: {
            title: "MARK AI 1 Ultra",
            subtitle: "Ultimate System Integration Solution",
            features: [
                {icon: "🖥️", title: "Total OS Dominion", desc: "Unrestricted control over all Windows subsystems"},
                {icon: "🤖", title: "Generative Automation", desc: "Self-improving workflow scripts based on usage patterns"},
                {icon: "🔍", title: "Neural Organization", desc: "Auto-sorting of files, emails, and unstructured data"},
                {icon: "📊", title: "Executive Suite", desc: "Full-scale data presentation and automated business intelligence"},
                {icon: "⌨️", title: "Predictive Input", desc: "Context-aware input prediction and automation"},
                {icon: "🔒", title: "Sentinel Mode", desc: "Real-time threat monitoring and system integrity defense"},
                {icon: "🚀", title: "Priority Uplink", desc: "Dedicated support channel for ultra operatives"},
                {icon: "🔄", title: "Perpetual Updates", desc: "Lifetime access to all future neural modules"}
            ],
            videos: [
                "https://www.youtube.com/embed/xxxxxxxx",  
            ],
            downloadFile: "mark_ai_windows_ultra_v3.0.exe",
            fileSize: "xxx.xx MB",
            price: 59900, // ₹599 in paise
            downloadUrl: "download url"
        }
    }
};

// Function to count remaining access keys (simulated)
function getRemainingKeysCount() {
    // Return a random number between 15-25 to simulate available keys
    return Math.floor(Math.random() * 11) + 15;
}

// Function to update key status display
function updateKeyStatus() {
    try {
        const mark1Count = getRemainingKeysCount();
        
        const mark1Status = document.getElementById('mark1-key-status');
        if (mark1Status) {
            const countElement = mark1Status.querySelector('.key-count');
            countElement.textContent = mark1Count;
            
            if (mark1Count > 10) {
                mark1Status.classList.add('keys-available');
                mark1Status.classList.remove('keys-low', 'keys-none');
            } else if (mark1Count > 0) {
                mark1Status.classList.add('keys-low');
                mark1Status.classList.remove('keys-available', 'keys-none');
            } else {
                mark1Status.classList.add('keys-none');
                mark1Status.classList.remove('keys-available', 'keys-low');
            }
        }
        
        // Update variant key counts if on variant selector screen
        if (document.getElementById('variant-selector').classList.contains('active')) {
            const variantCards = document.querySelectorAll('.variant-card');
            variantCards.forEach(card => {
                const count = getRemainingKeysCount();
                const countElement = card.querySelector('.key-count');
                countElement.textContent = count;
                
                // Update status colors
                const statusElement = card.querySelector('.key-status');
                if (count > 10) {
                    statusElement.classList.add('keys-available');
                    statusElement.classList.remove('keys-low', 'keys-none');
                } else if (count > 0) {
                    statusElement.classList.add('keys-low');
                    statusElement.classList.remove('keys-available', 'keys-none');
                } else {
                    statusElement.classList.add('keys-none');
                    statusElement.classList.remove('keys-available', 'keys-low');
                }
            });
        }
    } catch (error) {
        console.error('Error updating key status:', error);
        document.querySelectorAll('.key-count').forEach(element => {
            element.textContent = 'Err';
        });
    }
}

// Initialize particles - UPGRADED VISUALS
function initParticles() {
    const container = document.getElementById('particle-background');
    if (!container) return;
    
    container.innerHTML = ''; // Clear existing
    const particleCount = window.innerWidth < 768 ? 20 : 40;
    
    for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        
        // Size variation
        const size = Math.random() * 3 + 1;
        particle.style.width = `${size}px`;
        particle.style.height = `${size}px`;
        
        // Random Position
        particle.style.left = `${Math.random() * 100}%`;
        particle.style.top = `${Math.random() * 100}%`;
        
        // Animation params
        const duration = Math.random() * 15 + 10;
        particle.style.animationDuration = `${duration}s`;
        particle.style.animationDelay = `${Math.random() * 5}s`;
        particle.style.opacity = Math.random() * 0.5 + 0.2;
        
        container.appendChild(particle);
    }
}

// Show notification
function showNotification(message, type = 'info') {
    const notification = document.getElementById('notification');
    const icon = document.getElementById('notification-icon');
    const msg = document.getElementById('notification-message');
    
    // Reset classes
    notification.className = 'notification-panel';
    icon.innerHTML = '';

    switch(type) {
        case 'success':
            icon.innerHTML = '<i class="fas fa-check-circle" style="color: var(--success)"></i>';
            notification.classList.add('success');
            break;
        case 'warning':
            icon.innerHTML = '<i class="fas fa-exclamation-triangle" style="color: var(--warning)"></i>';
            notification.classList.add('warning');
            break;
        case 'error':
            icon.innerHTML = '<i class="fas fa-times-circle" style="color: var(--error)"></i>';
            notification.classList.add('error');
            break;
        default:
            icon.innerHTML = '<i class="fas fa-info-circle" style="color: var(--neon-cyan)"></i>';
    }
    
    msg.textContent = message;
    notification.classList.add('show');
    
    setTimeout(() => {
        notification.classList.remove('show');
    }, 5000);
}

// Show screen function
function showScreen(screenId) {
    document.querySelectorAll('.screen').forEach(screen => {
        screen.classList.remove('active');
    });
    document.getElementById(screenId).classList.add('active');
    
    if (screenId === 'version-selector') {
        updateKeyStatus();
    } else if (screenId === 'variant-selector') {
        updateKeyStatus();
    }
    
    // Update document title based on screen - REBRANDED
    if (screenId === 'welcome-screen') {
        document.title = "MARK AI - The Future of Personal Assistant";
    } else if (screenId === 'version-selector') {
        document.title = "MARK AI - Select Your Version";
    } else if (screenId === 'variant-selector') {
        document.title = "MARK AI - Select Edition";
    } else if (screenId === 'details-screen') {
        document.title = `MARK AI - ${selectedVariant ? versions.mark1[selectedVariant].title : 'System Details'}`;
    } else if (screenId === 'download-screen') {
        document.title = "MARK AI - Download";
    } else if (screenId === 'whatsapp-screen') {
        document.title = "MARK AI - Secure Contact";
    }
}

// Select version function
function selectVersion(version) {
    document.querySelectorAll('.version-card').forEach(card => {
        card.classList.remove('selected');
    });
    
    // Safely add class if event target exists
    if(event && event.target) {
       const card = event.target.closest('.version-card');
       if(card) card.classList.add('selected');
    }
    
    selectedVersion = version;
    
    if (version === 'mark1') {
        // For Windows version, show variant selector
        showScreen('variant-selector');
        return;
    }
    
    // For Android version (if exists), enable continue button
    const continueBtn = document.getElementById('continue-btn');
    if(continueBtn) {
        continueBtn.style.display = 'block';
        continueBtn.disabled = false;
    }
}

// Select variant function
function selectVariant(variant) {
    document.querySelectorAll('.variant-card').forEach(card => {
        card.classList.remove('selected');
    });
    
    if(event && event.target) {
        const card = event.target.closest('.variant-card');
        if(card) card.classList.add('selected');
    }
    
    selectedVariant = variant;
    
    const continueBtn = document.getElementById('variant-continue-btn');
    continueBtn.style.display = 'block';
    continueBtn.disabled = false;
}

// Go back from details function
function goBackFromDetails() {
    if (selectedVersion === 'mark1') {
        showScreen('variant-selector');
    } else {
        showScreen('version-selector');
    }
}

// Show version details function
function showVersionDetails() {
    if (!selectedVersion) {
        showNotification('System Error: No Version Selected', 'error');
        return;
    }
    
    let version;
    if (selectedVersion === 'mark1' && selectedVariant) {
        version = versions.mark1[selectedVariant];
    } else {
        showNotification('System Error: No Variant Selected', 'error');
        return;
    }
    
    document.getElementById('details-title').textContent = version.title;
    document.getElementById('details-subtitle').textContent = version.subtitle;
    
    // Populate features
    const featuresGrid = document.getElementById('features-grid');
    featuresGrid.innerHTML = '';
    version.features.forEach(feature => {
        const featureCard = document.createElement('div');
        featureCard.className = 'feature-card';
        featureCard.innerHTML = `
            <div class="feature-icon">${feature.icon}</div>
            <div class="feature-title">${feature.title}</div>
            <div class="feature-description">${feature.desc}</div>
        `;
        featuresGrid.appendChild(featureCard);
    });
    
    // Populate videos
    const videosGrid = document.getElementById('videos-grid');
    videosGrid.innerHTML = '';
    version.videos.forEach(videoUrl => {
        const videoContainer = document.createElement('div');
        videoContainer.className = 'video-container';
        videoContainer.innerHTML = `<iframe src="${videoUrl}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>`;
        videosGrid.appendChild(videoContainer);
    });
    
    showScreen('details-screen');
}

// Handle payment function
async function handlePayment() {
    return new Promise((resolve, reject) => {
        let version;
        if (selectedVersion === 'mark1' && selectedVariant) {
            version = versions.mark1[selectedVariant];
        } else {
            reject(new Error('Invalid selection parameter'));
            return;
        }
        
        const options = {
            key: 'YOUR_RAZORPAY_KEY_HERE',
            amount: version.price,
            currency: 'INR',
            name: "MARK AI", // REBRANDED
            description: `License Acquisition: ${version.title}`,
            handler: function (response) {
                console.log('Payment Success:', response);
                showNotification('Transaction Authorized.', 'success');
                paymentVerified = true;
                resolve(response);
            },
            prefill: {
                name: "MARK AI User",
                email: "user@markai.sys",
                contact: "9000000000"
            },
            theme: {
                color: "#00f3ff", // Neon Cyan
                backdrop_color: "#050510"
            },
            method: {
                upi: true,
                card: true,
                netbanking: true,
                wallet: true
            },
            config: {
                display: {
                    blocks: {
                        utib: {
                            name: 'UPI Interface',
                            instruments: [{ method: 'upi' }]
                        },
                        other: {
                            name: 'Alternative Channels',
                            instruments: [
                                { method: 'card' },
                                { method: 'netbanking' },
                                { method: 'wallet' }
                            ]
                        }
                    },
                    sequence: ['block.utib', 'block.other'],
                    preferences: { show_default_blocks: true }
                }
            },
            modal: {
                ondismiss: function () {
                    showNotification('Transaction Aborted.', 'warning');
                    reject(new Error('User cancelled transaction'));
                }
            },
            retry: { enabled: true, max_count: 3 }
        };

        const rzp = new Razorpay(options);
        rzp.on('payment.failed', function (response) {
            console.error('Payment failed:', response.error);
            showNotification(`Transaction Failed: ${response.error.description}`, 'error');
            reject(new Error(response.error.description));
        });

        rzp.open();
    });
}

// Get Mark function
async function getMark() {
    try {
        // First handle payment
        await handlePayment();
        
        if (!paymentVerified) {
            showNotification('Verification Failure. Access Denied.', 'error');
            return;
        }
        
        // Show congratulations screen with WhatsApp option
        showScreen('whatsapp-screen');
        
    } catch (error) {
        console.error('Error in getMark:', error);
        // Error is usually handled in handlePayment notifications
    }
}

// Open WhatsApp function
function openWhatsApp() {
    let version;
    if (selectedVersion === 'mark' && selectedVariant) {
        version = versions.mark1[selectedVariant];
    }
    
    // Create WhatsApp message - REBRANDED
    const message = `System Uplink Initiated. I have acquired license for ${version.title}. Requesting activation key and download directives.`;
    const phoneNumber = "919798022573"; 
    
    // Open WhatsApp
    window.open(`https://wa.me/${phoneNumber}?text=${encodeURIComponent(message)}`, '_blank');
}

// Download Mark function
function downloadMark() {
    if (!downloadUrl) {
        showNotification('Download Link Unavailable.', 'error');
        return;
    }
    
    if (downloadInProgress) {
        showNotification('Transfer Already In Progress.', 'warning');
        return;
    }
    
    downloadInProgress = true;
    const progressContainer = document.getElementById('progress-container');
    const progressBar = document.getElementById('progress-bar');
    const downloadBtn = document.getElementById('download-btn');
    const fileSizeEl = document.getElementById('file-size');
    const fileVerEl = document.getElementById('file-version');
    
    let version;
    if (selectedVersion === 'mark1' && selectedVariant) {
        version = versions.mark1[selectedVariant];
    }
    
    // Update Meta Info
    fileSizeEl.textContent = version.fileSize;
    fileVerEl.textContent = "3.0";

    // Show progress bar
    progressContainer.style.display = 'block';
    downloadBtn.disabled = true;
    downloadBtn.innerHTML = '<i class="fas fa-spinner fa-spin" style="margin-right: 15px;"></i>INITIALIZING...';
    
    // Create a download link element
    const link = document.createElement('a');
    link.href = version.downloadUrl; // Use the version specific URL
    link.download = version.downloadFile;
    link.style.display = 'none';
    document.body.appendChild(link);
    
    // Simulate download progress
    let progress = 0;
    const progressInterval = setInterval(() => {
        progress += Math.random() * 15;
        if (progress > 100) progress = 100;
        
        progressBar.style.width = progress + '%';
        
        if (progress >= 100) {
            clearInterval(progressInterval);
            
            // Trigger the download
            link.click();
            
            // Clean up the link element
            document.body.removeChild(link);
            
            downloadBtn.innerHTML = '<i class="fas fa-check" style="margin-right: 15px;"></i>TRANSFER COMPLETE';
            showNotification('Data Transfer Successful. Check local storage.', 'success');
            
            setTimeout(() => {
                downloadInProgress = false;
                downloadBtn.disabled = false;
                downloadBtn.innerHTML = '<i class="fas fa-download" style="margin-right: 15px;"></i>RE-INITIATE DOWNLOAD';
                progressContainer.style.display = 'none';
                progressBar.style.width = '0%';
            }, 3000);
        }
    }, 200);
}

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    // Start loading animation
    initializeLoadingScreen();
    
    // Enable audio on any user interaction (click, touch, key press)
    function enableAudio() {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        if (audioContext.state === 'suspended') {
            audioContext.resume().then(() => {
                console.log('Audio context resumed on user interaction');
            });
        }
        document.removeEventListener('click', enableAudio);
        document.removeEventListener('touchstart', enableAudio);
        document.removeEventListener('keydown', enableAudio);
    }
    
    document.addEventListener('click', enableAudio);
    document.addEventListener('touchstart', enableAudio);
    document.addEventListener('keydown', enableAudio);
    
    initParticles();
    
    // Mobile menu toggle
    const navbarToggle = document.getElementById('navbar-toggle');
    const navbarMenu = document.querySelector('.navbar-menu');
    
    if (navbarToggle) {
        navbarToggle.addEventListener('click', function() {
            navbarMenu.classList.toggle('active');
            navbarToggle.classList.toggle('active');
        });
    }
    
    // Close mobile menu when clicking outside
    document.addEventListener('click', function(event) {
        if (navbarToggle && navbarMenu && !navbarToggle.contains(event.target) && !navbarMenu.contains(event.target)) {
            navbarMenu.classList.remove('active');
            navbarToggle.classList.remove('active');
        }
    });
    
    // Event listeners for buttons
    // Check if elements exist before adding listeners to prevent console errors
    const bindClick = (id, func) => {
        const el = document.getElementById(id);
        if(el) el.addEventListener('click', func);
    };

    bindClick('welcome-continue-btn', () => showScreen('version-selector'));
    bindClick('mark1-card', () => selectVersion('mark1'));
    bindClick('continue-btn', showVersionDetails);
    bindClick('variant-back-btn', () => showScreen('version-selector'));
    bindClick('base-variant', () => selectVariant('base'));
    bindClick('pro-variant', () => selectVariant('pro'));
    bindClick('ultra-variant', () => selectVariant('ultra'));
    bindClick('variant-continue-btn', showVersionDetails);
    bindClick('details-back-btn', goBackFromDetails);
    bindClick('get-Mark-btn', getMark);
    bindClick('whatsapp-btn', openWhatsApp);
    bindClick('whatsapp-back-btn', () => showScreen('details-screen'));
    bindClick('download-btn', downloadMark);
    
    // Load key status on page load
    updateKeyStatus();
});

// Make functions global
window.showScreen = showScreen;
window.selectVersion = selectVersion;
window.selectVariant = selectVariant;
window.goBackFromDetails = goBackFromDetails;
window.showVersionDetails = showVersionDetails;
window.getMark = getMark;
window.openWhatsApp = openWhatsApp;
window.downloadMark = downloadMark;