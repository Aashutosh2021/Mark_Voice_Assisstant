
// Global variables
let selectedVersion = null;
let selectedVariant = null;
let downloadUrl = null;
let downloadInProgress = false;
let paymentVerified = false;

const versions = {
    nova2: {
        base: {
            title: "Nova 3.0 Base",
            subtitle: "Basic Windows AI assistant",
            features: [
                {icon: "🗣️", title: "Human-like conversation", desc: "Natural language processing for realistic conversations"},
                {icon: "🔍", title: "Basic file search", desc: "Find files on your computer with voice commands"},
                {icon: "⏱️", title: "Simple automation", desc: "Basic task automation with preset commands"},
                {icon: "🌐", title: "Web search", desc: "Search the web with your voice"},
                {icon: "📅", title: "Calendar integration", desc: "Basic calendar management and reminders"}
            ],
            videos: [
                "https://www.youtube.com/embed/OowjNSa3bsE?si=i8LJJBuHlpcIk7Ju",  
            ],
            downloadFile: "nova_windows_base_v2.0.exe",
            fileSize: "380.2 MB",
            price: 39900, // ₹399 in paise
            downloadUrl: "https://www.transfernow.net/dl/202509139E8fwBb1"
        },
        premium: {
            title: "Nova 3.0 Premium",
            subtitle: "Advanced Windows AI assistant",
            features: [
                {icon: "🖥️", title: "System control", desc: "Control your Windows system with voice commands"},
                {icon: "🤖", title: "Advanced automation", desc: "Create complex automation workflows with natural language"},
                {icon: "📊", title: "Productivity tools", desc: "Automated reporting and data analysis"},
                {icon: "🔍", title: "Smart search", desc: "Advanced file and content search across your system"},
                {icon: "⌨️", title: "Input automation", desc: "Keyboard and mouse automation with AI assistance"},
                {icon: "🌍", title: "Multi-language", desc: "Support for multiple languages with high accuracy"}
            ],
            videos: [
                "https://www.youtube.com/embed/OowjNSa3bsE?si=i8LJJBuHlpcIk7Ju",  
            ],
            downloadFile: "nova_windows_premium_v2.0.exe",
            fileSize: "420.5 MB",
            price: 59900, // ₹599 in paise
            downloadUrl: "https://www.transfernow.net/dl/202509139E8fwBb1"
        },
        elite: {
            title: "Nova 3.0 Elite",
            subtitle: "Complete Windows AI solution",
            features: [
                {icon: "🖥️", title: "Complete system control", desc: "Full control over all aspects of your Windows system"},
                {icon: "🤖", title: "AI-powered automation", desc: "Create complex automation with natural language instructions"},
                {icon: "🔍", title: "Smart search & organization", desc: "Find and organize files, emails, and information"},
                {icon: "📊", title: "Productivity suite", desc: "Automated reporting, data analysis, and presentations"},
                {icon: "⌨️", title: "Advanced input control", desc: "Full keyboard and mouse automation with AI prediction"},
                {icon: "🔒", title: "Security monitoring", desc: "Real-time system security monitoring and threat prevention"},
                {icon: "🚀", title: "Priority support", desc: "Dedicated support team for Elite customers"},
                {icon: "🔄", title: "All future updates", desc: "Free lifetime updates to all new features"}
            ],
            videos: [
                "https://www.youtube.com/embed/OowjNSa3bsE?si=i8LJJBuHlpcIk7Ju",  
            ],
            downloadFile: "nova_windows_elite_v2.0.exe",
            fileSize: "480.3 MB",
            price: 79900, // ₹799 in paise
            downloadUrl: "https://www.transfernow.net/dl/202509139E8fwBb1"
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
        const nova2Count = getRemainingKeysCount();
        
        const nova2Status = document.getElementById('nova2-key-status');
        if (nova2Status) {
            const countElement = nova2Status.querySelector('.key-count');
            countElement.textContent = nova2Count;
            
            if (nova2Count > 10) {
                nova2Status.classList.add('keys-available');
                nova2Status.classList.remove('keys-low', 'keys-none');
            } else if (nova2Count > 0) {
                nova2Status.classList.add('keys-low');
                nova2Status.classList.remove('keys-available', 'keys-none');
            } else {
                nova2Status.classList.add('keys-none');
                nova2Status.classList.remove('keys-available', 'keys-low');
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
            element.textContent = 'Error';
        });
    }
}

// Initialize particles
function initParticles() {
    const container = document.getElementById('particle-background');
    const particleCount = window.innerWidth < 768 ? 30 : 50;
    
    for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        
        const size = Math.random() * 2 + 1;
        particle.style.width = `${size}px`;
        particle.style.height = `${size}px`;
        
        particle.style.left = `${Math.random() * 100}%`;
        particle.style.top = `${Math.random() * 100}%`;
        
        const duration = Math.random() * 10 + 10;
        particle.style.animationDuration = `${duration}s`;
        
        particle.style.animationDelay = `${Math.random() * 10}s`;
        
        container.appendChild(particle);
    }
}

// Show notification
function showNotification(message, type = 'info') {
    const notification = document.getElementById('notification');
    const icon = document.getElementById('notification-icon');
    const msg = document.getElementById('notification-message');
    
    switch(type) {
        case 'success':
            icon.className = 'notification-icon fas fa-check-circle';
            notification.className = 'notification success';
            break;
        case 'warning':
            icon.className = 'notification-icon fas fa-exclamation-triangle';
            notification.className = 'notification warning';
            break;
        case 'error':
            icon.className = 'notification-icon fas fa-times-circle';
            notification.className = 'notification error';
            break;
        default:
            icon.className = 'notification-icon fas fa-info-circle';
            notification.className = 'notification';
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
    
    // Update document title based on screen
    if (screenId === 'welcome-screen') {
        document.title = "NOVA AI - The Future of Personal Assistant";
    } else if (screenId === 'version-selector') {
        document.title = "NOVA AI - Select Your Version";
    } else if (screenId === 'variant-selector') {
        document.title = "NOVA AI - Select Variant";
    } else if (screenId === 'details-screen') {
        document.title = `NOVA AI - ${selectedVariant ? versions.nova2[selectedVariant].title : 'Nova 3.0'} Details`;
    } else if (screenId === 'download-screen') {
        document.title = "NOVA AI - Download";
    } else if (screenId === 'whatsapp-screen') {
        document.title = "NOVA AI - Contact via WhatsApp";
    }
}

// Select version function
function selectVersion(version) {
    document.querySelectorAll('.version-card').forEach(card => {
        card.classList.remove('selected');
    });
    
    event.target.closest('.version-card').classList.add('selected');
    selectedVersion = version;
    
    if (version === 'nova2') {
        // For Windows version, show variant selector
        showScreen('variant-selector');
        return;
    }
    
    // For Android version, enable continue button
    const continueBtn = document.getElementById('continue-btn');
    continueBtn.style.display = 'block';
    continueBtn.disabled = false;
}

// Select variant function
function selectVariant(variant) {
    document.querySelectorAll('.variant-card').forEach(card => {
        card.classList.remove('selected');
    });
    
    event.target.closest('.variant-card').classList.add('selected');
    selectedVariant = variant;
    
    const continueBtn = document.getElementById('variant-continue-btn');
    continueBtn.style.display = 'block';
    continueBtn.disabled = false;
}

// Go back from details function
function goBackFromDetails() {
    if (selectedVersion === 'nova2') {
        showScreen('variant-selector');
    } else {
        showScreen('version-selector');
    }
}

// Show version details function
function showVersionDetails() {
    if (!selectedVersion) {
        showNotification('Please select a version first', 'error');
        return;
    }
    
    let version;
    if (selectedVersion === 'nova2' && selectedVariant) {
        version = versions.nova2[selectedVariant];
    } else {
        showNotification('Please select a variant first', 'error');
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
        if (selectedVersion === 'nova2' && selectedVariant) {
            version = versions.nova2[selectedVariant];
        } else {
            reject(new Error('Invalid version or variant selected'));
            return;
        }
        
        const options = {
            key: 'rzp_live_OcHSFiDAu0iMZC',
            amount: version.price,
            currency: 'INR',
            name: "NOVA AI",
            description: `Purchase ${version.title} License`,
            handler: function (response) {
                console.log('Payment Success:', response);
                showNotification('Payment successful!', 'success');
                paymentVerified = true;
                resolve(response);
            },
            prefill: {
                name: "NOVA User",
                email: "user@nova.ai",
                contact: "9000000000"
            },
            theme: {
                color: "#00ffff",
                backdrop_color: "#0a0a0a"
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
                            name: 'Pay using UPI',
                            instruments: [
                                {
                                    method: 'upi'
                                }
                            ]
                        },
                        other: {
                            name: 'Other Payment Methods',
                            instruments: [
                                {
                                    method: 'card'
                                },
                                {
                                    method: 'netbanking'
                                },
                                {
                                    method: 'wallet'
                                }
                            ]
                        }
                    },
                    sequence: ['block.utib', 'block.other'],
                    preferences: {
                        show_default_blocks: true
                    }
                }
            },
            modal: {
                ondismiss: function () {
                    showNotification('Payment window closed', 'warning');
                    reject(new Error('Payment cancelled by user'));
                }
            },
            retry: {
                enabled: true,
                max_count: 3
            }
        };

        const rzp = new Razorpay(options);
        rzp.on('payment.failed', function (response) {
            console.error('Payment failed:', response.error);
            showNotification(`Payment failed: ${response.error.description}`, 'error');
            reject(new Error(response.error.description));
        });

        rzp.open();
    });
}

// Get Nova function
async function getNova() {
    try {
        // First handle payment
        await handlePayment();
        
        if (!paymentVerified) {
            showNotification('Payment verification failed', 'error');
            return;
        }
        
        // Show congratulations screen with WhatsApp option
        showScreen('whatsapp-screen');
        
    } catch (error) {
        console.error('Error in getNova:', error);
        showNotification(error.message, 'error');
    }
}

// Open WhatsApp function
function openWhatsApp() {
    let version;
    if (selectedVersion === 'nova2' && selectedVariant) {
        version = versions.nova2[selectedVariant];
    }
    
    // Create WhatsApp message
    const message = `Hello! I just purchased ${version.title}. Please provide my access key and download link.`;
    const phoneNumber = "919512194144"; // Replace with your WhatsApp business number
    
    // Open WhatsApp
    window.open(`https://wa.me/${phoneNumber}?text=${encodeURIComponent(message)}`, '_blank');
}

// Download Nova function
function downloadNova() {
    if (!downloadUrl) {
        showNotification('Download URL not available', 'error');
        return;
    }
    
    if (downloadInProgress) {
        showNotification('Download already in progress', 'warning');
        return;
    }
    
    downloadInProgress = true;
    const progressContainer = document.getElementById('progress-container');
    const progressBar = document.getElementById('progress-bar');
    const downloadBtn = document.getElementById('download-btn');
    
    // Show progress bar
    progressContainer.style.display = 'block';
    downloadBtn.disabled = true;
    downloadBtn.innerHTML = '<i class="fas fa-spinner fa-spin" style="margin-right: 15px;"></i>Preparing Download...';
    
    // Create a download link element
    let version;
    if (selectedVersion === 'nova2' && selectedVariant) {
        version = versions.nova2[selectedVariant];
    }
    
    const link = document.createElement('a');
    link.href = downloadUrl;
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
            
            downloadBtn.innerHTML = '<i class="fas fa-check" style="margin-right: 15px;"></i>Download Started!';
            showNotification('Download started! Check your downloads folder.', 'success');
            
            setTimeout(() => {
                downloadInProgress = false;
                downloadBtn.disabled = false;
                downloadBtn.innerHTML = '<i class="fas fa-download" style="margin-right: 15px;"></i>Download Again';
                progressContainer.style.display = 'none';
                progressBar.style.width = '0%';
            }, 3000);
        }
    }, 200);
}

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initParticles();
    
    // Mobile menu toggle
    const navbarToggle = document.getElementById('navbar-toggle');
    const navbarMenu = document.querySelector('.navbar-menu');
    
    navbarToggle.addEventListener('click', function() {
        navbarMenu.classList.toggle('active');
        navbarToggle.classList.toggle('active');
    });
    
    // Close mobile menu when clicking outside
    document.addEventListener('click', function(event) {
        if (!navbarToggle.contains(event.target) && !navbarMenu.contains(event.target)) {
            navbarMenu.classList.remove('active');
            navbarToggle.classList.remove('active');
        }
    });
    
    // Event listeners for buttons
    document.getElementById('welcome-continue-btn').addEventListener('click', () => showScreen('version-selector'));
    document.getElementById('nova2-card').addEventListener('click', () => selectVersion('nova2'));
    document.getElementById('continue-btn').addEventListener('click', showVersionDetails);
    document.getElementById('variant-back-btn').addEventListener('click', () => showScreen('version-selector'));
    document.getElementById('base-variant').addEventListener('click', () => selectVariant('base'));
    document.getElementById('premium-variant').addEventListener('click', () => selectVariant('premium'));
    document.getElementById('elite-variant').addEventListener('click', () => selectVariant('elite'));
    document.getElementById('variant-continue-btn').addEventListener('click', showVersionDetails);
    document.getElementById('details-back-btn').addEventListener('click', goBackFromDetails);
    document.getElementById('get-nova-btn').addEventListener('click', getNova);
    document.getElementById('whatsapp-btn').addEventListener('click', openWhatsApp);
    document.getElementById('whatsapp-back-btn').addEventListener('click', () => showScreen('details-screen'));
    document.getElementById('download-btn').addEventListener('click', downloadNova);
    
    // Load key status on page load
    updateKeyStatus();
});

// Make functions global
window.showScreen = showScreen;
window.selectVersion = selectVersion;
window.selectVariant = selectVariant;
window.goBackFromDetails = goBackFromDetails;
window.showVersionDetails = showVersionDetails;
window.getNova = getNova;
window.openWhatsApp = openWhatsApp;
window.downloadNova = downloadNova;