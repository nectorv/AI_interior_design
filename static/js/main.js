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
        toggleSearchBtn: document.getElementById('toggle-search-btn'),
        selectionLayer: document.getElementById('selection-layer'),
        selectionBox: document.getElementById('selection-box'),
        resultsPanel: document.getElementById('search-results-panel'),
        resultsGrid: document.getElementById('results-grid'),
        closeResultsBtn: document.getElementById('close-results'),
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
            // Hide initial view - result view will show after generation
            elements.initialView.classList.add('hidden');
            elements.processBtn.disabled = false;
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

    // 3. Generate Design
    elements.processBtn.addEventListener('click', async () => {
        if (!selectedFile) return;
        UI.toggleLoading(true, elements, "Generating new interior...");
        
        try {
            const data = await API.redesignImage(selectedFile, elements.styleInput.value, elements.roomType.value);
            
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

    // 4. Refine Design
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
        downloadBtn.addEventListener('click', () => {
            console.log('Download feature not yet implemented');
            // Placeholder for future implementation
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