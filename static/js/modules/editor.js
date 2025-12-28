/* static/js/modules/editor.js */

let isDrawing = false;
let startX = 0, startY = 0;
let isSearchMode = false;

// Store event listener references for cleanup
let sliderListeners = {
    mouseup: null,
    mousemove: null,
    touchend: null,
    touchmove: null
};

// --- Slider Logic ---
export function initSlider(box, overlay, sliderHandle) {
    // Clean up previous listeners if they exist
    cleanupSliderListeners();

    let active = false;

    const move = (e) => {
        if (isSearchMode || !active) return; // Block slider if searching

        const clientX = e.touches ? e.touches[0].clientX : e.clientX;
        const rect = box.getBoundingClientRect();
        let x = clientX - rect.left;

        if (x < 0) x = 0;
        if (x > rect.width) x = rect.width;

        overlay.style.width = x + "px";
        sliderHandle.style.left = x + "px";
    };

    const handleMouseUp = () => active = false;
    const handleTouchEnd = () => active = false;

    // Mouse
    box.addEventListener('mousedown', () => active = true);
    sliderListeners.mouseup = handleMouseUp;
    sliderListeners.mousemove = move;
    window.addEventListener('mouseup', sliderListeners.mouseup);
    window.addEventListener('mousemove', sliderListeners.mousemove);

    // Touch
    box.addEventListener('touchstart', () => active = true);
    sliderListeners.touchend = handleTouchEnd;
    sliderListeners.touchmove = move;
    window.addEventListener('touchend', sliderListeners.touchend);
    window.addEventListener('touchmove', sliderListeners.touchmove);
}

// Cleanup function to remove event listeners
export function cleanupSliderListeners() {
    if (sliderListeners.mouseup) {
        window.removeEventListener('mouseup', sliderListeners.mouseup);
        sliderListeners.mouseup = null;
    }
    if (sliderListeners.mousemove) {
        window.removeEventListener('mousemove', sliderListeners.mousemove);
        sliderListeners.mousemove = null;
    }
    if (sliderListeners.touchend) {
        window.removeEventListener('touchend', sliderListeners.touchend);
        sliderListeners.touchend = null;
    }
    if (sliderListeners.touchmove) {
        window.removeEventListener('touchmove', sliderListeners.touchmove);
        sliderListeners.touchmove = null;
    }
}

export function syncImageSizes(baseImg, finalImg) {
    // Set base image width to match comparison-box width exactly
    // This prevents the image from shrinking when overlay width changes
    if (baseImg && finalImg && finalImg.complete && baseImg.complete) {
        const comparisonBox = baseImg.closest('.comparison-box');
        if (!comparisonBox) return;
        
        const boxRect = comparisonBox.getBoundingClientRect();
        
        // Set base image width to match the comparison box width
        // This ensures it stays the same size regardless of overlay width
        baseImg.style.width = boxRect.width + 'px';
        baseImg.style.height = '100%';
        baseImg.style.maxWidth = 'none';
        
        // Both images use object-fit: cover and height: 100%
        // The overlay just clips the base image, it doesn't resize it
    }
}

// --- Search/Cropping Logic ---
export function toggleSearchMode(active, elements) {
    isSearchMode = active;
    elements.toggleSearchBtn.classList.toggle('active', active);

    if (active) {
        // Hide overlay to show the final (new) image, not the original
        elements.overlay.style.display = 'none';
        elements.slider.style.display = 'none';
        // Hide custom instructions bar when using furniture searcher
        if (elements.customInstructionsBar) {
            elements.customInstructionsBar.classList.add('hidden');
        }
        elements.selectionLayer.classList.remove('hidden');
        elements.selectionBox.style.display = 'none';
        // Ensure final image is visible
        if (elements.finalImg) {
            elements.finalImg.style.display = 'block';
        }
    } else {
        // Show overlay again for comparison view
        // BUT only if slider is not supposed to be hidden (check for hidden class)
        if (!elements.slider.classList.contains('hidden')) {
            elements.overlay.style.display = 'block';
            elements.overlay.style.width = '50%';
            elements.slider.style.left = '50%';
            elements.overlay.style.borderRight = '2px solid white';
            elements.slider.style.display = 'flex';
        }
        // Show custom instructions bar again when exiting search mode
        // Only show if it was previously visible (not hidden by other logic)
        if (elements.customInstructionsBar && elements.finalImg && elements.finalImg.src) {
            elements.customInstructionsBar.classList.remove('hidden');
        }
        elements.selectionLayer.classList.add('hidden');
        elements.selectionBox.style.display = 'none';
        elements.resultsPanel.classList.add('hidden');
    }
}

export function initDrawing(elements, onSelectionComplete) {
    const layer = elements.selectionLayer;
    const box = elements.selectionBox;

    layer.addEventListener('mousedown', (e) => {
        isDrawing = true;
        const rect = layer.getBoundingClientRect();
        startX = e.clientX - rect.left;
        startY = e.clientY - rect.top;
        
        box.style.display = 'block';
        box.style.width = '0px';
        box.style.height = '0px';
        box.style.left = startX + 'px';
        box.style.top = startY + 'px';
    });

    layer.addEventListener('mousemove', (e) => {
        if (!isDrawing) return;
        const rect = layer.getBoundingClientRect();
        const currentX = e.clientX - rect.left;
        const currentY = e.clientY - rect.top;

        const width = Math.abs(currentX - startX);
        const height = Math.abs(currentY - startY);
        const left = Math.min(currentX, startX);
        const top = Math.min(currentY, startY);

        box.style.width = width + 'px';
        box.style.height = height + 'px';
        box.style.left = left + 'px';
        box.style.top = top + 'px';
    });

    layer.addEventListener('mouseup', () => {
        isDrawing = false;
        
        // Calculate data for backend
        const visualBox = {
            left: parseFloat(box.style.left) || 0,
            top: parseFloat(box.style.top) || 0,
            width: parseFloat(box.style.width) || 0,
            height: parseFloat(box.style.height) || 0
        };

        if (visualBox.width < 20 || visualBox.height < 20) {
            box.style.display = 'none';
            return;
        }

        // Calculate scaling - use final image since that's what we're searching on
        const finalImgRect = elements.finalImg.getBoundingClientRect();
        const displayedW = finalImgRect.width;
        const naturalW = elements.finalImg.naturalWidth;
        
        // Ensure we have valid dimensions
        if (!displayedW || !naturalW || displayedW <= 0 || naturalW <= 0) {
            console.error('Invalid image dimensions for scaling');
            box.style.display = 'none';
            return;
        }
        
        const scale = naturalW / displayedW;

        const backendBox = {
            x: visualBox.left * scale,
            y: visualBox.top * scale,
            width: visualBox.width * scale,
            height: visualBox.height * scale
        };
        
        // Validate backend box values
        if (!backendBox.x || !backendBox.y || !backendBox.width || !backendBox.height ||
            isNaN(backendBox.x) || isNaN(backendBox.y) || isNaN(backendBox.width) || isNaN(backendBox.height)) {
            console.error('Invalid backend box values:', backendBox);
            box.style.display = 'none';
            return;
        }

        onSelectionComplete(backendBox);
    });
}