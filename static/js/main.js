/* static/js/main.js */
import * as API from './modules/api.js';
import * as UI from './modules/ui.js';
import * as Editor from './modules/editor.js';

document.addEventListener('DOMContentLoaded', () => {
    
    // 1. Centralized DOM Store
    const elements = {
        dropArea: document.getElementById('drop-area'),
        fileInput: document.getElementById('file-input'),
        styleInput: document.getElementById('style-input'),
        roomType: document.getElementById('room-type'),
        processBtn: document.getElementById('process-button'),
        initialView: document.getElementById('initial-view'),
        resultView: document.getElementById('result-view'),
        loadingMsg: document.getElementById('loading-msg'),
        loadingText: document.getElementById('loading-text'),
        loadingBackground: document.getElementById('loading-background'),
        comparisonBox: document.getElementById('comparison-box'),
        overlay: document.getElementById('overlay'),
        slider: document.getElementById('slider'),
        baseImg: document.getElementById('base-image'),
        finalImg: document.getElementById('final-image'),
        storeOriginal: document.getElementById('store-original'),
        customInstructionsInput: document.getElementById('custom-instructions-input'),
        applyInstructionsBtn: document.getElementById('apply-instructions-btn'),
        toggleSearchBtn: document.getElementById('toggle-search-btn'),
        selectionLayer: document.getElementById('selection-layer'),
        selectionBox: document.getElementById('selection-box'),
        resultsPanel: document.getElementById('search-results-panel'),
        resultsGrid: document.getElementById('results-grid'),
        closeResultsBtn: document.getElementById('close-results'),
        customInstructionsBar: document.getElementById('custom-instructions-bar'),
        emptyThenGenerate: document.getElementById('empty-then-generate'),
        additionalInstructions: document.getElementById('additional-instructions'),
    };

    let selectedFile = null;
    elements.addStyleBtn = document.getElementById('add-style-btn'); 
    elements.styleGrid = document.querySelector('.style-grid');
    const uploadBtnTrigger = document.getElementById('upload-btn-trigger');

    // Cache badge elements to avoid repeated DOM queries
    const beforeBadge = document.querySelector('.badge-before-static');
    const afterBadge = document.querySelector('.badge-after-static');

    // History management for undo/revert functionality
    const imageHistory = {
        states: [], // Array of { finalImage: url, baseImage: url }
        maxSize: 10,
        currentIndex: -1,
        
        save(finalImageSrc, baseImageSrc) {
            // Remove any "future" history if we're not at the end (user did undo then new operation)
            if (this.currentIndex < this.states.length - 1) {
                this.states = this.states.slice(0, this.currentIndex + 1);
            }
            
            // Add new state
            this.states.push({
                finalImage: finalImageSrc,
                baseImage: baseImageSrc || finalImageSrc // Use finalImage as base if not provided
            });
            this.currentIndex = this.states.length - 1;
            
            // Limit history size (remove oldest entries)
            if (this.states.length > this.maxSize) {
                this.states.shift();
                this.currentIndex--;
            }
            
            // Update button states
            this.updateButtons();
        },
        
        canUndo() {
            return this.currentIndex > 0 && this.states.length > 1;
        },
        
        canRedo() {
            return this.currentIndex < this.states.length - 1;
        },
        
        undo() {
            if (!this.canUndo()) {
                return null;
            }
            this.currentIndex--;
            this.updateButtons();
            return this.states[this.currentIndex];
        },
        
        redo() {
            if (!this.canRedo()) {
                return null;
            }
            this.currentIndex++;
            this.updateButtons();
            return this.states[this.currentIndex];
        },
        
        clear() {
            this.states = [];
            this.currentIndex = -1;
            this.updateButtons();
        },
        
        updateButtons() {
            const undoBtn = document.getElementById('undo-btn');
            const redoBtn = document.getElementById('redo-btn');
            
            if (undoBtn) {
                undoBtn.disabled = !this.canUndo();
                undoBtn.title = this.canUndo() 
                    ? 'Undo last change' 
                    : 'No changes to undo';
            }
            
            if (redoBtn) {
                redoBtn.disabled = !this.canRedo();
                redoBtn.title = this.canRedo() 
                    ? 'Redo last undone change' 
                    : 'No changes to redo';
            }
        },
        
        getCurrentState() {
            if (this.currentIndex >= 0 && this.currentIndex < this.states.length) {
                return this.states[this.currentIndex];
            }
            return null;
        },
        
        getAllStates() {
            return this.states;
        },
        
        jumpToState(index) {
            if (index >= 0 && index < this.states.length) {
                this.currentIndex = index;
                this.updateButtons();
                return this.states[index];
            }
            return null;
        }
    };

    // Helper function to safely set image src with cleanup of previous handlers
    function setImageSrcWithCleanup(imgElement, newSrc, onloadHandler) {
        if (!imgElement) return;
        // Clear previous onload handler to prevent accumulation
        imgElement.onload = null;
        imgElement.onerror = null;
        // Set new src
        imgElement.src = newSrc;
        // Set new onload handler if provided
        if (onloadHandler) {
            imgElement.onload = onloadHandler;
        }
    }

    // Helper function to restore image state (used by both undo and redo)
    function restoreImageState(state) {
        if (!state) return;
        
        // Exit search furniture mode if active
        exitSearchModeIfActive();
        
        // Restore final image
        setImageSrcWithCleanup(elements.finalImg, state.finalImage, () => {
            // Update UI after image loads
            elements.resultView.classList.remove('hidden');
            showComparisonElements();
            
            // Sync sizes after a brief delay
            setTimeout(() => {
                Editor.syncImageSizes(elements.baseImg, elements.finalImg);
            }, 100);
        });
        
        // Restore base image if it was different
        if (state.baseImage && state.baseImage !== state.finalImage) {
            setImageSrcWithCleanup(elements.baseImg, state.baseImage);
            setImageSrcWithCleanup(elements.storeOriginal, state.baseImage);
        }
    }

    // Function to render history panel
    function renderHistoryPanel() {
        const historyGrid = document.getElementById('history-grid');
        if (!historyGrid) return;
        
        const states = imageHistory.getAllStates();
        const currentIndex = imageHistory.currentIndex;
        
        if (states.length === 0) {
            historyGrid.innerHTML = '<p class="history-empty">No history available. Start designing to see your history!</p>';
            return;
        }
        
        historyGrid.innerHTML = states.map((state, index) => {
            const isActive = index === currentIndex;
            const label = index === 0 
                ? 'Original' 
                : index === states.length - 1 
                    ? 'Latest' 
                    : `Step ${index + 1}`;
            
            return `
                <div class="history-item ${isActive ? 'active' : ''}" data-index="${index}">
                    <div class="history-item-thumbnail">
                        <img src="${state.finalImage}" alt="${label}" loading="lazy">
                        ${isActive ? '<div class="history-item-badge">Current</div>' : ''}
                    </div>
                    <div class="history-item-label">${label}</div>
                </div>
            `;
        }).join('');
        
        // Add click handlers to history items
        historyGrid.querySelectorAll('.history-item').forEach(item => {
            item.addEventListener('click', () => {
                const index = parseInt(item.dataset.index);
                const state = imageHistory.jumpToState(index);
                if (state) {
                    restoreImageState(state);
                    // Re-render to update active state
                    renderHistoryPanel();
                    // Close modal after selection
                    closeHistoryModal();
                }
            });
        });
    }

    // Function to show history modal
    function showHistoryModal() {
        const modal = document.getElementById('history-modal');
        if (modal) {
            modal.classList.remove('hidden');
            renderHistoryPanel();
            // Prevent body scroll when modal is open
            document.body.style.overflow = 'hidden';
        }
    }

    // Function to close history modal
    function closeHistoryModal() {
        const modal = document.getElementById('history-modal');
        if (modal) {
            modal.classList.add('hidden');
            // Restore body scroll
            document.body.style.overflow = '';
        }
    }

    // --- Initialization ---
    Editor.initSlider(elements.comparisonBox, elements.overlay, elements.slider);
    
    // Helper function to convert data URI to File object
    function dataURItoFile(dataURI, fileName) {
        const byteString = atob(dataURI.split(',')[1]);
        const mimeString = dataURI.split(',')[0].match(/:(.*?);/)[1];
        const ab = new ArrayBuffer(byteString.length);
        const ia = new Uint8Array(ab);
        for (let i = 0; i < byteString.length; i++) {
            ia[i] = byteString.charCodeAt(i);
        }
        return new File([ab], fileName, { type: mimeString });
    }

    // Initialize Drawing logic with a callback for what to do when finished
    Editor.initDrawing(elements, async (backendBox) => {
        elements.resultsPanel.classList.remove('hidden');
        elements.resultsGrid.innerHTML = '<p style="text-align:center;">Searching...</p>';
        
        try {
            // Convert data URI to File object
            const imageFile = dataURItoFile(elements.finalImg.src, 'search-image.jpg');
            const data = await API.searchFurniture(imageFile, backendBox);
            UI.renderSearchResults(data.results, elements.resultsGrid);
        } catch (err) {
            elements.resultsGrid.innerHTML = '<p>Error searching.</p>';
            console.error(err);
        }
    });

    // --- Helper Functions for Comparison UI State ---
    
    /**
     * Hides all comparison UI elements (Slider, Bar, Badges)
     * Used when a new image is uploaded/selected.
     */
    function hideComparisonElements() {
        // 1. Hide Slider Handle - Use multiple methods to ensure it's hidden
        if (elements.slider) {
            // First, add the hidden class
            elements.slider.classList.add('hidden');
            
            // Then use setProperty with !important to ensure it overrides any other styles
            // This must come AFTER adding the class to work with the CSS rule
            elements.slider.style.setProperty('display', 'none', 'important');
            elements.slider.style.setProperty('visibility', 'hidden', 'important');
            elements.slider.style.setProperty('opacity', '0', 'important');
            elements.slider.style.left = '0%';
            elements.slider.style.pointerEvents = 'none';
            
            // Force a reflow to ensure styles are applied
            void elements.slider.offsetHeight;
        }

        // 2. Hide Custom Instructions Bar
        if (elements.customInstructionsBar) {
            elements.customInstructionsBar.classList.add('hidden');
        }

        // 3. Hide Static Badges (using cached elements)
        if (beforeBadge) {
            beforeBadge.classList.add('hidden');
            beforeBadge.style.display = 'none';
            beforeBadge.style.visibility = 'hidden';
        }
        if (afterBadge) {
            afterBadge.classList.add('hidden');
            afterBadge.style.display = 'none';
            afterBadge.style.visibility = 'hidden';
        }

        // 4. Reset Overlay (Visual reset and hide)
        if (elements.overlay) {
            elements.overlay.style.width = '0%';
            elements.overlay.style.borderRight = 'none';
            elements.overlay.style.setProperty('display', 'none', 'important');
        }
    }

    /**
     * Shows all comparison UI elements
     * Used after generation, refinement, or applying instructions is complete.
     */
    function showComparisonElements() {
        // 1. Show Slider Handle - Reset all properties
        if (elements.slider) {
            elements.slider.classList.remove('hidden');
            elements.slider.style.display = 'flex'; // Flex is required for centering the icon
            elements.slider.style.visibility = 'visible';
            elements.slider.style.opacity = '1';
            elements.slider.style.left = '50%';
            elements.slider.style.pointerEvents = 'auto';
        }

        // 2. Show Custom Instructions Bar
        if (elements.customInstructionsBar) {
            elements.customInstructionsBar.classList.remove('hidden');
        }

        // 3. Show Static Badges (using cached elements)
        if (beforeBadge) {
            beforeBadge.classList.remove('hidden');
            beforeBadge.style.display = 'block';
            beforeBadge.style.visibility = 'visible';
        }
        if (afterBadge) {
            afterBadge.classList.remove('hidden');
            afterBadge.style.display = 'block';
            afterBadge.style.visibility = 'visible';
        }

        // 4. Set Overlay to Comparison Mode
        if (elements.overlay) {
            elements.overlay.style.display = 'block';
            elements.overlay.style.width = '50%';
            elements.overlay.style.borderRight = '2px solid white';
        }
    }

    // --- Event Listeners ---

    // 1. File Upload
    // Handle click on drop area (viewport) or upload button
    elements.dropArea.addEventListener('click', (e) => {
        // Only trigger if clicking on the viewport itself or initial view, not on result view elements
        if (e.target === elements.dropArea || 
            e.target.id === 'initial-view' || 
            e.target.closest('#initial-view') ||
            (elements.resultView.classList.contains('hidden') && !e.target.closest('#result-view'))) {
            elements.fileInput.click();
        }
    });
    
    // Handle drag and drop
    elements.dropArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        elements.dropArea.style.backgroundColor = 'rgba(217, 70, 239, 0.1)';
    });
    
    elements.dropArea.addEventListener('dragleave', (e) => {
        e.preventDefault();
        elements.dropArea.style.backgroundColor = '';
    });
    
    elements.dropArea.addEventListener('drop', (e) => {
        e.preventDefault();
        elements.dropArea.style.backgroundColor = '';
        const files = e.dataTransfer.files;
        if (files.length > 0 && files[0].type.startsWith('image/')) {
            handleFileSelect(files[0]);
        }
    });
    
    // Handle file input change
    elements.fileInput.addEventListener('change', (e) => {
        if (e.target.files[0]) {
            handleFileSelect(e.target.files[0]);
        }
    });
    
    // Helper function to handle file selection
    function handleFileSelect(file) {
        selectedFile = file;
        // Clear history when new file is uploaded
        imageHistory.clear();
        
        const reader = new FileReader();
        reader.onload = (ev) => {
            // Hide initial view
            elements.initialView.classList.add('hidden');
            
            // --- FIX: FORCE UI RESET ---
            // CRITICAL: Hide all comparison tools BEFORE showing result view
            // This ensures they're hidden before the DOM renders
            hideComparisonElements();
            
            // Show custom instructions bar after image is uploaded (but before generation)
            // Note: Slider and badges stay hidden until after generation
            if (elements.customInstructionsBar) {
                elements.customInstructionsBar.classList.remove('hidden');
            }
            
            // Display uploaded image immediately in the center
            const imageDataUrl = ev.target.result;
            
            // Use helper function to set image src with cleanup
            setImageSrcWithCleanup(elements.baseImg, imageDataUrl, () => {
                Editor.syncImageSizes(elements.baseImg, elements.finalImg);
                // Ensure comparison elements stay hidden after image loads (slider and badges)
                hideComparisonElements();
                // Show custom instructions bar after image is uploaded
                if (elements.customInstructionsBar) {
                    elements.customInstructionsBar.classList.remove('hidden');
                }
            });
            
            setImageSrcWithCleanup(elements.finalImg, imageDataUrl); // Show same image initially
            setImageSrcWithCleanup(elements.storeOriginal, imageDataUrl);
            
            // Save initial state to history (as first state)
            imageHistory.save(imageDataUrl, imageDataUrl);
            
            // Show result view with uploaded image
            elements.resultView.classList.remove('hidden');
            
            // Force hide again after showing result view to ensure it stays hidden
            // Use requestAnimationFrame to ensure DOM has updated
            requestAnimationFrame(() => {
                hideComparisonElements();
                // Show custom instructions bar after image is uploaded
                if (elements.customInstructionsBar) {
                    elements.customInstructionsBar.classList.remove('hidden');
                }
            });
            
            elements.processBtn.disabled = false;
            
            // Show custom instructions bar immediately after upload
            if (elements.customInstructionsBar) {
                elements.customInstructionsBar.classList.remove('hidden');
            }
        };
        reader.readAsDataURL(selectedFile);
    }
    
    // Show upload button only when needed
    if (uploadBtnTrigger) {
        // Initially hidden, will show after result is generated
        uploadBtnTrigger.style.display = 'none';
    }

    // 2. Room Type Selection (Chips)
    document.querySelectorAll('.chip').forEach(chip => {
        chip.addEventListener('click', () => {
            document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
            elements.roomType.value = chip.dataset.value;
        });
    });

    // Helper function to exit search furniture mode if active
    function exitSearchModeIfActive() {
        if (elements.toggleSearchBtn.classList.contains('active')) {
            Editor.toggleSearchMode(false, elements);
        }
    }

    // 3. Generate Design
    elements.processBtn.addEventListener('click', async () => {
        if (!selectedFile) return;
        
        // Exit search furniture mode before generating new design
        exitSearchModeIfActive();
        
        // Check if empty then generate is enabled
        const emptyThenGenerate = elements.emptyThenGenerate && elements.emptyThenGenerate.checked;
        const loadingMessage = emptyThenGenerate 
            ? "Emptying room, then generating new design..." 
            : "Generating new interior...";
        
        // Get additional instructions if provided
        const additionalInstructions = elements.additionalInstructions 
            ? elements.additionalInstructions.value.trim() 
            : '';
        
        UI.toggleLoading(true, elements, loadingMessage);
        
        try {
            const data = await API.redesignImage(
                selectedFile, 
                elements.styleInput.value, 
                elements.roomType.value,
                emptyThenGenerate,
                additionalInstructions
            );
            
            // Wait for both images to load
            let baseLoaded = false;
            let finalLoaded = false;
            
            const checkBothLoaded = () => {
                if (baseLoaded && finalLoaded) {
                    UI.toggleLoading(false, elements);
                    elements.initialView.classList.add('hidden');
                    elements.resultView.classList.remove('hidden');
                    if (uploadBtnTrigger) uploadBtnTrigger.style.display = 'flex';
                    
                    // --- REPLACEMENT: Use helper function ---
                    // Show all comparison elements (slider, badges, custom instructions bar)
                    showComparisonElements();
                    
                    // Enable custom instructions button after image is loaded
                    if (elements.applyInstructionsBtn && elements.customInstructionsInput) {
                        const hasText = elements.customInstructionsInput.value.trim().length > 0;
                        elements.applyInstructionsBtn.disabled = !hasText;
                    }
                    
                    // Save new state to history after images are loaded
                    imageHistory.save(data.final_image, data.original_image);
                    
                    // Sync sizes after a brief delay to ensure layout is complete
                    setTimeout(() => {
                        Editor.syncImageSizes(elements.baseImg, elements.finalImg);
                    }, 100);
                }
            };
            
            // Use helper function to set image src with cleanup and proper handlers
            setImageSrcWithCleanup(elements.storeOriginal, data.original_image);
            setImageSrcWithCleanup(elements.baseImg, data.original_image, () => {
                baseLoaded = true;
                checkBothLoaded();
            });
            setImageSrcWithCleanup(elements.finalImg, data.final_image, () => {
                finalLoaded = true;
                checkBothLoaded();
            });
            
            UI.updateStyleCardThumbnail(data.final_image);
        } catch (error) {
            alert(error.message);
            UI.toggleLoading(false, elements);
        }
    });

    // 4. Refine Design functionality removed - now handled by custom instructions bar

    // 5. Apply Custom Instructions (from typing bar)
    if (elements.applyInstructionsBtn && elements.customInstructionsInput) {
        // Initially disable the button until an image is generated
        elements.applyInstructionsBtn.disabled = true;
        
        const updateApplyButtonState = () => {
            const hasImage = elements.finalImg && elements.finalImg.src && elements.finalImg.src !== '';
            const hasText = elements.customInstructionsInput.value.trim().length > 0;
            elements.applyInstructionsBtn.disabled = !hasImage || !hasText;
        };
        
        // Update button state when text changes
        elements.customInstructionsInput.addEventListener('input', updateApplyButtonState);
        
        const applyCustomInstructions = async () => {
            const prompt = elements.customInstructionsInput.value.trim();
            if (!prompt) {
                alert('Please enter custom instructions');
                return;
            }
            
            // Check if we have a generated image
            if (!elements.finalImg || !elements.finalImg.src || elements.finalImg.src === '') {
                alert('Please generate a design first before applying custom instructions');
                return;
            }
            
            // Exit search furniture mode before generating new design
            exitSearchModeIfActive();
            
            // Get current base image to preserve it
            const currentBaseImage = elements.baseImg && elements.baseImg.src ? elements.baseImg.src : null;
            
            UI.toggleLoading(true, elements, "Applying custom instructions...");
            elements.applyInstructionsBtn.disabled = true;
            
            try {
                const data = await API.refineImage(elements.finalImg.src, prompt);
                
                // Use helper function to set image src with cleanup and proper handler
                setImageSrcWithCleanup(elements.finalImg, data.refined_image, () => {
                    UI.toggleLoading(false, elements);
                    elements.resultView.classList.remove('hidden');
                    
                    // --- REPLACEMENT: Use helper function ---
                    showComparisonElements();
                    
                    // Save new state to history after image is loaded
                    imageHistory.save(data.refined_image, currentBaseImage || data.refined_image);
                    
                    // Clear the input field after successful application
                    elements.customInstructionsInput.value = '';
                    updateApplyButtonState(); // This will disable the button since input is now empty
                    setTimeout(() => {
                        Editor.syncImageSizes(elements.baseImg, elements.finalImg);
                    }, 100);
                });
            } catch (error) {
                alert(error.message || 'Failed to apply custom instructions');
                UI.toggleLoading(false, elements);
                elements.resultView.classList.remove('hidden');
                updateApplyButtonState();
            }
        };
        
        elements.applyInstructionsBtn.addEventListener('click', applyCustomInstructions);
        
        // Allow Enter key to submit (Shift+Enter for new line, Enter to submit)
        elements.customInstructionsInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (!elements.applyInstructionsBtn.disabled) {
                    applyCustomInstructions();
                }
            }
        });
        
    }

    // 5. Non-functional buttons (present but not implemented)
    const historyBtn = document.getElementById('history-btn');
    const shareBtn = document.getElementById('share-btn');
    const undoBtn = document.getElementById('undo-btn');
    const downloadBtn = document.getElementById('download-btn');
    
    if (historyBtn) {
        historyBtn.addEventListener('click', () => {
            showHistoryModal();
        });
    }

    // Close history modal handlers
    const closeHistoryBtn = document.getElementById('close-history');
    const historyModal = document.getElementById('history-modal');
    
    if (closeHistoryBtn) {
        closeHistoryBtn.addEventListener('click', closeHistoryModal);
    }
    
    if (historyModal) {
        // Close on overlay click
        const overlay = historyModal.querySelector('.history-modal-overlay');
        if (overlay) {
            overlay.addEventListener('click', closeHistoryModal);
        }
        
        // Close on Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !historyModal.classList.contains('hidden')) {
                closeHistoryModal();
            }
        });
    }
    
    if (shareBtn) {
        shareBtn.addEventListener('click', () => {
            console.log('Share feature not yet implemented');
            // Placeholder for future implementation
        });
    }
    
    if (undoBtn) {
        undoBtn.addEventListener('click', () => {
            // Get previous state from history
            const previousState = imageHistory.undo();
            restoreImageState(previousState);
        });
    }

    // Redo button
    const redoBtn = document.getElementById('redo-btn');
    if (redoBtn) {
        redoBtn.addEventListener('click', () => {
            // Get next state from history
            const nextState = imageHistory.redo();
            restoreImageState(nextState);
        });
    }

    // Initialize button states
    imageHistory.updateButtons();
    
    if (downloadBtn) {
        downloadBtn.addEventListener('click', async () => {
            // Get the current image
            const currentImage = elements.finalImg;
            
            // Check if there's an image to download
            if (!currentImage || !currentImage.src || currentImage.src === '') {
                alert('No image available to download. Please upload and generate a design first.');
                return;
            }
            
            try {
                let blob;
                let filename = 'interior-design.jpg';
                
                // Check if it's a data URL or regular URL
                if (currentImage.src.startsWith('data:')) {
                    // Convert data URL to blob
                    const response = await fetch(currentImage.src);
                    blob = await response.blob();
                } else {
                    // Fetch the image from URL
                    const response = await fetch(currentImage.src);
                    blob = await response.blob();
                    
                    // Try to extract filename from URL if possible
                    const urlPath = new URL(currentImage.src).pathname;
                    const urlFilename = urlPath.split('/').pop();
                    if (urlFilename && urlFilename.includes('.')) {
                        filename = urlFilename;
                    }
                }
                
                // Create download link
                const url = window.URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = filename;
                document.body.appendChild(link);
                link.click();
                
                // Cleanup
                document.body.removeChild(link);
                window.URL.revokeObjectURL(url);
            } catch (error) {
                console.error('Error downloading image:', error);
                alert('Failed to download image. Please try again.');
            }
        });
    }

    // 6. Search Toggle
    elements.toggleSearchBtn.addEventListener('click', () => {
        const isNowActive = !elements.toggleSearchBtn.classList.contains('active');
        Editor.toggleSearchMode(isNowActive, elements);
    });

    elements.closeResultsBtn.addEventListener('click', () => {
        elements.resultsPanel.classList.add('hidden');
        elements.selectionBox.style.display = 'none';
        // Exit search mode when closing results
        if (elements.toggleSearchBtn.classList.contains('active')) {
            Editor.toggleSearchMode(false, elements);
        }
    });

    // ESC key to exit search mode
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && elements.toggleSearchBtn.classList.contains('active')) {
            Editor.toggleSearchMode(false, elements);
        }
    });

    // 7. Style Selection
    // A. Handle standard style cards (Exclude the add-new-style button)
    document.querySelectorAll('.style-card:not(.add-new-style)').forEach(card => {
        card.addEventListener('click', () => {
            document.querySelectorAll('.style-card').forEach(c => {
                c.classList.remove('active');
                const checkIcon = c.querySelector('.check-icon');
                if (checkIcon) checkIcon.style.display = 'none';
            });
            card.classList.add('active');
            const checkIcon = card.querySelector('.check-icon');
            if (checkIcon) checkIcon.style.display = 'flex';
            elements.styleInput.value = card.dataset.style;
        });
    });
    
    // Initialize check icons visibility for active card
    const activeStyleCard = document.querySelector('.style-card.active');
    if (activeStyleCard) {
        const checkIcon = activeStyleCard.querySelector('.check-icon');
        if (checkIcon) {
            checkIcon.style.display = 'flex';
        }
    }
    
    // Hide check icons for non-active cards
    document.querySelectorAll('.style-card:not(.active) .check-icon').forEach(icon => {
        icon.style.display = 'none';
    });

    // B. Handle "Add Custom" Button
    if (elements.addStyleBtn) {
        elements.addStyleBtn.addEventListener('click', (e) => {
            e.stopPropagation(); // Stop bubbling

            // 1. Open the Prompt Window
            const customStyle = prompt("Enter a custom interior style (e.g., 'Cyberpunk', 'Baroque', 'Vaporwave'):");

            // 2. If user typed something and didn't cancel
            if (customStyle && customStyle.trim() !== "") {
                
                // Pass null to trigger the "Pending/?" state in the UI
                UI.addCustomStyleToGrid(
                    customStyle.trim(), 
                    null,
                    elements.styleGrid, 
                    elements.styleInput
                );
            }
        });
    }

    // Window Resize Handler with debouncing for performance
    let resizeTimeout;
    window.addEventListener('resize', () => {
        // Clear previous timeout to debounce resize events
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
            if (elements.resultView && !elements.resultView.classList.contains('hidden')) {
                // Recalculate base image width when window resizes
                Editor.syncImageSizes(elements.baseImg, elements.finalImg);
            }
        }, 150); // Wait 150ms after last resize event
    });
});