from typing import Optional
from PIL import Image, ImageDraw, ImageFont
from fastapi import HTTPException
import os
from pathlib import Path
from src.crop import crop_to_4x5


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Load a font at the requested size.

    Attempts to load DejaVuSans on Linux or falls back to system fonts
    on macOS and other platforms.

    Args:
        size: Font size in points.
        bold: Whether to load the bold variant.

    Returns:
        A PIL ImageFont instance.
    """
    import platform

    system = platform.system()

    # No hay soporte para windows pq pa que ¯\_(ツ)_/¯

    if system == "Linux":
        # Linux path for DejaVu fonts
        font_name = f"DejaVuSans{'-Bold' if bold else ''}.ttf"
        font_path = f"/usr/share/fonts/truetype/dejavu/{font_name}"
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, size)
            except IOError:
                print(f"No se ha encontrado la fuente {font_name}")

    elif system == "Darwin":  # macOS
        list_fonts = ["Helvetica", "Arial", "ArialMT"]
        if bold:
            list_fonts = ["Helvetica-Bold", "Arial Bold", "Arial-BoldMT"]

        # macOS system font_side
        for font_name in list_fonts:
            try:
                return ImageFont.truetype(font_name, size)
            except IOError:
                print(f"No se ha encontrado la fuente {font_name}")

    # Fallback to default PIL font if nothing works
    try:
        return ImageFont.load_default()
    except IOError:
        # Last resort: try to use any available TrueType font
        return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size)

def _load_fonts(main_font_size: int, side_font_size: int) -> dict:
    return {
        "bold": _load_font(main_font_size, bold=True),
        "regular": _load_font(main_font_size, bold=False),
        "side": _load_font(side_font_size, bold=False),
    }

def calculate_real_width(text_str, highlights_list, draw_dummy, fonts):
    """Calculate the REAL width as it will be drawn, char by char with correct fonts."""
    
    total_width = 0
    for i, char in enumerate(text_str):
        is_highlighted = i < len(highlights_list) and highlights_list[i]
        char_font = fonts["bold"] if is_highlighted else fonts["regular"]
        total_width += draw_dummy.textlength(char, font=char_font)
    return total_width

# Word-based wrapping that preserves exact highlight positions and doesn't cut words
def wrap_text_with_highlights(text, highlight_mask, max_width, draw_dummy, fonts):
    """Wrap text by words while preserving exact character-level highlight information."""

    lines = []
    words = text.split()  # Split by whitespace

    current_line_words = []
    current_line_highlights = []
    char_position = 0

    for word in words:
        # Find the word's position in the original text
        word_start = text.find(word, char_position)
        word_end = word_start + len(word)

        # Get highlight info for this word
        word_highlight_chars = []
        for i in range(word_start, word_end):
            if i < len(highlight_mask):
                word_highlight_chars.append(highlight_mask[i])
            else:
                word_highlight_chars.append(False)

        # Build candidate line with proper spacing
        if current_line_words:
            candidate_text = " ".join(current_line_words + [word])
            candidate_highlights = (
                current_line_highlights + [False] + word_highlight_chars
            )  # False for space
        else:
            candidate_text = word
            candidate_highlights = word_highlight_chars

        # Calculate REAL width as it will be rendered
        candidate_width = calculate_real_width(candidate_text, candidate_highlights, draw_dummy, fonts)

        # Be VERY conservative - use 80% of available width with safety margin
        if candidate_width * 1.15 <= max_width:  # 15% safety margin
            current_line_words.append(word)
            if current_line_highlights:
                current_line_highlights.append(False)  # Add space highlight
            current_line_highlights.extend(word_highlight_chars)
        else:
            # Line is full, save it and start new line
            if current_line_words:
                line_text = " ".join(current_line_words)
                lines.append((line_text, current_line_highlights))

            # Start new line with current word
            current_line_words = [word]
            current_line_highlights = word_highlight_chars

        # Update character position
        char_position = word_end

    # Add the last line
    if current_line_words:
        line_text = " ".join(current_line_words)
        lines.append((line_text, current_line_highlights))

    return lines


def create_composite_image(
    base_image: Image.Image,
    headline: str,
    highlight: str,
    *,
    formato: Optional[str] = "*",
    logo_image: Optional[Image.Image] = None,
    watermark_text: str = "diarioeldia.cl",
    highlight_color: tuple[int, int, int] = (0, 64, 145),
    text_color: tuple[int, int, int] = (0, 0, 0),
    box_color: tuple[int, int, int, int] = (255, 255, 255, 230),
    logo_scale: float = 0.10,
    recorte: Optional[str] = None, # Sabemos que solo se ocupa recorte para formato ig
) -> dict:
    """Compose a new image by drawing text and a logo over a base photograph.

    This helper encapsulates the layout logic used to build the final
    composite. It draws a watermark along the left edge, splits the
    headline into a highlighted segment and the remainder, wraps the
    remainder into lines, and draws irregularly sized boxes behind each
    line of text. A logo is also placed in the top-right corner.

    Args:
        base_image: The background photograph. It should be in RGB or RGBA mode.
        headline: The full headline to display on the image.
        highlight: The portion of the headline to emphasize (rendered in
            `highlight_color`). Only the first occurrence of this string
            will be removed from the remainder. If it is not found,
            `highlight` will be used as the highlighted line and the
            remainder will be the original headline.
        logo_image: A PIL image of the logo. If None, this function
            attempts to load ``El_Dia.png`` from the current directory.
        watermark_text: A short string to repeat vertically along the
            left-hand margin.
        highlight_color: RGB tuple for the highlighted line.
        text_color: RGB tuple for the non-highlight lines.
        box_color: RGBA tuple for the text box backgrounds. The fourth
            value controls transparency (0=transparent, 255=opaque).
        logo_scale: Fraction of the base image width to use as the logo
            width. Height is scaled to preserve aspect ratio.

    Returns:
        A new PIL Image containing the composed graphic.
    """

    ret = {}

    # Detectamos que formatos usar
    formatos_disponibles = ["facebook", "instagram"]
    for_usar = []
    
    for frm_actual in formato.split(','):
        if frm_actual.lower() in formatos_disponibles:
            for_usar.append(frm_actual.lower())

    if formato == "*":
        for_usar = formatos_disponibles

    if len(for_usar) == 0: 
        raise HTTPException("Error: Invalid Format.")


    # Ensure we are working on a copy in RGBA mode
    img = base_image.convert("RGBA").copy()

    for frm in for_usar:
    # Resize para formato Instagram 4:5 (1080x1350) si es necesario
        if frm == "instagram":
            # Parse recorte parameter si existe (formato: "x,y,w,h" en valores 0..1)
            rel_box = None

            if recorte:
                try:
                    parts = [float(v.strip()) for v in recorte.split(",")]
                    if len(parts) == 4:
                        rel_box = tuple(parts)
                except (ValueError, AttributeError):
                    # Si hay error en el formato, usar recorte centrado por defecto
                    pass
            
            box = None
            if rel_box is not None:
                box = {
                    "x": rel_box[0],
                    "y": rel_box[1],
                    "w": rel_box[2],
                    "h": rel_box[3]
                }            

            # Usar la función de recorte 4:5 avanzada
            img = crop_to_4x5('', # Porque me dio lata sacarle el path como argumento obligatorio
                            _img = img,
                            rel_box=box,
                            anchor="center", 
                            resize_to=(1080, 1350)
            )

        width, height = img.size

        # Determine sizes for fonts relative to image height
        # Para Instagram usamos fuentes más pequeñas para mejor distribución del texto
        if frm == "instagram":
            main_font_size = max(12, int(height * 0.038))  # 37% más pequeño para Instagram
            side_font_size = max(8, int(height * 0.022))
        else:
            main_font_size = max(12, int(height * 0.06))  # tamaño normal para horizontal
            side_font_size = max(8, int(height * 0.03))

        # Load fonts
        fonts = _load_fonts(main_font_size, side_font_size)

        # Prepare watermark along the left side
        # Para Instagram usamos barra lateral más delgada para más espacio de texto
        if frm == "instagram":
            bar_width = int(width * 0.05)  # Barra más delgada en Instagram
        else:
            bar_width = int(width * 0.07)  # Barra normal en horizontal

        # Create a temporary image for rendering horizontal watermark text
        temp = Image.new("RGBA", (height, bar_width), (0, 0, 0, 0))
        draw_temp = ImageDraw.Draw(temp)

        # Build a repeated string to fill the width when rotated
        phrase = watermark_text + "   "
        phrase_width = draw_temp.textlength(phrase, font=fonts["side"])

        repeats = int((height / phrase_width)) + 3
        full_text = phrase * repeats
        
        y_offset = (bar_width - fonts["side"].getbbox("Ay")[3]) // 2
        draw_temp.text((0, y_offset), full_text, font=fonts["side"], fill=(255, 255, 255, 150))
        
        # Rotate to create vertical text and paste on base image
        vertical_img = temp.rotate(90, expand=True)
        img.paste(vertical_img, (0, 0), vertical_img)

        # Load or resize the logo
        if logo_image is not None:
            logo_w = int(width * logo_scale)

            # Maintain aspect ratio
            logo_h = int(logo_w * logo_image.height / logo_image.width)
            logo_resized = logo_image.resize((logo_w, logo_h), Image.Resampling.LANCZOS)

            # Paste the logo in the top right corner with a small margin
            img.paste(logo_resized, (width - logo_w - 10, 10), logo_resized)
            
        else:
            try:
                # Attempt to load a default logo from the current directory
                logo_image = Image.open(f"{Path(__file__).resolve().parent.parent}/El_Dia.png").convert("RGBA")
            except Exception:
                logo_image = None
        

        # Compute available width for text (excluding left bar and margins)
        # Para Instagram damos más espacio horizontal al texto
        if frm == "instagram":
            available_width = width - bar_width - 10  # Menos margen en Instagram
        else:
            available_width = width - bar_width - 20  # Margen normal en horizontal

        draw_dummy = ImageDraw.Draw(Image.new("RGB", (10, 10)))

        # Create a character-by-character map of which characters are highlighted
        highlight_mask = [False] * len(headline)

        if highlight and highlight in headline:
            highlight_start = headline.find(highlight)
            highlight_end = highlight_start + len(highlight)
            
            for i in range(highlight_start, highlight_end):
                if i < len(headline):
                    highlight_mask[i] = True

        

        # Wrap the headline with variable line widths - calculate real width char by char
        # Para Instagram usamos más ancho disponible (90% vs 85%)
        wrap_factor = 0.90 if frm == "instragram" else 0.85
        wrapped_lines = wrap_text_with_highlights(
            headline, highlight_mask, available_width * wrap_factor, draw_dummy, fonts
        )

        # Calculate dimensions for each line
        padding_x = 20
        padding_y = 10
        line_spacing = 8
        line_heights = []
        line_widths = []

        

        for line_text, line_highlights in wrapped_lines:
            # Calculate REAL width considering bold and regular characters
            real_width = calculate_real_width(line_text, line_highlights, draw_dummy, fonts)
            line_widths.append(real_width)

            # Height can use regular font as reference
            bbox = draw_dummy.textbbox((0, 0), line_text, font=fonts["regular"])
            line_heights.append(bbox[3] - bbox[1])

        # Calculate total height
        total_boxes_height = sum(h + 2 * padding_y for h in line_heights)
        total_boxes_height += line_spacing * (len(wrapped_lines) - 1)
        start_y = height - total_boxes_height - 20
        current_y = start_y

        # Draw each line with variable width and centered
        for idx, (line_text, line_highlights) in enumerate(wrapped_lines):
            text_w = line_widths[idx]
            text_h = line_heights[idx]
            box_w = text_w + 2 * padding_x
            box_h = text_h + 2 * padding_y

            # Center each line individually within the available space
            x = bar_width + (available_width - box_w) // 2
            y = current_y

            # Create the box
            box_img = Image.new("RGBA", (int(box_w), int(box_h)), box_color)
            box_draw = ImageDraw.Draw(box_img)

            # Draw text character by character with appropriate colors and fonts
            text_x = padding_x

            # Calculate baseline offset to align bold and regular text
            regular_bbox = draw_dummy.textbbox((0, 0), "Ay", font=fonts["regular"])
            bold_bbox = draw_dummy.textbbox((0, 0), "Ay", font=fonts["bold"])
            regular_baseline = regular_bbox[3]  # bottom of regular font
            bold_baseline = bold_bbox[3]  # bottom of bold font
            baseline_offset = regular_baseline - bold_baseline

            # Calculate vertical centering - get actual text height
            text_bbox = draw_dummy.textbbox((0, 0), line_text, font=fonts["regular"])
            actual_text_height = text_bbox[3] - text_bbox[1]

            # Center text vertically in the box
            text_y_offset = (box_h - actual_text_height) // 2

            for char_idx, char in enumerate(line_text):
                # Check if this character is highlighted
                is_highlighted = (
                    char_idx < len(line_highlights) and line_highlights[char_idx]
                )
                color = highlight_color if is_highlighted else text_color
                font = fonts["bold"] if is_highlighted else fonts["regular"]

                # Adjust Y position for bold text to align with regular text + vertical centering
                y_position = text_y_offset + (baseline_offset if is_highlighted else 0)

                # Draw the character
                box_draw.text((text_x, y_position), char, font=font, fill=color)

                # Move x position (use the correct font for width calculation)
                char_width = draw_dummy.textlength(char, font=font)
                text_x += char_width

            # Paste onto the base image
            img.paste(box_img, (int(x), int(y)), box_img)

            # Move to next line
            current_y += box_h + line_spacing

        print(frm)
        ret[frm] = img

    return ret