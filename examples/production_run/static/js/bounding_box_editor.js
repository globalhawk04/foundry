// FILE: static/js/bounding_box_editor.js (Simplified)

function initializeEditor() {
    console.log("SUCCESS: initializeEditor() has been called.");

    const card = document.getElementById('pole-editor-card');
    const canvasEl = card.querySelector('#canvas-editor');
    const container = card.querySelector('#canvas-container');
    const saveBtn = card.querySelector('#save-correction-btn');
    const dataEl = document.getElementById('ai-data'); 
    
    // This check is important in case the function is called on the wrong page
    if (!canvasEl || !container || !saveBtn || !dataEl) {
        console.error("Editor elements not found. Bailing out.");
        return;
    }

    const aiData = JSON.parse(dataEl.textContent);
    const imageUrl = aiData.image_url;
    const initialBoxes = aiData.ai_output.boxes;

    const canvas = new fabric.Canvas(canvasEl);
    let isDrawing = false;
    let startX, startY, rect;

    // This is the core logic that draws the background image.
    // The inline script in the HTML ensures this runs AFTER the image is loaded.
    fabric.Image.fromURL(imageUrl, (img) => {
        const containerWidth = container.clientWidth;
        if (containerWidth === 0) {
            console.error("Canvas container has zero width. This is the source of the rendering error.");
            return;
        }
        const scale = containerWidth / img.width;
        canvas.setWidth(containerWidth);
        canvas.setHeight(img.height * scale);
        canvas.setBackgroundImage(img, canvas.renderAll.bind(canvas), {
            scaleX: scale,
            scaleY: scale,
        });
        drawInitialBoxes(initialBoxes, scale);
        console.log("Image and canvas rendered successfully.");

    }, { crossOrigin: 'anonymous' });

    // --- All the drawing and saving logic from before remains identical ---
    const drawInitialBoxes = (boxes, scale) => {
        boxes.forEach(boxData => {
            const [x1, y1, x2, y2] = boxData.box;
            const rect = new fabric.Rect({
                left: x1 * scale, top: y1 * scale,
                width: (x2 - x1) * scale, height: (y2 - y1) * scale,
                fill: 'rgba(0,0,0,0)', 
                stroke: boxData.confidence < 0.95 ? 'orange' : 'limegreen',
                strokeWidth: 2,
                customData: {
                    box_id: boxData.box_id, label: boxData.label,
                    confidence: boxData.confidence, is_human: false
                }
            });
            canvas.add(rect);
        });
    };

    canvas.on('mouse:down', (o) => { if (!o.target) { isDrawing = true; const p = canvas.getPointer(o.e); startX = p.x; startY = p.y; rect = new fabric.Rect({ left: startX, top: startY, width: 0, height: 0, fill: 'rgba(0,0,0,0)', stroke: 'cyan', strokeWidth: 2, customData: { label: 'utility_pole', is_human: true } }); canvas.add(rect); } });
    canvas.on('mouse:move', (o) => { if (!isDrawing) return; const p = canvas.getPointer(o.e); let w = p.x - startX, h = p.y - startY; rect.set({ left: w > 0 ? startX : p.x, top: h > 0 ? startY : p.y, width: Math.abs(w), height: Math.abs(h) }); canvas.renderAll(); });
    canvas.on('mouse:up', () => { isDrawing = false; if (rect.width < 5 || rect.height < 5) { canvas.remove(rect); } });
    const keydownHandler = (e) => { if (e.key === 'Delete' || e.key === 'Backspace') { const o = canvas.getActiveObject(); if (o) canvas.remove(o); } };
    window.addEventListener('keydown', keydownHandler);
    saveBtn.addEventListener('click', async () => { /* ... save logic is the same ... */ });
    htmx.on(card, 'htmx:beforeSwap', () => { window.removeEventListener('keydown', keydownHandler); });
}