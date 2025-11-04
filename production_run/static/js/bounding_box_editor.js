// FILE: static/js/bounding_box_editor.js (Corrected and Simplified)

function initializeEditor() {
    console.log("Attempting to initialize Bounding Box Editor...");

    const card = document.getElementById('pole-editor-card');
    if (!card) {
        console.error("Initialization failed: pole-editor-card not found in DOM.");
        return;
    }

    const canvasEl = card.querySelector('#canvas-editor');
    const container = card.querySelector('#canvas-container');
    const saveBtn = card.querySelector('#save-correction-btn');
    const dataEl = document.getElementById('ai-data'); 
    
    if (!canvasEl || !container || !saveBtn || !dataEl) {
        console.error("Editor elements not found! Bailing out.", { canvasEl, container, saveBtn, dataEl });
        return;
    }

    const aiData = JSON.parse(dataEl.textContent);
    const imageUrl = aiData.image_url;
    const initialBoxes = aiData.ai_output.boxes;

    const canvas = new fabric.Canvas(canvasEl);
    let isDrawing = false;
    let startX, startY, rect;

    const setCanvasDimensions = (img) => {
        const containerWidth = container.clientWidth;
        if (containerWidth === 0) {
            console.error("Canvas container has zero width. Cannot render.");
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
        console.log("SUCCESS: Canvas initialized and image loaded.");
    };

    fabric.Image.fromURL(imageUrl, setCanvasDimensions, { crossOrigin: 'anonymous' });

    const drawInitialBoxes = (boxes, scale) => {
        boxes.forEach(boxData => {
            const [x1, y1, x2, y2] = boxData.box;
            const confidence = boxData.confidence;
            const rect = new fabric.Rect({
                left: x1 * scale, top: y1 * scale,
                width: (x2 - x1) * scale, height: (y2 - y1) * scale,
                fill: 'rgba(0,0,0,0)', stroke: confidence < 0.95 ? 'orange' : 'limegreen',
                strokeWidth: 2,
                customData: {
                    box_id: boxData.box_id, label: boxData.label,
                    confidence: confidence, is_human: false
                }
            });
            canvas.add(rect);
        });
    };

    canvas.on('mouse:down', function(o) {
        if (o.target) return;
        isDrawing = true;
        const pointer = canvas.getPointer(o.e);
        startX = pointer.x; startY = pointer.y;
        rect = new fabric.Rect({
            left: startX, top: startY, width: 0, height: 0,
            fill: 'rgba(0,0,0,0)', stroke: 'cyan', strokeWidth: 2,
            customData: { label: 'utility_pole', is_human: true }
        });
        canvas.add(rect);
    });

    canvas.on('mouse:move', function(o) {
        if (!isDrawing) return;
        const pointer = canvas.getPointer(o.e);
        let width = pointer.x - startX; let height = pointer.y - startY;
        rect.set({ 
            left: width > 0 ? startX : pointer.x, top: height > 0 ? startY : pointer.y,
            width: Math.abs(width), height: Math.abs(height) 
        });
        canvas.renderAll();
    });

    canvas.on('mouse:up', function() {
        isDrawing = false;
        if (rect.width < 5 || rect.height < 5) { canvas.remove(rect); }
    });

    const keydownHandler = function(e) {
        if (e.key === 'Delete' || e.key === 'Backspace') {
            const activeObject = canvas.getActiveObject();
            if (activeObject) { canvas.remove(activeObject); }
        }
    };
    window.addEventListener('keydown', keydownHandler);

    saveBtn.addEventListener('click', async function() {
        const requestId = this.getAttribute('data-request-id');
        const scale = canvas.backgroundImage.scaleX;
        const finalBoxes = canvas.getObjects().map((obj, index) => {
            const x1 = Math.round(obj.left / scale);
            const y1 = Math.round(obj.top / scale);
            const x2 = Math.round((obj.left + obj.width) / scale);
            const y2 = Math.round((obj.top + obj.height) / scale);
            return {
                box_id: obj.customData.box_id || `human_${index}`, label: obj.customData.label,
                confidence: obj.customData.is_human ? 1.0 : obj.customData.confidence,
                box: [x1, y1, x2, y2]
            };
        });
        const payload = { boxes: finalBoxes };

        try {
            const response = await fetch(`/api/clarifications/${requestId}/resolve`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (response.ok) {
                htmx.trigger('#clarification-section', 'loadNextCard');
            } else { alert('Error saving correction.'); }
        } catch (error) {
            console.error('Save failed:', error);
            alert('Error saving correction.');
        }
    });
    
    // Clean up the global listener before the card is removed
    htmx.on(card, 'htmx:beforeSwap', () => {
        window.removeEventListener('keydown', keydownHandler);
    });
}