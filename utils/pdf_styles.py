from reportlab.lib import colors as rl_colors
from reportlab.lib.colors import HexColor

# Colors from the provided example (approximate)
COLOR_PRIMARY = HexColor("#1E1E1E") # Dark header/text
COLOR_SECONDARY = HexColor("#e0e0e0") # Light gray for graphical elements
COLOR_ACCENT_BLUE = HexColor("#E6F2FF") # Light blue for boxes? No, looking at image...

# Based on CVImage.jpg
# Headers: White text on Dark Background (almost black)
# Experience/Summary: Dark text on White
# Some blue accents in tags/buttons in the editor, but in PDF it looks clean B&W or grayscale with some blue links.

COLOR_HEADER_BG = HexColor("#1A1F2C") # Dark Navy/Black
COLOR_HEADER_TEXT = rl_colors.white

COLOR_TEXT_MAIN = HexColor("#333333")
COLOR_TEXT_SUB = HexColor("#666666")

COLOR_TAG_BG = HexColor("#E3F2FD") # Light Blue
COLOR_TAG_BORDER = HexColor("#2196F3") # Blue link color
COLOR_LINK = HexColor("#0000CC") # Dark Blue for links

# Fonts
FONT_HEADING = "Helvetica-Bold" # Placeholder, will try to register standard fonts
FONT_BODY = "Helvetica"

# Dimensions
MARGIN = 20
PAGE_WIDTH_A4 = 595.27
PAGE_HEIGHT_A4 = 841.89
