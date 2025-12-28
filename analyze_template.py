"""Analyze template to find head region"""
import cv2
import numpy as np
from pathlib import Path

# Load template
template_path = Path("template_check.png")
img = cv2.imread(str(template_path))

if img is None:
    print("Failed to load template")
    exit(1)

h, w = img.shape[:2]
print(f"Template size: {w}x{h}")

# Convert to HSV for better color detection
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# The head appears to be a beige/skin-colored sphere
# Let's find the bright area in the upper portion
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# The head is the brightest area in upper 30% of image
upper_portion = gray[0:int(h*0.3), :]

# Find the brightest region
_, thresh = cv2.threshold(upper_portion, 180, 255, cv2.THRESH_BINARY)

# Find contours
contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

if contours:
    # Get largest contour (should be the head)
    largest = max(contours, key=cv2.contourArea)
    x, y, w_head, h_head = cv2.boundingRect(largest)

    print(f"\nHead region found:")
    print(f"  x={x}, y={y}")
    print(f"  width={w_head}, height={h_head}")
    print(f"  as percentage: x={x/w*100:.1f}%, y={y/h*100:.1f}%")
    print(f"  size: {w_head/w*100:.1f}% x {h_head/h*100:.1f}%")

    # Draw rectangle on image
    result = img.copy()
    cv2.rectangle(result, (x, y), (x+w_head, y+h_head), (0, 255, 0), 3)

    # Add text
    cv2.putText(result, f"HEAD: {w_head}x{h_head}", (x, y-10),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # Save result
    output_path = Path("template_analysis.jpg")
    cv2.imwrite(str(output_path), result)
    print(f"\nAnalysis saved to: {output_path}")
    print("\nSuggested code for template_generator.py:")
    print(f"    head_width = int(w * {w_head/w:.3f})")
    print(f"    head_height = int(h * {h_head/h:.3f})")
    print(f"    x = int(w * {x/w:.3f})")
    print(f"    y = int(h * {y/h:.3f})")
else:
    print("No head region found!")
