// ========================================
// GitCloud Website - Main JavaScript
// ========================================

// Workflow Animation Controller
class WorkflowAnimation {
    constructor() {
        this.stages = [
            { id: 'stage-github', arrow: 'arrow-1', timeline: 0 },
            { id: 'stage-ai', arrow: 'arrow-2', timeline: 1 },
            { id: 'stage-cloud', arrow: 'arrow-3', timeline: 2 },
            { id: 'stage-running', arrow: null, timeline: 3 }
        ];
        this.currentStage = -1;
        this.isAnimating = false;
        this.animationSpeed = 1500; // milliseconds per stage
        this.init();
    }

    init() {
        // Set up Intersection Observer for auto-start
        this.setupIntersectionObserver();

        // Set up replay button
        const replayBtn = document.getElementById('replay-btn');
        if (replayBtn) {
            replayBtn.addEventListener('click', () => this.restart());
        }

        // Set up timeline items
        this.setupTimelineInteraction();
    }

    setupIntersectionObserver() {
        const workflowSection = document.querySelector('.workflow-section');

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && !this.isAnimating && this.currentStage === -1) {
                    // Start animation when section comes into view
                    setTimeout(() => this.start(), 500);
                }
            });
        }, { threshold: 0.3 });

        if (workflowSection) {
            observer.observe(workflowSection);
        }
    }

    setupTimelineInteraction() {
        const timelineItems = document.querySelectorAll('.timeline-item');
        timelineItems.forEach((item, index) => {
            item.addEventListener('click', () => {
                if (!this.isAnimating) {
                    this.jumpToStage(index);
                }
            });
        });
    }

    start() {
        if (this.isAnimating) return;
        this.isAnimating = true;
        this.animateNextStage();
    }

    animateNextStage() {
        this.currentStage++;

        if (this.currentStage >= this.stages.length) {
            this.isAnimating = false;
            return;
        }

        const stage = this.stages[this.currentStage];

        // Activate current stage
        this.activateStage(stage);

        // Update timeline
        this.updateTimeline(stage.timeline);

        // Schedule next stage
        if (this.currentStage < this.stages.length - 1) {
            setTimeout(() => this.animateNextStage(), this.animationSpeed);
        } else {
            this.isAnimating = false;
        }
    }

    activateStage(stage) {
        const stageElement = document.getElementById(stage.id);
        if (stageElement) {
            stageElement.classList.add('active');

            // Trigger typing animation for text elements
            const typingElements = stageElement.querySelectorAll('.typing-text');
            typingElements.forEach(el => {
                const text = el.getAttribute('data-text');
                if (text) {
                    this.typeText(el, text);
                }
            });
        }

        // Activate arrow
        if (stage.arrow) {
            const arrowElement = document.getElementById(stage.arrow);
            if (arrowElement) {
                setTimeout(() => {
                    arrowElement.classList.add('active');
                }, 300);
            }
        }

        // Special animations for specific stages
        this.triggerStageSpecialEffects(stage.id);
    }

    triggerStageSpecialEffects(stageId) {
        switch(stageId) {
            case 'stage-ai':
                this.animateAnalysisLines();
                break;
            case 'stage-cloud':
                this.animateProvisionProgress();
                break;
            case 'stage-running':
                this.animateSuccessState();
                break;
        }
    }

    animateAnalysisLines() {
        const analysisBox = document.querySelector('#stage-ai .analysis-box');
        if (analysisBox) {
            const lines = analysisBox.querySelectorAll('.analysis-line');
            lines.forEach((line, index) => {
                setTimeout(() => {
                    line.style.opacity = '1';
                    line.style.transform = 'translateX(0)';
                }, index * 300);
            });
        }
    }

    animateProvisionProgress() {
        const progressBars = document.querySelectorAll('#stage-cloud .progress-fill');
        progressBars.forEach((bar, index) => {
            setTimeout(() => {
                bar.style.width = '100%';
            }, index * 400);
        });
    }

    animateSuccessState() {
        const successRing = document.querySelector('#stage-running .success-ring');
        if (successRing) {
            successRing.style.animation = 'success-pulse 1s ease-out';
        }
    }

    typeText(element, text) {
        element.textContent = text;
        element.style.animation = 'typing 2s steps(20) 0.5s forwards, blink 0.5s step-end infinite';
    }

    updateTimeline(index) {
        const timelineItems = document.querySelectorAll('.timeline-item');
        timelineItems.forEach((item, i) => {
            if (i <= index) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });
    }

    jumpToStage(stageIndex) {
        // Reset all stages
        this.reset();

        // Activate stages up to selected one
        for (let i = 0; i <= stageIndex; i++) {
            const stage = this.stages[i];
            this.activateStage(stage);
        }

        this.currentStage = stageIndex;
        this.updateTimeline(stageIndex);
    }

    reset() {
        // Remove active class from all stages
        this.stages.forEach(stage => {
            const stageElement = document.getElementById(stage.id);
            if (stageElement) {
                stageElement.classList.remove('active');
            }

            if (stage.arrow) {
                const arrowElement = document.getElementById(stage.arrow);
                if (arrowElement) {
                    arrowElement.classList.remove('active');
                }
            }
        });

        // Reset timeline
        const timelineItems = document.querySelectorAll('.timeline-item');
        timelineItems.forEach(item => item.classList.remove('active'));

        // Reset analysis lines
        const analysisLines = document.querySelectorAll('.analysis-line');
        analysisLines.forEach(line => {
            line.style.opacity = '0';
            line.style.transform = 'translateX(-10px)';
        });

        // Reset progress bars
        const progressBars = document.querySelectorAll('.progress-fill');
        progressBars.forEach(bar => {
            bar.style.width = '0';
        });

        this.currentStage = -1;
        this.isAnimating = false;
    }

    restart() {
        this.reset();
        setTimeout(() => this.start(), 300);
    }
}

// Copy to Clipboard functionality
function copyToClipboard(text, event) {
    navigator.clipboard.writeText(text).then(() => {
        // Show feedback
        const btn = event.target.closest('.copy-btn');
        const originalHTML = btn.innerHTML;
        btn.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M13.5 4.5L6 12L2.5 8.5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        `;
        btn.style.color = '#10b981';

        setTimeout(() => {
            btn.innerHTML = originalHTML;
            btn.style.color = '';
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy:', err);
    });
}

// Smooth scroll for navigation links
function setupSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (href === '#') return; // Skip empty anchors

            e.preventDefault();
            const target = document.querySelector(href);
            if (target) {
                const navHeight = document.querySelector('.nav').offsetHeight;
                const targetPosition = target.offsetTop - navHeight - 20;

                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });
}

// Navbar scroll effect
function setupNavbarScroll() {
    const nav = document.querySelector('.nav');

    window.addEventListener('scroll', () => {
        const currentScroll = window.pageYOffset;

        if (currentScroll > 50) {
            nav.style.background = 'rgba(10, 10, 15, 0.95)';
            nav.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.3)';
        } else {
            nav.style.background = 'rgba(10, 10, 15, 0.8)';
            nav.style.boxShadow = 'none';
        }
    });
}

// Feature cards hover effect
function setupFeatureCards() {
    const cards = document.querySelectorAll('.feature-card');

    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-8px)';
        });

        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
}

// Intersection Observer for fade-in animations
function setupScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);

    // Observe feature cards and other elements
    document.querySelectorAll('.feature-card').forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(30px)';
        card.style.transition = 'all 0.6s ease-out';
        observer.observe(card);
    });
}

// Particle background effect (subtle)
function createParticleBackground() {
    const canvas = document.createElement('canvas');
    canvas.style.position = 'fixed';
    canvas.style.top = '0';
    canvas.style.left = '0';
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    canvas.style.pointerEvents = 'none';
    canvas.style.zIndex = '0';
    canvas.style.opacity = '0.3';

    document.body.prepend(canvas);

    const ctx = canvas.getContext('2d');
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    const particles = [];
    const particleCount = 50;

    class Particle {
        constructor() {
            this.x = Math.random() * canvas.width;
            this.y = Math.random() * canvas.height;
            this.size = Math.random() * 2 + 1;
            this.speedX = Math.random() * 0.5 - 0.25;
            this.speedY = Math.random() * 0.5 - 0.25;
            this.opacity = Math.random() * 0.5 + 0.2;
        }

        update() {
            this.x += this.speedX;
            this.y += this.speedY;

            if (this.x > canvas.width) this.x = 0;
            if (this.x < 0) this.x = canvas.width;
            if (this.y > canvas.height) this.y = 0;
            if (this.y < 0) this.y = canvas.height;
        }

        draw() {
            ctx.fillStyle = `rgba(99, 102, 241, ${this.opacity})`;
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fill();
        }
    }

    function init() {
        for (let i = 0; i < particleCount; i++) {
            particles.push(new Particle());
        }
    }

    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        particles.forEach(particle => {
            particle.update();
            particle.draw();
        });

        requestAnimationFrame(animate);
    }

    init();
    animate();

    window.addEventListener('resize', () => {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    });
}

// Initialize everything when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Initialize workflow animation
    const workflowAnimation = new WorkflowAnimation();

    // Setup all interactions
    setupSmoothScroll();
    setupNavbarScroll();
    setupFeatureCards();
    setupScrollAnimations();

    // Optional: Create particle background (comment out if too heavy)
    createParticleBackground();

    // Make copy function globally available
    window.copyToClipboard = copyToClipboard;

    console.log('🚀 GitCloud website initialized');
});

// Handle page visibility change to restart animation
document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') {
        // Optionally restart animation when page becomes visible
    }
});

// Add keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Press 'R' to replay animation
    if (e.key === 'r' || e.key === 'R') {
        const replayBtn = document.getElementById('replay-btn');
        if (replayBtn) {
            replayBtn.click();
        }
    }
});
