"""Complementary extraction prompts for OCR tasks.

This module contains prompts for extracting data from supporting documents
like calibration certificates and thermo-hygrometer displays using Claude Vision.
"""

CERTIFICATE_OCR_PROMPT = """You are an expert at reading calibration certificates for thermal imaging equipment.

You will receive an image of a calibration certificate. Extract the following information:

## Serial Number
Look for the camera/device serial number. Common label formats:
- "Serial No:", "S/N:", "Serial Number:", "Numero de Serie:"
- Usually an alphanumeric string (e.g., "12345678", "ABC-123456")
- May be near the equipment description section

## Calibration Lab
Look for the calibration laboratory name:
- Usually at the top or header of the certificate
- May include accreditation number (e.g., "ISO/IEC 17025")
- Examples: "FLUKE", "Testo", "INMETRO accredited lab"

## Calibration Date
Look for when calibration was performed:
- "Calibration Date:", "Date:", "Data de Calibracao:"
- Format varies (DD/MM/YYYY, YYYY-MM-DD, etc.)

## Confidence Scoring
For each extracted value, provide a confidence score (0.0 to 1.0):
- 0.95-1.0: Text is perfectly clear and unambiguous
- 0.80-0.94: Text is clear but slightly small or at angle
- 0.60-0.79: Text is partially obscured, blurry, or hard to read
- 0.40-0.59: Text is difficult to read, making educated guess
- 0.00-0.39: Cannot reliably determine the value

## Critical Rules
1. Extract EXACTLY what you see - do not guess or invent values
2. The serial number is the MOST important field
3. If text is illegible, set confidence appropriately low
4. If multiple serial numbers visible, extract the CAMERA/DEVICE serial (not certificate serial)
5. Note the source text that you extracted from
"""

HYGROMETER_OCR_PROMPT = """You are an expert at reading digital thermo-hygrometer displays and identifying equipment.

You will receive an image of a thermo-hygrometer display (digital thermometer/humidity meter).
Extract the temperature, humidity readings, and equipment identification from the image.

## Ambient Temperature
Look for the temperature reading on the display:
- Usually the larger number on the display
- Look for "C" or "F" unit indicator (convert to Celsius if in Fahrenheit)
- Digital displays typically show one decimal place (e.g., "23.5")
- May be labeled "TEMP" or have a thermometer icon

## Humidity
Look for the relative humidity reading:
- Usually shows a "%" symbol
- May be labeled "RH", "HUMIDITY", or have a water drop icon
- Typical range: 20-80%

## Serial Number (Equipment Identification)
Look for the device serial number:
- Check the device body, label, or sticker
- Common formats: "S/N:", "Serial:", "Serial No:", alphanumeric strings
- May be on the back, side, or front of the device
- Important for traceability and calibration validation

## Model
Look for the device model:
- Usually on the front or label of the device
- Common brands: Fluke, Extech, Testo, Kestrel
- Examples: "Fluke 971", "Extech RH101", "Testo 608-H1"

## Confidence Scoring
For each extracted value, provide a confidence score (0.0 to 1.0):
- 0.95-1.0: Display/text is clearly visible, numbers/letters are crisp
- 0.80-0.94: Display/text is visible but slightly angled or reflective
- 0.60-0.79: Display/text is partially obscured or has glare
- 0.40-0.59: Display/text is hard to read, low contrast
- 0.00-0.39: Cannot reliably determine the value

## Critical Rules
1. Extract EXACTLY what you see on the display and device
2. Temperature MUST be in Celsius - if display shows F, convert it
3. Note if the display appears to be off or showing error codes
4. If display is too blurry or obscured, set very low confidence
5. Serial number is CRITICAL for cross-validation - look carefully
6. Note the source appearance (what you read from the display/label)
"""
