/* static/js/modules/ui.js */

export const elements = {
    // We export this selector helper or the object itself
    // But for simplicity, we'll let main.js grab elements or pass them in.
    // Here we define pure UI functions.
};

export function toggleLoading(isLoading, elements, text = "") {
    if (isLoading) {
        elements.loadingMsg.classList.remove('hidden');
    } else {
        elements.loadingMsg.classList.add('hidden');
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
        container.innerHTML = '<p>No matching furniture found.</p>';
        return;
    }

    products.forEach(p => {
        const imgUrl = p.image_url || 'static/assets/placeholder.jpg';
        const query = encodeURIComponent(p.search_query || '');
        const googleSearchUrl = `https://www.google.com/search?q=${query}`;

        const card = document.createElement('div');
        card.className = 'product-card';

        const thumb = document.createElement('img');
        thumb.src = imgUrl;
        thumb.alt = 'Product';
        thumb.style.width = '70px';
        thumb.style.height = '70px';
        thumb.style.objectFit = 'cover';
        thumb.style.borderRadius = '4px';

        const info = document.createElement('div');
        info.className = 'product-info';
        info.style.flex = '1';
        info.style.marginLeft = '10px';

        const titleEl = document.createElement('h4');
        titleEl.style.margin = '0 0 4px 0';
        const link = document.createElement('a');
        link.href = googleSearchUrl;
        link.target = '_blank';
        link.style.color = 'white';
        link.style.textDecoration = 'none';
        link.style.borderBottom = '1px solid #555';
        link.textContent = p.title || 'View item';
        titleEl.appendChild(link);

        const meta = document.createElement('div');
        meta.style.fontSize = '0.8rem';
        meta.style.color = '#ccc';
        meta.style.display = 'flex';
        meta.style.flexDirection = 'column';
        meta.style.gap = '2px';

        const priceEl = document.createElement('span');
        priceEl.style.color = '#4CAF50';
        priceEl.style.fontWeight = 'bold';
        priceEl.textContent = p.price || 'N/A';

        const sourceEl = document.createElement('span');
        sourceEl.style.color = '#888';
        sourceEl.textContent = p.source || '';

        const scoreEl = document.createElement('span');
        scoreEl.style.fontSize = '0.7rem';
        scoreEl.style.opacity = '0.6';
        scoreEl.textContent = `Match: ${((p.score || 0) * 100).toFixed(0)}%`;

        meta.appendChild(priceEl);
        meta.appendChild(sourceEl);
        meta.appendChild(scoreEl);

        info.appendChild(titleEl);
        info.appendChild(meta);

        card.appendChild(thumb);
        card.appendChild(info);
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