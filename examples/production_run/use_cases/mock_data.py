# FILE: examples/production_run/use_cases/mock_data.py

# This file contains the predefined "AI predictions" for our simulator.
# The data structures here conform to the schemas defined in app/schemas.py.

# ==============================================================================
# 1. INVOICE PROCESSING MOCK DATA
# ==============================================================================

mock_invoice_results = [
    # --- RESULT 1: High confidence, everything is correct ---
    {
        "supplier_name": {"value": "Office Supplies Co.", "confidence": 0.99},
        "invoice_date": {"value": "2025-10-20", "confidence": 0.99},
        "invoice_number": {"value": "INV-1024", "confidence": 0.99},
        "line_items": [
            {
                "item_description": {"value": "Standard Ballpoint Pens, Black (12-pack)", "confidence": 0.98},
                "quantity": {"value": 5.0, "confidence": 0.99},
                "unit_price": {"value": 8.99, "confidence": 0.99},
                "total_cost": {"value": 44.95, "confidence": 0.99},
            },
            {
                "item_description": {"value": "A4 Printer Paper (500 sheets)", "confidence": 0.99},
                "quantity": {"value": 2.0, "confidence": 0.99},
                "unit_price": {"value": 25.50, "confidence": 0.99},
                "total_cost": {"value": 51.00, "confidence": 0.99},
            },
        ],
    },
    # --- RESULT 2: Contains multiple low-confidence errors to be corrected ---
    {
        "supplier_name": {"value": "Hardwar & Son", "confidence": 0.82}, # <-- TYPO
        "invoice_date": {"value": "2025-10-22", "confidence": 0.99},
        "invoice_number": {"value": "8845-B", "confidence": 0.99},
        "line_items": [
            {
                "item_description": {"value": "Galvanized Steel Nails, 2-inch", "confidence": 0.99},
                "quantity": {"value": 1.0, "confidence": 0.75}, # <-- WRONG QUANTITY
                "unit_price": {"value": 15.00, "confidence": 0.99},
                "total_cost": {"value": 15.00, "confidence": 0.99},
            },
            {
                "item_description": {"value": "Wood Glue, 1 Gallon", "confidence": 0.99},
                "quantity": {"value": 1.0, "confidence": 0.99},
                "unit_price": {"value": 35.50, "confidence": 0.99},
                "total_cost": {"value": 35.50, "confidence": 0.99},
            },
        ],
    },
    # --- RESULT 3: Another high-confidence, correct result ---
    {
        "supplier_name": {"value": "Fresh Produce Distributors", "confidence": 0.98},
        "invoice_date": {"value": "2025-10-21", "confidence": 0.99},
        "invoice_number": {"value": "FP-98452", "confidence": 0.99},
        "line_items": [
            {
                "item_description": {"value": "Organic Bananas (Case)", "confidence": 0.99},
                "quantity": {"value": 10.0, "confidence": 0.99},
                "unit_price": {"value": 22.00, "confidence": 0.99},
                "total_cost": {"value": 220.00, "confidence": 0.99},
            },
        ],
    }
]


# ==============================================================================
# 2. UTILITY POLE DETECTION MOCK DATA
# ==============================================================================

mock_pole_detection_results = [
    # --- RESULT 1: High confidence, everything is correct ---
    {
        "boxes": [
            {"box_id": "a1", "label": "utility_pole", "confidence": 0.98, "box": [150, 200, 200, 450]},
            {"box_id": "b2", "label": "utility_pole", "confidence": 0.97, "box": [550, 220, 590, 460]},
        ]
    },
    # --- RESULT 2: Contains a misidentified tree with low confidence ---
    {
        "boxes": [
            {"box_id": "c3", "label": "utility_pole", "confidence": 0.99, "box": [400, 150, 450, 480]},
            {"box_id": "d4", "label": "utility_pole", "confidence": 0.65, "box": [610, 300, 650, 380]}, # <-- THIS IS ACTUALLY A TREE
        ]
    },
    # --- RESULT 3: Missed one pole, and misidentified a sign with low confidence ---
    {
        "boxes": [
            {"box_id": "e5", "label": "utility_pole", "confidence": 0.96, "box": [220, 180, 280, 400]},
            # This result is missing a second, real pole. The user will have to add it.
            {"box_id": "f6", "label": "utility_pole", "confidence": 0.71, "box": [700, 400, 730, 450]}, # <-- THIS IS A STREET SIGN
        ]
    }
]


# --- Self-Verification (Optional but good practice) ---
# This block allows us to run this file directly to validate the data structures.
if __name__ == "__main__":
    from app.schemas import InvoiceSchema, PoleDetectionSchema

    print("--- Verifying Mock Invoice Data ---")
    for i, data in enumerate(mock_invoice_results):
        try:
            InvoiceSchema.model_validate(data)
            print(f"Result {i+1}: OK")
        except Exception as e:
            print(f"Result {i+1}: FAILED VALIDATION\n{e}")

    print("\n--- Verifying Mock Pole Detection Data ---")
    for i, data in enumerate(mock_pole_detection_results):
        try:
            PoleDetectionSchema.model_validate(data)
            print(f"Result {i+1}: OK")
        except Exception as e:
            print(f"Result {i+1}: FAILED VALIDATION\n{e}")
