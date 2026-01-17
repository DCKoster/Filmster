"""
Generate printable game cards with QR codes.
Creates PDF with 8 cards per page (2 columns, 4 rows).
Each card has: Movie name + Year (left column) and QR code (right column).
Uses GitHub Pages URLs for QR codes.
"""

import os
import json
import re
import qrcode
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def extract_movie_info(filename):
    """
    Extract movie name and year from filename.
    
    Args:
        filename: Poster filename (e.g., "The_Matrix_1999.jpg")
        
    Returns:
        Tuple of (name, year) or (filename, "Unknown") if parsing fails
    """
    # Remove extension
    name = os.path.splitext(filename)[0]
    
    # Try to extract year (4 digits at the end)
    match = re.search(r'_(\d{4})$', name)
    if match:
        year = match.group(1)
        # Remove year from name and replace underscores with spaces
        name = name[:match.start()].replace('_', ' ')
        return name, year
    
    # Fallback: return filename without extension
    return name.replace('_', ' '), "Unknown"


def generate_qr_code(url, size=300):
    """
    Generate QR code image from URL.
    
    Args:
        url: URL to encode
        size: Size of QR code in pixels
        
    Returns:
        PIL Image of QR code
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img = img.resize((size, size), Image.Resampling.LANCZOS)
    
    return img


def create_card_image(movie_name, year, qr_image, card_width=90*mm, card_height=63*mm):
    """
    Create a single card image with text and QR code.
    
    Layout: [Movie Name + Year | QR Code]
    
    Args:
        movie_name: Name of the movie
        year: Release year
        qr_image: PIL Image of QR code
        card_width: Width of card in points
        card_height: Height of card in points
        
    Returns:
        PIL Image of the card
    """
    # Convert dimensions to pixels (assuming 300 DPI)
    dpi = 300
    width_px = int(card_width * dpi / 72)
    height_px = int(card_height * dpi / 72)
    
    # Create card image
    card = Image.new('RGB', (width_px, height_px), 'white')
    draw = ImageDraw.Draw(card)
    
    # Draw border
    border_width = 4
    draw.rectangle(
        [(border_width, border_width), (width_px - border_width, height_px - border_width)],
        outline='black',
        width=border_width
    )
    
    # Calculate column widths (60% for text, 40% for QR)
    text_col_width = int(width_px * 0.6)
    qr_col_width = width_px - text_col_width
    
    # Add movie name and year (left column)
    try:
        # Try to use a nice font
        font_large = ImageFont.truetype("arial.ttf", 60)
        font_small = ImageFont.truetype("arial.ttf", 40)
    except:
        # Fallback to default font
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Split movie name into multiple lines if too long
    words = movie_name.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font_large)
        text_width = bbox[2] - bbox[0]
        
        if text_width < text_col_width - 40:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    # Limit to 3 lines
    lines = lines[:3]
    
    # Calculate vertical positioning
    total_text_height = len(lines) * 70 + 50  # Approximate
    start_y = (height_px - total_text_height) // 2
    
    # Draw movie name lines
    y = start_y
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font_large)
        text_width = bbox[2] - bbox[0]
        x = (text_col_width - text_width) // 2
        draw.text((x, y), line, fill='black', font=font_large)
        y += 70
    
    # Draw year
    y += 20
    bbox = draw.textbbox((0, 0), f"({year})", font=font_small)
    text_width = bbox[2] - bbox[0]
    x = (text_col_width - text_width) // 2
    draw.text((x, y), f"({year})", fill='gray', font=font_small)
    
    # Add QR code (right column)
    qr_size = int(min(qr_col_width * 0.9, height_px * 0.8))
    qr_resized = qr_image.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
    
    qr_x = text_col_width + (qr_col_width - qr_size) // 2
    qr_y = (height_px - qr_size) // 2
    card.paste(qr_resized, (qr_x, qr_y))
    
    return card


def generate_cards_pdf(poster_dir='game/posters',
                       output_pdf='src/card_generation/printable_cards.pdf'):
    """
    Generate PDF with printable game cards.
    8 cards per A4 page (2 columns, 4 rows).
    Uses GitHub Pages URLs for QR codes.
    
    Args:
        poster_dir: Directory containing poster images
        output_pdf: Output PDF file path
    """
    print("\n" + "=" * 60)
    print("GENERATING PRINTABLE CARDS")
    print("=" * 60 + "\n")
    
    # Get GitHub username from environment
    github_username = os.getenv('GITHUB_USERNAME')
    if not github_username:
        print("✗ GITHUB_USERNAME not found in .env file")
        print("  Please add: GITHUB_USERNAME=your_github_username")
        return False
    
    print(f"GitHub Username: {github_username}")
    print(f"Base URL: https://{github_username}.github.io/Filmster/game/posters/\n")
    
    # Check if poster directory exists
    if not os.path.exists(poster_dir):
        print(f"✗ Poster directory not found: {poster_dir}")
        return False
    
    # Get all poster files
    poster_files = [f for f in os.listdir(poster_dir) if f.endswith('.jpg') or f.endswith('.png')]
    
    if not poster_files:
        print(f"✗ No posters found in {poster_dir}")
        return False
    
    print(f"✓ Found {len(poster_files)} posters\n")
    
    # A4 dimensions
    page_width, page_height = A4
    
    # Card dimensions (8 per page: 2 cols x 4 rows)
    cards_per_row = 2
    cards_per_col = 4
    margin = 10 * mm
    
    card_width = (page_width - 2 * margin) / cards_per_row
    card_height = (page_height - 2 * margin) / cards_per_col
    
    # Create PDF
    c = canvas.Canvas(output_pdf, pagesize=A4)
    
    # Create temporary directory for card images
    temp_dir = 'src/card_generation/temp_cards'
    os.makedirs(temp_dir, exist_ok=True)
    
    # Generate cards
    card_count = 0
    page_count = 0
    
    for filename in poster_files:
        # Extract movie info
        movie_name, year = extract_movie_info(filename)
        
        # Generate GitHub Pages URL
        url = f"https://{github_username}.github.io/Filmster/game/posters/{filename}"
        
        print(f"[{card_count + 1}/{len(poster_files)}] Creating card: {movie_name} ({year})")
        
        # Generate QR code
        qr_img = generate_qr_code(url)
        
        # Create card image
        card_img = create_card_image(movie_name, year, qr_img, card_width, card_height)
        
        # Save temporary card image
        temp_card_path = os.path.join(temp_dir, f"card_{card_count}.png")
        card_img.save(temp_card_path, 'PNG', dpi=(300, 300))
        
        # Calculate position on page
        row = (card_count % 8) // cards_per_row
        col = (card_count % 8) % cards_per_row
        
        x = margin + col * card_width
        y = page_height - margin - (row + 1) * card_height
        
        # Add card to PDF
        c.drawImage(temp_card_path, x, y, width=card_width, height=card_height)
        
        # Draw cut marks (light gray lines)
        c.setStrokeColorRGB(0.7, 0.7, 0.7)
        c.setLineWidth(0.5)
        
        # Horizontal cut marks
        if col == 0:
            c.line(0, y, margin / 2, y)
            c.line(page_width - margin / 2, y, page_width, y)
        
        # Vertical cut marks
        if row == 0:
            c.line(x, page_height, x, page_height - margin / 2)
            c.line(x, margin / 2, x, 0)
        
        card_count += 1
        
        # New page after 8 cards
        if card_count % 8 == 0:
            c.showPage()
            page_count += 1
            print(f"  → Page {page_count} complete\n")
    
    # Save final page if not complete
    if card_count % 8 != 0:
        c.showPage()
        page_count += 1
    
    c.save()
    
    # Clean up temporary files
    import shutil
    shutil.rmtree(temp_dir)
    
    # Summary
    print("\n" + "=" * 60)
    print("CARD GENERATION SUMMARY")
    print("=" * 60)
    print(f"Total cards created: {card_count}")
    print(f"Total pages: {page_count}")
    print(f"Cards per page: 8 (2 columns × 4 rows)")
    print(f"Card size: {int(card_width/mm)}mm × {int(card_height/mm)}mm")
    print(f"\nPDF saved to: {output_pdf}")
    print("=" * 60 + "\n")
    
    return True


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate printable game cards with QR codes')
    parser.add_argument('--poster-dir', default='game/posters',
                       help='Directory containing posters (default: game/posters)')
    parser.add_argument('--output', default='src/card_generation/printable_cards.pdf',
                       help='Output PDF file (default: src/card_generation/printable_cards.pdf)')
    
    args = parser.parse_args()
    
    success = generate_cards_pdf(args.poster_dir, args.output)
    
    if not success:
        exit(1)


if __name__ == "__main__":
    main()
