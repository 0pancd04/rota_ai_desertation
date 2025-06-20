Based on your project structure and the `RotaRequest` schema, here are sample request bodies for the `/assign-employee` API:

## **Basic Assignment Request:**
```json
{
  "prompt": "Patient P001 needs exercise support today. Can you assign an available employee?"
}
```

## **Service-Specific Request:**
```json
{
  "prompt": "Patient P003 requires medication administration at 10:00 AM. Please assign a qualified nurse."
}
```

## **Language-Specific Request:**
```json
{
  "prompt": "Patient P002 prefers Spanish-speaking care worker for personal care assistance this afternoon."
}
```

## **Time-Constrained Request:**
```json
{
  "prompt": "Patient P004 needs companionship service between 2:00 PM and 4:00 PM today. Assign available care worker."
}
```

## **Complex Request with Context:**
```json
{
  "prompt": "Patient P005 with diabetes needs medication support and has mobility issues. Assign experienced nurse with vehicle access.",
  "context": {
    "priority": "high",
    "medical_condition": "diabetes",
    "special_requirements": ["vehicle_needed", "experienced_staff"]
  }
}
```

## **Emergency Assignment:**
```json
{
  "prompt": "URGENT: Patient P001 needs immediate medical attention. Assign nearest available nurse with car."
}
```

These requests test various scenarios including:
- **Service types** (exercise, medication, companionship, personal care)
- **Staff qualifications** (nurse vs care worker)
- **Language preferences**
- **Time constraints**
- **Special requirements** (vehicle access, experience level)
- **Priority levels** (urgent vs routine)