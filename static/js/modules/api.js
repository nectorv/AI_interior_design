/* static/js/modules/api.js */

export async function redesignImage(file, style, roomType, emptyThenGenerate = false, additionalInstructions = '') {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('style', style);
    formData.append('room_type', roomType);
    formData.append('empty_then_generate', emptyThenGenerate ? 'true' : 'false');
    if (additionalInstructions) {
        formData.append('additional_instructions', additionalInstructions);
    }

    const response = await fetch('/api/redesign', { method: 'POST', body: formData });
    return handleResponse(response);
}

export async function refineImage(imageData, prompt) {
    const response = await fetch('/api/refine', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image_data: imageData, prompt: prompt })
    });
    return handleResponse(response);
}

export async function searchFurniture(file, box) {
    const formData = new FormData();
    formData.append('image', file);
    formData.append('box_x', box.x);
    formData.append('box_y', box.y);
    formData.append('box_width', box.width);
    formData.append('box_height', box.height);

    const response = await fetch('/api/search-furniture', {
        method: 'POST',
        body: formData
    });
    return handleResponse(response);
}

// Helper to check for errors uniformly
async function handleResponse(response) {
    const data = await response.json();
    if (!response.ok || data.error) {
        throw new Error(data.error || `Request failed: ${response.status}`);
    }
    return data;
}