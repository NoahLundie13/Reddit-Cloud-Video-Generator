from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import textwrap

TEMPLATE_PATH = Path(__file__).parent / "utils/frame.png"
OUTPUT_PATH = Path(__file__).parent / "utils/output_image.png"
FONT_PATH = Path(__file__).parent / "utils/Inter_24pt-Bold.ttf"

FONT_SIZE = 97
TEXT_COLOR = (0, 0, 0)
PADDING_X = 80
LINE_SPACING = 22
TOP_MARGIN = 283
BOTTOM_MARGIN = 204
FRAME_TOP_PRESERVE = 485
FRAME_BOTTOM_PRESERVE = 380
HEIGHT_PER_EXTRA_LINE = 120
MAX_LINES = 2


def generate_frame(title_text: str):
    base = Image.open(TEMPLATE_PATH).convert("RGBA")
    
    try:
        font = ImageFont.truetype(str(FONT_PATH), FONT_SIZE)
    except OSError:
        print("Could not open font - using default PIL font.")
        font = ImageFont.load_default()
    
    draw = ImageDraw.Draw(base)
    
    usable_width = base.width - (2 * PADDING_X)
    
    words = title_text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        test_width = font.getlength(test_line)
        
        if test_width <= usable_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    line_height = font.getbbox("Ay")[3] - font.getbbox("Ay")[1]
    
    if len(lines) > MAX_LINES:
        extra_lines = len(lines) - MAX_LINES
        extra_height_needed = extra_lines * HEIGHT_PER_EXTRA_LINE
        
        width, height = base.size
        new_height = height + extra_height_needed
        
        extended = Image.new("RGBA", (width, new_height), (255, 255, 255, 255))
        
        extended.paste(base.crop((0, 0, width, FRAME_TOP_PRESERVE)), (0, 0))
        
        bottom_source_y = height - FRAME_BOTTOM_PRESERVE
        bottom_dest_y = new_height - FRAME_BOTTOM_PRESERVE
        extended.paste(
            base.crop((0, bottom_source_y, width, height)), 
            (0, bottom_dest_y)
        )
        
        base = extended
        draw = ImageDraw.Draw(base)
    
    total_text_height = (line_height * len(lines)) + (LINE_SPACING * (len(lines) - 1))
    
    text_block = "\n".join(lines)
    
    text_bbox = draw.multiline_textbbox((0, 0), text_block, font=font, spacing=LINE_SPACING)
    text_h = text_bbox[3] - text_bbox[1]
    
    x = PADDING_X
    
    available_space_top = TOP_MARGIN
    available_space_bottom = base.height - BOTTOM_MARGIN
    total_available = available_space_bottom - available_space_top
    y = available_space_top + (total_available - text_h) / 2
    
    draw.multiline_text(
        (x, y),
        text_block,
        font=font,
        fill=TEXT_COLOR,
        align="left",
        spacing=LINE_SPACING
    )
    
    base.save(OUTPUT_PATH)
    print(f"Frame saved to {OUTPUT_PATH}")
