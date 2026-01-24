"""
Generate printable game cards with QR codes.
Left column: QR code | Right column: Year (big) + Movie name (below)
Uses GitHub Pages URLs for QR codes.
"""

import os
import re
import qrcode
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PyPDF2 import PdfReader, PdfWriter
from dotenv import load_dotenv
import io

# Load environment variables
load_dotenv()

# Register Eras fonts (Medium and Bold)
try:
    # Try to register the fonts from Windows font directory
    pdfmetrics.registerFont(TTFont('Eras Medium ITC', 'ERASMD.TTF'))
    pdfmetrics.registerFont(TTFont('Eras Bold ITC', 'ERASBD.TTF'))
    FONT_NAME = 'Eras Medium ITC'
    FONT_NAME_BOLD = 'Eras Bold ITC'
except Exception as e:
    print(f"Warning: Could not load Eras fonts, falling back to Helvetica. Error: {e}")
    # If font not found, we'll use Helvetica as fallback
    FONT_NAME = 'Helvetica'
    FONT_NAME_BOLD = 'Helvetica-Bold'

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
    
    # Create QR code with transparent background
    img = qr.make_image(fill_color="black", back_color="transparent")
    
    # Convert to RGBA to ensure transparency is preserved
    img = img.convert("RGBA")
    img = img.resize((size, size), Image.Resampling.LANCZOS)
    
    return img


def create_card_image(movie_name, year, qr_image, card_width=90*mm, card_height=63*mm):
    """
    Create a single card image with text and QR code.
    
    Layout: [Year (big) + Movie Name (below) | QR Code]
    
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
    
    # Add year and movie name (left column)
    try:
        # Try to use a nice font - Year is BIG, Name is smaller
        font_year = ImageFont.truetype("arial.ttf", 100)  # Big year
        font_name = ImageFont.truetype("arial.ttf", 35)   # Smaller name
    except:
        # Fallback to default font
        font_year = ImageFont.load_default()
        font_name = ImageFont.load_default()
    
    # Split movie name into multiple lines if too long
    words = movie_name.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font_name)
        text_width = bbox[2] - bbox[0]
        
        if text_width < text_col_width - 40:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    # Limit to 4 lines
    lines = lines[:4]
    
    # Calculate vertical positioning - Year at top, name below
    year_bbox = draw.textbbox((0, 0), year, font=font_year)
    year_height = year_bbox[3] - year_bbox[1]
    
    name_total_height = len(lines) * 45
    total_height = year_height + 30 + name_total_height  # 30px gap between year and name
    
    start_y = (height_px - total_height) // 2
    
    # Draw year (BIG)
    year_width = year_bbox[2] - year_bbox[0]
    x = (text_col_width - year_width) // 2
    draw.text((x, start_y), year, fill='black', font=font_year)
    
    # Draw movie name lines (below year)
    y = start_y + year_height + 30
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font_name)
        text_width = bbox[2] - bbox[0]
        x = (text_col_width - text_width) // 2
        draw.text((x, y), line, fill='black', font=font_name)
        y += 45
    
    # Add QR code (right column)
    qr_size = int(min(qr_col_width * 0.9, height_px * 0.8))
    qr_resized = qr_image.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
    
    qr_x = text_col_width + (qr_col_width - qr_size) // 2
    qr_y = (height_px - qr_size) // 2
    card.paste(qr_resized, (qr_x, qr_y))
    
    return card


def generate_cards_pdf(poster_dir='game/posters',
                       output_pdf='src/card_generation/printable_cards.pdf',
                       template_pdf='src/card_generation/template.pdf',
                       debug=False,
                       test_positioning=False,
                       filter_list=None):
    """
    Generate PDF with printable game cards using template.
    Uses template.pdf with 8 pre-styled boxes (2 columns, 4 rows).
    Left column: QR code | Right column: Year + Movie name
    
    Args:
        poster_dir: Directory containing poster images
        output_pdf: Output PDF file path
        template_pdf: Path to template PDF with styled boxes
        debug: If True, only process the first poster
        test_positioning: If True, only process 4 posters (one per row) to test positioning
        filter_list: Path to a text file with movie list to filter (e.g., list/add_posters.txt)
    """
    print("\n" + "=" * 60)
    print("GENERATING PRINTABLE CARDS WITH TEMPLATE")
    print("=" * 60 + "\n")
    
    # Check if template exists
    if not os.path.exists(template_pdf):
        print(f"Template PDF not found: {template_pdf}")
        return False
    
    # Get GitHub username from environment
    github_username = os.getenv('GITHUB_USERNAME')
    if not github_username:
        print("GITHUB_USERNAME not found in .env file")
        print("  Please add: GITHUB_USERNAME=your_github_username")
        return False
    
    # Check if poster directory exists
    if not os.path.exists(poster_dir):
        print(f"Poster directory not found: {poster_dir}")
        return False
    
    # Get all poster files
    poster_files = [f for f in os.listdir(poster_dir) if f.endswith('.jpg') or f.endswith('.png')]
    
    if not poster_files:
        print(f"No posters found in {poster_dir}")
        return False
    
    # Filter by list if specified
    if filter_list:
        print(f"Filtering posters based on: {filter_list}")
        
        # Read movie names from filter list
        filter_movies = set()
        try:
            with open(filter_list, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines, comments, and separators
                    if not line or line.startswith('#') or line.startswith('='):
                        continue
                    
                    # Parse "Movie Name (Year)" format
                    if '(' in line and line.endswith(')'):
                        name = line[:line.rfind('(')].strip()
                        year = line[line.rfind('(')+1:-1].strip()
                        
                        if name and year:
                            # Convert to filename format
                            safe_name = re.sub(r'[^\w\s-]', '', name)
                            safe_name = re.sub(r'[-\s]+', '_', safe_name)
                            safe_name = safe_name.strip('_')
                            filename = f"{safe_name}_{year}.jpg"
                            filter_movies.add(filename)
            
            if not filter_movies:
                print(f"No valid movies found in {filter_list}")
                return False
            
            # Filter poster files
            original_count = len(poster_files)
            poster_files = [f for f in poster_files if f in filter_movies]
            
            print(f"Filtered {original_count} posters to {len(poster_files)} matching the list\n")
            
            if not poster_files:
                print(f"None of the posters in {poster_dir} match the filter list")
                return False
                
        except IOError as e:
            print(f"Error reading filter list: {e}")
            return False
    
    # Sort files for consistent ordering
    poster_files.sort()
    
    # Test positioning mode: only process 4 posters (one per row)
    if test_positioning:
        poster_files = poster_files[:4]
        print(f"TEST POSITIONING MODE: Processing 4 posters (one per row)\n")
    # Debug mode: only process first poster
    elif debug:
        poster_files = poster_files[:1]
        print(f"DEBUG MODE: Processing only first poster\n")
    
    print(f"✓ Found {len(poster_files)} poster(s) to process\n")
    
    # A4 dimensions
    page_width, page_height = A4
    
    # Template-based positioning
    # Format: (x, y, width, height) in points from bottom-left
    # Row positions from top to bottom (PDF coordinates go from bottom)
    
    # Define box positions for each row (4 rows per page)
    # Each row has: [QR box (left), Text box (right)]
    row_positions = [
        # Row 1
        {
            'qr': {'x': 21*mm, 'y': page_height - 80 *mm, 'width': 70*mm, 'height': 70*mm},
            'text': {'x': 117*mm, 'y': page_height - 80*mm, 'width': 80*mm, 'height': 70*mm}
        },
        # Row 2
        {
            'qr': {'x': 21*mm, 'y': page_height - 151*mm, 'width': 70*mm, 'height': 70*mm},
            'text': {'x': 117*mm, 'y': page_height - 151*mm, 'width': 80*mm, 'height': 70*mm}
        },
        # Row 3
        {
            'qr': {'x': 21*mm, 'y': page_height - 220*mm, 'width': 70*mm, 'height': 70*mm},
            'text': {'x': 117*mm, 'y': page_height - 221*mm, 'width': 80*mm, 'height': 70*mm}
        },
        # Row 4
        {
            'qr': {'x': 21*mm, 'y': page_height - 289*mm, 'width': 70*mm, 'height': 70*mm},
            'text': {'x': 117*mm, 'y': page_height - 291*mm, 'width': 80*mm, 'height': 70*mm}
        }
    ]
    
    # Load template PDF
    template_reader = PdfReader(template_pdf)
    pdf_writer = PdfWriter()
    
    # Create temporary directory for QR codes
    temp_dir = 'src/card_generation/temp_qr'
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
        
        # Calculate which page and row
        page_idx = card_count // 4  
        row_idx = card_count % 4     
        
        # Start new page if needed
        if row_idx == 0:
            # Get a fresh copy of template page
            # Use modulo to cycle through template pages if we have more cards than template pages
            template_idx = page_idx % len(template_reader.pages)
            
            # Re-read the template to get a fresh copy 
            template_reader_fresh = PdfReader(template_pdf)
            template_page = template_reader_fresh.pages[template_idx]
            
            # Create overlay canvas
            packet = io.BytesIO()
            c = canvas.Canvas(packet, pagesize=A4)
        
        # Get position for this row
        pos = row_positions[row_idx]
        
        # Generate and save QR code
        qr_img = generate_qr_code(url, size=400)
        temp_qr_path = os.path.join(temp_dir, f"qr_{card_count}.png")
        qr_img.save(temp_qr_path, 'PNG')
        
        # Draw QR code in left box
        qr_box = pos['qr']
        qr_display_size = qr_box['width'] * 0.5
        qr_offset_x = (qr_box['width'] - qr_display_size) / 2
        qr_offset_y = (qr_box['height'] - qr_display_size) / 2
        c.drawImage(temp_qr_path, 
                   qr_box['x'] + qr_offset_x, 
                   qr_box['y'] + qr_offset_y, 
                   width=qr_display_size, 
                   height=qr_display_size, 
                   preserveAspectRatio=True, mask='auto')
        
        # Draw text (Year + Name) in right box
        text_box = pos['text']
        
        # Draw year (large and bold) - using registered bold font
        c.setFont(FONT_NAME_BOLD, 48)
        c.setFillColorRGB(0, 0, 0)
        year_width = c.stringWidth(year, FONT_NAME_BOLD, 48)
        year_x = text_box['x'] + (text_box['width'] - year_width) / 2
        year_y = text_box['y'] + text_box['height'] - 30*mm
        c.drawString(year_x, year_y, year)
        
        # Draw movie name (adaptive font size based on text length)
        # Start with default font size
        font_size = 12
        line_spacing = 5*mm
        max_width = text_box['width'] - 10*mm
        max_chars_per_line = 28
        
        # Calculate available height for title (from below year to bottom of box)
        available_height = year_y - 8*mm - text_box['y']
        max_lines = 4
        
        # Function to split text into lines based on character count
        def split_into_lines(text, max_chars):
            words = text.split()
            lines = []
            current_line = []
            current_length = 0
            
            for word in words:
                # Calculate length if we add this word (including space)
                word_length = len(word)
                space_length = 1 if current_line else 0
                test_length = current_length + space_length + word_length
                
                if test_length <= max_chars:
                    current_line.append(word)
                    current_length = test_length
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                    current_line = [word]
                    current_length = word_length
            
            if current_line:
                lines.append(' '.join(current_line))
            
            return lines[:max_lines] 
        
        # Try to fit text, reducing font size if necessary
        lines = []
        while font_size >= 7:  # Minimum font size
            lines = split_into_lines(movie_name, max_chars_per_line)
            
            # Calculate total height needed
            total_text_height = len(lines) * line_spacing
            
            # Check if it fits within available height
            if total_text_height <= available_height:
                break
            
            # Reduce font size and try again
            font_size -= 1
        
        # Draw name lines centered
        c.setFont(FONT_NAME, font_size)
        name_y = year_y - 8*mm
        for line in lines:
            line_width = c.stringWidth(line, FONT_NAME, font_size)
            line_x = text_box['x'] + (text_box['width'] - line_width) / 2
            c.drawString(line_x, name_y, line)
            name_y -= line_spacing
        
        card_count += 1
        
        # Complete page
        if row_idx == 3 or card_count == len(poster_files):
            # Finish the overlay canvas
            c.save()
            packet.seek(0)
            
            # Merge overlay with template
            overlay_pdf = PdfReader(packet)
            template_page.merge_page(overlay_pdf.pages[0])
            pdf_writer.add_page(template_page)
            
            page_count += 1
    
    # Write final PDF
    with open(output_pdf, 'wb') as output_file:
        pdf_writer.write(output_file)
    
    # Clean up temporary files
    import shutil
    shutil.rmtree(temp_dir)
    
    # Summary
    print("\n" + "=" * 60)
    print("CARD GENERATION SUMMARY")
    print("=" * 60)
    print(f"Template used: {template_pdf}")
    print(f"Total cards created: {card_count}")
    print(f"Total pages: {page_count}")
    print(f"\nPDF saved to: {output_pdf}")
    print("=" * 60 + "\n")
    
    return True


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate printable game cards with QR codes using template')
    parser.add_argument('--poster-dir', default='game/posters',
                       help='Directory containing posters (default: game/posters)')
    parser.add_argument('--output', default='output/printable_cards.pdf',
                       help='Output PDF file (default: output/printable_cards.pdf)')
    parser.add_argument('--template', default='src/card_generation/template.pdf',
                       help='Template PDF file (default: src/card_generation/template.pdf)')
    parser.add_argument('--debug', action='store_true',
                       help='Debug mode: only process the first poster')
    parser.add_argument('--test-positioning', action='store_true',
                       help='Test positioning: only process 4 posters (one per row)')
    parser.add_argument('--add-posters', nargs='?', const='list/add_posters.txt', metavar='ADD_POSTERS_LIST',
                       help='Only generate cards for posters in add_posters.txt (default: list/add_posters.txt)')
    
    args = parser.parse_args()
    
    success = generate_cards_pdf(
        poster_dir=args.poster_dir,
        output_pdf=args.output,
        template_pdf=args.template,
        debug=args.debug,
        test_positioning=args.test_positioning,
        filter_list=args.add_posters
    )
    if not success:
        print("✗ Card generation failed.")
    else:
        print("✓ Card generation completed successfully.")


if __name__ == "__main__":
    main()
