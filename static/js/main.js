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
        comparisonBox: document.getElementById('comparison-box'),
        overlay: document.getElementById('overlay'),
        slider: document.getElementById('slider'),
        baseImg: document.getElementById('base-image'),
        finalImg: document.getElementById('final-image'),
        storeOriginal: document.getElementById('store-original'),
        refineBtn: document.getElementById('refine-button'),
        refineInput: document.getElementById('refine-prompt'),
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
    };

    let selectedFile = null;
    elements.addStyleBtn = document.getElementById('add-style-btn'); 
    elements.styleGrid = document.querySelector('.style-grid');
    const uploadBtnTrigger = document.getElementById('upload-btn-trigger');

    // --- Initialization ---
    Editor.initSlider(elements.comparisonBox, elements.overlay, elements.slider);
    
    // Initialize Drawing logic with a callback for what to do when finished
    Editor.initDrawing(elements, async (backendBox) => {
        elements.resultsPanel.classList.remove('hidden');
        elements.resultsGrid.innerHTML = '<p style="text-align:center;">Searching...</p>';
        
        try {
            const data = await API.searchFurniture(elements.finalImg.src, backendBox);
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

        // 3. Hide Static Badges
        const beforeBadge = document.querySelector('.badge-before-static');
        const afterBadge = document.querySelector('.badge-after-static');
        
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

        // 3. Show Static Badges
        const beforeBadge = document.querySelector('.badge-before-static');
        const afterBadge = document.querySelector('.badge-after-static');

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
            elements.baseImg.src = imageDataUrl;
            elements.finalImg.src = imageDataUrl; // Show same image initially
            elements.storeOriginal.src = imageDataUrl;
            
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
            
            // Wait for image to load, then sync sizes
            elements.baseImg.onload = () => {
                Editor.syncImageSizes(elements.baseImg, elements.finalImg);
                // Ensure comparison elements stay hidden after image loads (slider and badges)
                hideComparisonElements();
                // Show custom instructions bar after image is uploaded
                if (elements.customInstructionsBar) {
                    elements.customInstructionsBar.classList.remove('hidden');
                }
            };
            
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
        
        UI.toggleLoading(true, elements, loadingMessage);
        
        try {
            const data = await API.redesignImage(
                selectedFile, 
                elements.styleInput.value, 
                elements.roomType.value,
                emptyThenGenerate
            );
            
            elements.storeOriginal.src = data.original_image;
            elements.baseImg.src = data.original_image;
            elements.finalImg.src = data.final_image;
            
            UI.updateStyleCardThumbnail(data.final_image);

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
                    
                    // Sync sizes after a brief delay to ensure layout is complete
                    setTimeout(() => {
                        Editor.syncImageSizes(elements.baseImg, elements.finalImg);
                    }, 100);
                }
            };
            
            elements.baseImg.onload = () => {
                baseLoaded = true;
                checkBothLoaded();
            };
            
            elements.finalImg.onload = () => {
                finalLoaded = true;
                checkBothLoaded();
            };
        } catch (error) {
            alert(error.message);
            UI.toggleLoading(false, elements);
        }
    });

    // 4. Refine Design (from Advanced Options)
    if (elements.refineBtn) {
        elements.refineBtn.addEventListener('click', async () => {
            const prompt = elements.refineInput.value.trim();
            if (!prompt) return;
            
            UI.toggleLoading(true, elements, "Refining details...");
            try {
                const data = await API.refineImage(elements.finalImg.src, prompt);
                elements.finalImg.src = data.refined_image;
                elements.refineInput.value = '';
                
                elements.finalImg.onload = () => {
                    UI.toggleLoading(false, elements);
                    elements.resultView.classList.remove('hidden');
                    
                    // --- REPLACEMENT: Use helper function ---
                    showComparisonElements();
                    
                    setTimeout(() => {
                        Editor.syncImageSizes(elements.baseImg, elements.finalImg);
                    }, 100);
                };
            } catch (error) {
                alert(error.message);
                UI.toggleLoading(false, elements);
                elements.resultView.classList.remove('hidden');
            }
        });
    }

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
            
            UI.toggleLoading(true, elements, "Applying custom instructions...");
            elements.applyInstructionsBtn.disabled = true;
            
            try {
                const data = await API.refineImage(elements.finalImg.src, prompt);
                elements.finalImg.src = data.refined_image;
                
                elements.finalImg.onload = () => {
                    UI.toggleLoading(false, elements);
                    elements.resultView.classList.remove('hidden');
                    
                    // --- REPLACEMENT: Use helper function ---
                    showComparisonElements();
                    
                    // Clear the input field after successful application
                    elements.customInstructionsInput.value = '';
                    updateApplyButtonState(); // This will disable the button since input is now empty
                    setTimeout(() => {
                        Editor.syncImageSizes(elements.baseImg, elements.finalImg);
                    }, 100);
                };
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
            console.log('History feature not yet implemented');
            // Placeholder for future implementation
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
            console.log('Undo feature not yet implemented');
            // Placeholder for future implementation
        });
    }
    
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

    // Window Resize Handler
    window.addEventListener('resize', () => {
        if (elements.resultView && !elements.resultView.classList.contains('hidden')) {
            // Recalculate base image width when window resizes
            Editor.syncImageSizes(elements.baseImg, elements.finalImg);
        }
    });
});