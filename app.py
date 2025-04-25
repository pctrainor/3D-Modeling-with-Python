import trimesh
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont
import os

# Create a much more detailed basketball
radius = 1.0
# Increase subdivisions for more detail (6 or 7 gives high detail but is more resource intensive)
sphere = trimesh.creation.icosphere(subdivisions=7, radius=radius)

# Add more information about the mesh
print(f"Ultra-high-detail basketball created with radius: {radius}")
print(f"Number of vertices: {len(sphere.vertices)}")
print(f"Number of faces: {len(sphere.faces)}")
print(f"Volume: {sphere.volume:.4f}")
print(f"Surface area: {sphere.area:.4f}")

# Set base color to basketball orange with slight texture variation
orange_color = [255, 140, 0, 255]  # Base orange color (RGBA)
sphere.visual.face_colors = orange_color

# Create more realistic basketball seams
seam_width = 0.02  # Thinner seams for higher detail

# Main seams - horizontal and vertical great circles
for face_idx, face in enumerate(sphere.faces):
    face_center = sphere.vertices[face].mean(axis=0)
    normalized = face_center / np.linalg.norm(face_center)
    
    # More authentic basketball seam pattern
    # Horizontal seams
    if abs(normalized[2]) < seam_width:
        sphere.visual.face_colors[face_idx] = [0, 0, 0, 255]  # Black seams
    
    # Vertical seams (8 segments like a real basketball)
    for i in range(8):
        angle = i * np.pi / 4
        x_test = np.cos(angle)
        y_test = np.sin(angle)
        # Test if face is close to this vertical great circle
        if abs(normalized[0]*y_test - normalized[1]*x_test) < seam_width and abs(normalized[2]) < 0.95:
            sphere.visual.face_colors[face_idx] = [0, 0, 0, 255]

# Add pebble texture to simulate basketball surface
# Small random color variation for the non-seam parts
for face_idx, face in enumerate(sphere.faces):
    if np.array_equal(sphere.visual.face_colors[face_idx], orange_color):
        # Add slight texture variation to orange parts
        random_val = np.random.randint(-15, 15)
        sphere.visual.face_colors[face_idx] = [
            min(255, max(0, orange_color[0] + random_val)),
            min(255, max(0, orange_color[1] + random_val)), 
            min(255, max(0, orange_color[2] + random_val)),
            255
        ]

# Load the Spalding logo with full error checking and debug info
logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Spalding-Logo-1280x800.png")
print(f"Looking for logo at: {logo_path}")
print(f"File exists: {os.path.exists(logo_path)}")

try:
    logo_img = Image.open(logo_path)
    print(f"Successfully loaded logo from {logo_path}")
except Exception as e:
    print(f"Error loading logo: {e}")
    print("Creating fallback logo instead")
    
    # Create a more detailed fallback logo
    logo_size = 1024  # Larger size for more detail
    logo_img = Image.new('RGBA', (logo_size, logo_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(logo_img)
    
    # Try multiple fonts for better chance of success
    font = None
    for font_name in ["Arial Bold.ttf", "Arial.ttf", "Times New Roman.ttf", "Verdana.ttf"]:
        try:
            font = ImageFont.truetype(font_name, 80)
            print(f"Using font: {font_name}")
            break
        except IOError:
            continue
    
    if font is None:
        font = ImageFont.load_default()
        print("Using default font")
    
    # Create a more realistic Spalding logo
    text_color = (180, 30, 30, 255)  # Spalding red
    draw.ellipse((logo_size//4-50, logo_size//3-50, logo_size//4+350, logo_size//3+100), 
                 outline=text_color, width=5)
    draw.text((logo_size//4+30, logo_size//3-10), "SPALDING", fill=text_color, font=font)
    
    # Save the fallback logo for inspection
    fallback_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fallback_logo.png")
    logo_img.save(fallback_path)
    print(f"Saved fallback logo to {fallback_path}")

# Resize logo if needed
target_size = (1024, 1024)  # Larger for more detail
logo_img = logo_img.resize(target_size, Image.LANCZOS)

# Ensure the image has an alpha channel
if logo_img.mode != 'RGBA':
    logo_img = logo_img.convert('RGBA')

# Replace the logo application section with this code

# Apply the logo to a specific region of the basketball
logo_center = np.array([0.0, 0.0, 1.0])  # Top of the ball
logo_radius = 0.25  # Size of logo region

# Convert logo to numpy array for pixel access
logo_array = np.array(logo_img)
logo_height, logo_width = logo_array.shape[:2]

# Find faces in the logo region and apply actual logo pixels
for face_idx, face in enumerate(sphere.faces):
    face_center = sphere.vertices[face].mean(axis=0)
    normalized = face_center / np.linalg.norm(face_center)
    
    # Check if face is in logo region (near the top)
    angle = np.arccos(np.dot(normalized, logo_center))
    if angle < logo_radius:
        # Project the 3D point onto the 2D logo image
        
        # Create tangent vectors on sphere surface
        if abs(normalized[0]) < 0.9:
            tangent1 = np.array([0, normalized[2], -normalized[1]])
        else:
            tangent1 = np.array([normalized[2], 0, -normalized[0]])
        tangent1 = tangent1 / np.linalg.norm(tangent1)
        tangent2 = np.cross(normalized, tangent1)
        
        # Get local coordinates
        rel_pos = normalized - logo_center
        # Project onto tangent plane
        u = np.dot(rel_pos, tangent1) / logo_radius
        v = np.dot(rel_pos, tangent2) / logo_radius
        
        # Map to image coordinates
        img_x = int((u + 1) * logo_width / 2)
        img_y = int((1 - v) * logo_height / 2)  # Flip Y for image coordinates
        
        # Ensure coordinates are in bounds
        img_x = max(0, min(logo_width-1, img_x))
        img_y = max(0, min(logo_height-1, img_y))
        
        # Get pixel color from logo
        try:
            pixel = logo_array[img_y, img_x]
            # Only apply non-transparent pixels
            if len(pixel) == 4 and pixel[3] > 20:  # If alpha > 20
                # Apply logo pixel color
                sphere.visual.face_colors[face_idx] = pixel
            # Otherwise keep the original orange/seam color
        except IndexError:
            # Just in case our coordinates are somehow out of bounds
            pass
        
# Show the enhanced basketball - use smooth shading for better look
sphere.show(smooth=True, flags={'wireframe': False, 'cull': False})

# Save the basketball mesh for examination
output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "basketball.obj")
sphere.export(output_path)
print(f"Saved basketball mesh to {output_path}")