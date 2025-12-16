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
        storeEmpty: document.getElementById('store-empty'),
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
    elements.dropArea.addEventListener('click', () => elements.fileInput.click());
    elements.fileInput.addEventListener('change', (e) => {
        if (e.target.files[0]) {
            selectedFile = e.target.files[0];
            const reader = new FileReader();
            reader.onload = (ev) => {
                elements.dropArea.innerHTML = `<img src="${ev.target.result}" style="width:100%; height:100%; object-fit:cover; border-radius:8px;">`;
                elements.processBtn.disabled = false;
            };
            reader.readAsDataURL(selectedFile);
        }
    });

    // 2. Generate Design
    elements.processBtn.addEventListener('click', async () => {
        if (!selectedFile) return;
        UI.toggleLoading(true, elements, "Generating new interior...");
        
        try {
            const data = await API.redesignImage(selectedFile, elements.styleInput.value, elements.roomType.value);
            
            elements.storeOriginal.src = data.original_image;
            elements.storeEmpty.src = data.empty_image;
            elements.baseImg.src = data.original_image;
            elements.finalImg.src = data.final_image;
            
            UI.updateStyleCardThumbnail(data.final_image);

            elements.baseImg.onload = () => {
                UI.toggleLoading(false, elements);
                elements.resultView.classList.remove('hidden');
                Editor.syncImageSizes(elements.baseImg, elements.finalImg);
            };
        } catch (error) {
            alert(error.message);
            UI.toggleLoading(false, elements);
        }
    });

    // 3. Refine Design
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
                Editor.syncImageSizes(elements.baseImg, elements.finalImg);
            };
        } catch (error) {
            alert(error.message);
            UI.toggleLoading(false, elements);
            elements.resultView.classList.remove('hidden');
        }
    });

    // 4. View Tabs
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', (e) => {
            UI.switchView(e.target.dataset.view, elements);
            // Re-sync size after switching images
            requestAnimationFrame(() => Editor.syncImageSizes(elements.baseImg, elements.finalImg));
        });
    });

    // 5. Search Toggle
    elements.toggleSearchBtn.addEventListener('click', () => {
        const isNowActive = !elements.toggleSearchBtn.classList.contains('active');
        Editor.toggleSearchMode(isNowActive, elements);
    });

    elements.closeResultsBtn.addEventListener('click', () => {
        elements.resultsPanel.classList.add('hidden');
        elements.selectionBox.style.display = 'none';
    });

    // 6. Style Selection
    // A. Handle standard style cards (Exclude the add-new-style button)
    document.querySelectorAll('.style-card:not(.add-new-style)').forEach(card => {
        card.addEventListener('click', () => {
            document.querySelectorAll('.style-card').forEach(c => c.classList.remove('active'));
            card.classList.add('active');
            elements.styleInput.value = card.dataset.style;
        });
    });

    // B. Handle "Add Custom" Button
    // B. Handle "Add Custom" Button
    if (elements.addStyleBtn) {
        elements.addStyleBtn.addEventListener('click', (e) => {
            e.stopPropagation(); // Stop bubbling

            // 1. Open the Prompt Window
            const customStyle = prompt("Enter a custom interior style (e.g., 'Cyberpunk', 'Baroque', 'Vaporwave'):");

            // 2. If user typed something and didn't cancel
            if (customStyle && customStyle.trim() !== "") {
                
                // CHANGE: We pass null instead of elements.finalImg.src
                // This triggers the "Pending/?" state in the UI
                UI.addCustomStyleToGrid(
                    customStyle.trim(), 
                    null, // <--- CHANGED THIS
                    elements.styleGrid, 
                    elements.styleInput
                );
            }
        });
    }

    // Window Resize Handler
    window.addEventListener('resize', () => Editor.syncImageSizes(elements.baseImg, elements.finalImg));
});