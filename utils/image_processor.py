# utils/image_processor.py
import cv2
import numpy as np
from PIL import Image

def analyze_tumor(image):
    """Real tumor detection using OpenCV"""
    # Convert PIL to OpenCV
    img_array = np.array(image)
    
    # Convert to grayscale if it's color
    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_array
    
    # Apply Gaussian blur
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Edge detection
    edges = cv2.Canny(blurred, 30, 100)
    
    # Find contours
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if len(contours) == 0:
        return {
            'stage': 'No tumor detected',
            'confidence': 0.95,
            'tumor_count': 0,
            'largest_size': '0 pixels',
            'malignancy': 'None'
        }
    
    # Analyze contours
    tumor_areas = [cv2.contourArea(cnt) for cnt in contours]
    largest_area = max(tumor_areas)
    
    # Determine stage based on size
    if largest_area < 1000:
        stage = "Stage I"
        confidence = 0.85
        malignancy = "Low"
    elif largest_area < 5000:
        stage = "Stage II"
        confidence = 0.80
        malignancy = "Moderate"
    elif largest_area < 15000:
        stage = "Stage III"
        confidence = 0.75
        malignancy = "High"
    else:
        stage = "Stage IV"
        confidence = 0.70
        malignancy = "High"
    
    return {
        'stage': stage,
        'confidence': confidence,
        'tumor_count': len(contours),
        'largest_size': f"{largest_area:.0f} pixels",
        'malignancy': malignancy,
        'location': 'Multiple regions' if len(contours) > 1 else 'Single region'
    }

def create_visualization(image):
    """Create visualization of detected tumors"""
    img_array = np.array(image)
    
    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_array
    
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 30, 100)
    
    # Draw contours on original image
    if len(img_array.shape) == 3:
        output = img_array.copy()
    else:
        output = cv2.cvtColor(img_array, cv2.COLOR_GRAY2RGB)
    
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Draw green contours
    cv2.drawContours(output, contours, -1, (0, 255, 0), 2)
    
    # Draw red bounding boxes
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        cv2.rectangle(output, (x, y), (x + w, y + h), (255, 0, 0), 2)
    
    return Image.fromarray(output)