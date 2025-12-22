/* static/js/modules/editor.js */

let isDrawing = false;
let startX = 0, startY = 0;
let isSearchMode = false;

// --- Slider Logic ---
export function initSlider(box, overlay, sliderHandle) {
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

    // Mouse
    box.addEventListener('mousedown', () => active = true);
    window.addEventListener('mouseup', () => active = false);
    window.addEventListener('mousemove', move);

    // Touch
    box.addEventListener('touchstart', () => active = true);
    window.addEventListener('touchend', () => active = false);
    window.addEventListener('touchmove', move);
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
        elements.overlay.style.width = '100%'; 
        elements.overlay.style.borderRight = 'none';
        elements.slider.style.display = 'none';
        elements.selectionLayer.classList.remove('hidden');
        elements.selectionBox.style.display = 'none';
    } else {
        elements.overlay.style.width = '50%';
        elements.slider.style.left = '50%';
        elements.overlay.style.borderRight = '2px solid white';
        elements.slider.style.display = 'flex';
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
            left: parseFloat(box.style.left),
            top: parseFloat(box.style.top),
            width: parseFloat(box.style.width),
            height: parseFloat(box.style.height)
        };

        if (visualBox.width < 20 || visualBox.height < 20) {
            box.style.display = 'none';
            return;
        }

        // Calculate scaling
        const displayedW = elements.baseImg.getBoundingClientRect().width;
        const naturalW = elements.finalImg.naturalWidth;
        const scale = naturalW / displayedW;

        const backendBox = {
            x: visualBox.left * scale,
            y: visualBox.top * scale,
            width: visualBox.width * scale,
            height: visualBox.height * scale
        };

        onSelectionComplete(backendBox);
    });
}