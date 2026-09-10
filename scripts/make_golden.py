from pathlib import Path
import csv

rows = {
    "billing_refund": [
        "I was charged twice for my order", "Can you refund my payment", "Why is there a billing charge", "I need my money back", "The invoice is wrong",
    ],
    "delivery_tracking": [
        "Where is my package", "Can I get tracking for my shipment", "My delivery is late", "The order has not arrived", "It says delivered but I do not have it",
    ],
    "technical_problem": [
        "The app is not working", "I get an error when I open the app", "The website keeps crashing", "This feature is broken", "I cannot complete the request",
    ],
    "account_access": [
        "I forgot my password", "My account is locked", "I cannot sign in", "How do I verify my account", "I lost access to my account",
    ],
    "product_information": [
        "How much does this cost", "Is this product available", "What features are included", "Do you offer this service", "What are your hours",
    ],
    "cancellation": [
        "Please cancel my order", "I want to unsubscribe", "How do I close my account", "Stop this service", "Can I cancel this request",
    ],
    "complaint": [
        "This is unacceptable", "I am very frustrated", "Your service is terrible", "I want to make a complaint", "I am disappointed with this",
    ],
    "other": [
        "Hello, I have a question", "Can someone help me", "I need support", "Thanks for your help", "Please contact me",
    ],
}

out = Path("data/golden.csv")
with out.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=["id", "text", "intent", "expected_action"])
    writer.writeheader()
    index = 0
    for intent, templates in rows.items():
        for round_number in range(4):
            for template in templates:
                index += 1
                text = template
                if round_number:
                    text += [" please", " today", " - can you help", "?", " now"][round_number]
                action = "escalate" if intent in {"complaint", "other"} else "auto-handle"
                writer.writerow({"id": f"golden-{index:03d}", "text": text, "intent": intent, "expected_action": action})
print(f"wrote {index} rows to {out}")
