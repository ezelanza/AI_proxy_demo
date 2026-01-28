#!/usr/bin/env python3
"""Make labels optimized for 50mm paper (t50*3080)"""

import sys
from PIL import Image, ImageDraw, ImageFont

if len(sys.argv) < 2:
    print("Usage: python make_label.py 'YOUR TEXT'")
    print("\nExamples:")
    print("  python make_label.py 'HELLO WORLD'")
    print("  python make_label.py 'Meeting Room A'")
    print("\nPaper: 50mm width (384px for B1 printer)")
    sys.exit(1)

text = ' '.join(sys.argv[1:])

# Optimal for 50mm paper: 384px width (48mm print area)
WIDTH = 384
HEIGHT = 80  # Adjust based on text length

# Create image
img = Image.new('RGB', (WIDTH, HEIGHT), 'white')
draw = ImageDraw.Draw(img)

# Try to get a nice font
try:
    font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 40)
except:
    try:
        font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 40)
    except:
        font = ImageFont.load_default()

# Center text
bbox = draw.textbbox((0, 0), text, font=font)
text_width = bbox[2] - bbox[0]
text_height = bbox[3] - bbox[1]
x = (WIDTH - text_width) // 2
y = (HEIGHT - text_height) // 2

draw.text((x, y), text, fill='black', font=font)
img = img.convert('1')

# Save with simple filename
filename = f"images/{text.replace(' ', '_').lower()}.png"
img.save(filename)

print(f"✓ Created: {filename}")
print(f"  Text: {text}")
print(f"  Size: {WIDTH}x{HEIGHT}px (optimized for 50mm paper)")
print(f"\nNow print it with the agent:")
print(f"  python niimprint_agent.py")
print(f"  You: Print {filename}")
