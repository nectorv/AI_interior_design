/* static/js/modules/ui.js */

export const elements = {
    // We export this selector helper or the object itself
    // But for simplicity, we'll let main.js grab elements or pass them in.
    // Here we define pure UI functions.
};

export function toggleLoading(isLoading, elements, text = "") {
    if (isLoading) {
        elements.loadingMsg.classList.remove('hidden');
        
        // Show old image in background with transparency
        if (elements.loadingBackground) {
            // Try to get the current image to show - prioritize finalImg, then baseImg, then storeOriginal
            let oldImageSrc = null;
            if (elements.finalImg && elements.finalImg.src && elements.finalImg.src !== '') {
                oldImageSrc = elements.finalImg.src;
            } else if (elements.baseImg && elements.baseImg.src && elements.baseImg.src !== '') {
                oldImageSrc = elements.baseImg.src;
            } else if (elements.storeOriginal && elements.storeOriginal.src && elements.storeOriginal.src !== '') {
                oldImageSrc = elements.storeOriginal.src;
            }
            
            if (oldImageSrc) {
                elements.loadingBackground.style.backgroundImage = `url(${oldImageSrc})`;
                elements.loadingBackground.classList.remove('hidden');
            }
        }
    } else {
        elements.loadingMsg.classList.add('hidden');
        
        // Hide background image when loading ends
        if (elements.loadingBackground) {
            elements.loadingBackground.classList.add('hidden');
        }
    }
    elements.loadingText.textContent = text;
    elements.processBtn.disabled = isLoading;
    if (elements.refineBtn) {
        elements.refineBtn.disabled = isLoading;
    }

    if (isLoading) {
        elements.initialView.classList.add('hidden');
        elements.resultView.classList.add('hidden');
    }
}

export function switchView(viewType, elements) {
    document.querySelectorAll('.tab').forEach(t => {
        t.classList.toggle('active', t.dataset.view === viewType);
    });

    if (viewType === 'original') elements.baseImg.src = elements.storeOriginal.src;
}

export function renderSearchResults(products, container) {
    container.innerHTML = '';
    
    if (!products || products.length === 0) {
        container.innerHTML = '<div class="no-results"><p>No matching furniture found.</p></div>';
        return;
    }

    products.forEach(p => {
        const imgUrl = p.image_url || 'static/assets/placeholder.jpg';
        const query = encodeURIComponent(p.search_query || '');
        const googleSearchUrl = `https://www.google.com/search?q=${query}`;
        const matchScore = ((p.score || 0) * 100).toFixed(0);

        const card = document.createElement('a');
        card.className = 'product-card';
        card.href = googleSearchUrl;
        card.target = '_blank';
        card.rel = 'noopener noreferrer';

        // Image container with match badge
        const imageContainer = document.createElement('div');
        imageContainer.className = 'product-image-container';
        
        const thumb = document.createElement('img');
        thumb.src = imgUrl;
        thumb.alt = p.title || 'Product';
        thumb.className = 'product-image';
        thumb.loading = 'lazy';

        // Match score badge
        const matchBadge = document.createElement('div');
        matchBadge.className = 'match-badge';
        matchBadge.textContent = `${matchScore}% match`;
        
        imageContainer.appendChild(thumb);
        imageContainer.appendChild(matchBadge);

        // Content container
        const content = document.createElement('div');
        content.className = 'product-content';

        const titleEl = document.createElement('h4');
        titleEl.className = 'product-title';
        titleEl.textContent = p.title || 'View item';

        const meta = document.createElement('div');
        meta.className = 'product-meta';

        // Price
        if (p.price && p.price !== 'N/A') {
            const priceEl = document.createElement('div');
            priceEl.className = 'product-price';
            priceEl.textContent = p.price;
            meta.appendChild(priceEl);
        }

        // Source
        if (p.source) {
            const sourceEl = document.createElement('div');
            sourceEl.className = 'product-source';
            sourceEl.textContent = p.source;
            meta.appendChild(sourceEl);
        }

        // External link indicator
        const linkIndicator = document.createElement('div');
        linkIndicator.className = 'link-indicator';
        linkIndicator.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>';

        content.appendChild(titleEl);
        content.appendChild(meta);
        content.appendChild(linkIndicator);

        card.appendChild(imageContainer);
        card.appendChild(content);
        container.appendChild(card);
    });
}

export function updateStyleCardThumbnail(imageUrl) {
    // 1. Find the active card wrapper
    const activeCard = document.querySelector('.style-card.active');
    
    if (activeCard) {
        // 2. Find the image inside
        const img = activeCard.querySelector('img');
        if (img) {
            img.src = imageUrl;
            img.style.display = 'block'; // Ensure it's visible if it was hidden
            // 3. Remove the pending class (removes the '?')
            activeCard.classList.remove('pending');
        }
    }
}

export function addCustomStyleToGrid(styleName, imageUrl, gridElement, styleInput) {
    // 1. Create the new card element
    const newCard = document.createElement('div');
    
    // Check if we have an image. If not, add 'pending' class.
    if (!imageUrl) {
        newCard.className = 'style-card active pending'; 
    } else {
        newCard.className = 'style-card active';
    }
    
    newCard.dataset.style = styleName;

    // 2. Use a placeholder logic for the src, though CSS will hide it if pending
    const thumbSrc = imageUrl || 'static/assets/placeholder.jpg'; 

    newCard.innerHTML = `
        <img src="${thumbSrc}" alt="${styleName}">
        <div class="style-name">${styleName}</div>
        <div class="check-icon" style="display: flex;">✓</div>
    `;

    // 3. Remove 'active' class from all other cards and hide their check icons
    document.querySelectorAll('.style-card').forEach(c => {
        c.classList.remove('active');
        const checkIcon = c.querySelector('.check-icon');
        if (checkIcon) checkIcon.style.display = 'none';
    });

    // 4. Update the hidden input value immediately
    styleInput.value = styleName;

    // 5. Add Click Listener
    newCard.addEventListener('click', () => {
        document.querySelectorAll('.style-card').forEach(c => {
            c.classList.remove('active');
            const checkIcon = c.querySelector('.check-icon');
            if (checkIcon) checkIcon.style.display = 'none';
        });
        newCard.classList.add('active');
        const checkIcon = newCard.querySelector('.check-icon');
        if (checkIcon) checkIcon.style.display = 'flex';
        styleInput.value = styleName;
    });

    // 6. Insert before the "Add New" button
    const addBtn = document.getElementById('add-style-btn');
    gridElement.insertBefore(newCard, addBtn);
}