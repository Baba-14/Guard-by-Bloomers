from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib import colors

OUT = Path('output/pdf/guard-low-fi-wireframes.pdf')
W, H = 720, 500
INK = colors.HexColor('#333333')
MID = colors.HexColor('#777777')
LINE = colors.HexColor('#a8a8a8')
PAPER = colors.HexColor('#fafafa')
FILL = colors.HexColor('#eeeeee')
WHITE = colors.white


def text(c, x, y, value, size=8, bold=False, align='left', color=INK):
    c.setFillColor(color)
    c.setFont('Courier-Bold' if bold else 'Courier', size)
    if align == 'center': c.drawCentredString(x, y, value)
    elif align == 'right': c.drawRightString(x, y, value)
    else: c.drawString(x, y, value)


def box(c, x, y, w, h, label='', fill=WHITE, dash=False, radius=2):
    c.setFillColor(fill); c.setStrokeColor(LINE); c.setLineWidth(1)
    c.setDash(5, 3) if dash else c.setDash()
    c.roundRect(x, y, w, h, radius, fill=1, stroke=1)
    c.setDash()
    if label: text(c, x+w/2, y+h/2-3, label, 6.5, True, 'center', MID)


def image(c, x, y, w, h, label='IMAGE'):
    box(c, x, y, w, h, fill=FILL, dash=True)
    c.setStrokeColor(LINE); c.line(x, y, x+w, y+h); c.line(x+w, y, x, y+h)
    text(c, x+w/2, y+h/2-3, label, 7, True, 'center', MID)


def bars(c, x, y, widths, height=7, gap=7):
    c.setFillColor(colors.HexColor('#bdbdbd'))
    for i, width in enumerate(widths): c.roundRect(x, y-i*(height+gap), width, height, 2, fill=1, stroke=0)


def button(c, x, y, w, label='BUTTON', dark=False):
    box(c, x, y, w, 24, fill=INK if dark else WHITE, radius=12)
    text(c, x+w/2, y+8, label, 6.5, True, 'center', WHITE if dark else INK)


def chrome(c, title, number, admin=False):
    c.setFillColor(colors.HexColor('#dddddd')); c.rect(0, H-22, W, 22, fill=1, stroke=0)
    for i in range(3): c.setFillColor(colors.HexColor('#aaaaaa')); c.circle(12+i*12, H-11, 3, fill=1, stroke=0)
    box(c, 65, H-18, 485, 14, f'/{title}', fill=PAPER, radius=7)
    text(c, W-14, H-14, f'{number:02d}', 6.5, True, 'right', MID)
    if admin: return
    box(c, 0, H-62, W, 40, fill=WHITE, radius=0)
    box(c, 74, H-51, 80, 20, 'LOGO', fill=FILL)
    for i, label in enumerate(['NAV 1', 'NAV 2', 'NAV 3', 'NAV 4']): text(c, 408+i*53, H-45, label, 6, True, color=MID)
    button(c, 645, H-54, 48, 'LOGIN', True)


def note(c, label):
    text(c, 14, 10, f'LOW-FI WIREFRAME  |  {label}', 5.8, True, color=MID)


def home(c):
    chrome(c, 'home', 1)
    box(c, 0, 48, W, H-110, fill=FILL, radius=0)
    image(c, 390, 48, 330, H-110, 'HERO IMAGE')
    text(c, 78, 358, 'EYEBROW / CATEGORY', 7, True, color=MID)
    bars(c, 78, 318, [260, 225], 18, 10)
    bars(c, 78, 245, [250, 280, 205], 8, 7)
    box(c, 78, 158, 300, 42, 'PRIMARY CHECK INPUT', fill=WHITE, radius=21)
    button(c, 260, 167, 108, 'CHECK', True)
    bars(c, 82, 137, [190, 235], 5, 6)
    box(c, 0, 0, W, 48, fill=WHITE, radius=0)
    text(c, 78, 25, 'PARTNER / TRUST STRIP', 7, True, color=MID)
    for i in range(5): box(c, 380+i*54, 17, 44, 15, 'LOGO', fill=FILL)
    note(c, 'LANDING PAGE'); c.showPage()


def detect(c):
    chrome(c, 'detect', 2)
    box(c, 0, 175, W, 263, fill=FILL, radius=0)
    text(c, 78, 393, 'EYEBROW', 7, True, color=MID); bars(c, 78, 350, [270, 230], 18, 10); bars(c, 78, 282, [270, 245, 180], 7, 7)
    button(c, 78, 220, 105, 'PRIMARY CTA', True); button(c, 192, 220, 120, 'SECONDARY CTA')
    box(c, 405, 215, 250, 180, 'RISK SUMMARY CARD', fill=WHITE)
    image(c, 422, 308, 62, 62, 'SCORE'); bars(c, 505, 352, [95, 70], 8, 8)
    for i in range(3): box(c, 422, 274-i*25, 215, 18, f'SIGNAL {i+1}', fill=FILL)
    box(c, 422, 220, 215, 22, 'NEXT ACTION', fill=FILL)
    box(c, 0, 125, W, 50, fill=WHITE, radius=0)
    for i in range(4): box(c, 70+i*160, 136, 130, 28, f'STAT {i+1}', fill=PAPER)
    text(c, 90, 88, 'SECTION HEADING', 7, True, color=MID); bars(c, 90, 58, [250, 210], 14, 8); bars(c, 425, 80, [210, 190, 160], 6, 6)
    note(c, 'DETECTION OVERVIEW'); c.showPage()


def checker(c):
    chrome(c, 'detect/payment', 3)
    text(c, 82, 398, 'PAGE CATEGORY', 7, True, color=MID); bars(c, 82, 365, [350], 20, 0); bars(c, 82, 338, [410, 315], 7, 6)
    box(c, 82, 78, 470, 240, fill=WHITE); text(c, 99, 294, 'FORM LABEL', 7, True)
    box(c, 99, 255, 436, 30, 'SELECT / INPUT', fill=PAPER)
    box(c, 99, 130, 436, 112, 'LARGE TEXT AREA', fill=PAPER)
    button(c, 99, 93, 120, 'SUBMIT CHECK', True)
    image(c, 574, 168, 90, 150, 'EVIDENCE')
    note(c, 'CHECK FORM'); c.showPage()


def result(c):
    chrome(c, 'result', 4, True)
    box(c, 52, 31, 616, 424, fill=FILL, radius=8)
    text(c, 72, 430, '< BACK', 6.5, True, color=MID); text(c, 72, 397, 'RESULT TYPE / SUBMITTED ITEM', 7, True, color=MID)
    image(c, 72, 330, 45, 45, 'ICON'); bars(c, 132, 365, [180, 280], 18, 12); bars(c, 132, 320, [350, 290], 7, 7)
    for i in range(4):
        x=72+(i%2)*273; y=235-(i//2)*55; box(c, x, y, 265, 48, f'RESULT DETAIL {i+1}', fill=WHITE)
    box(c, 72, 85, 250, 72, fill=WHITE); text(c, 88, 140, 'WHY FLAGGED', 6.5, True)
    bars(c, 88, 124, [180, 155, 195], 5, 6)
    box(c, 350, 85, 245, 72, fill=WHITE); text(c, 365, 140, 'WHAT TO DO NEXT', 6.5, True)
    button(c, 365, 96, 78, 'REPORT'); button(c, 450, 96, 120, 'CHECK AGAIN', True)
    note(c, 'ASSESSMENT RESULT'); c.showPage()


def report(c):
    chrome(c, 'report', 5)
    text(c, 155, 400, 'PAGE CATEGORY', 7, True, color=MID); bars(c, 155, 367, [360], 20, 0); bars(c, 155, 338, [390, 320], 7, 6)
    box(c, 155, 25, 410, 292, fill=WHITE)
    fields = [(286,252,28),(240,207,28),(195,162,28),(150,117,28),(105,53,48)]
    for i, (label_y, box_y, height) in enumerate(fields):
        text(c, 171, label_y, f'FIELD LABEL {i+1}', 6.5, True)
        box(c, 171, box_y, 378, height, 'DESCRIPTION' if height>40 else 'INPUT', fill=PAPER)
    button(c, 171, 28, 95, 'SUBMIT', True)
    note(c, 'REPORT FORM'); c.showPage()


def dashboard(c):
    chrome(c, 'dashboard', 6)
    text(c, 78, 395, 'PAGE CATEGORY', 7, True, color=MID); bars(c, 78, 361, [250], 20, 0); bars(c, 78, 334, [290], 7, 0)
    for i in range(3): box(c, 78+i*143, 250, 135, 70, f'METRIC {i+1}', fill=WHITE)
    box(c, 78, 105, 565, 128, fill=WHITE); text(c, 92, 211, 'RECENT CHECKS', 8, True)
    box(c, 90, 176, 540, 23, 'TABLE HEADER', fill=FILL)
    for i in range(3): box(c, 90, 145-i*25, 540, 22, f'RECORD {i+1}', fill=PAPER)
    note(c, 'USER DASHBOARD'); c.showPage()


def admin(c):
    chrome(c, 'admin', 7, True)
    box(c, 0, 0, 116, H-22, fill=FILL, radius=0); box(c, 14, 430, 88, 25, 'LOGO', fill=WHITE); text(c, 14, 410, 'ADMIN CONSOLE', 6.5, True, color=MID)
    for i in range(10): box(c, 10, 370-i*34, 96, 24, f'NAV ITEM {i+1}', fill=WHITE if i else colors.HexColor('#d0d0d0'))
    text(c, 134, 445, 'DATE / CONTEXT', 6.5, True, color=MID); bars(c, 134, 416, [170], 18, 0); bars(c, 134, 392, [230], 6, 0); button(c, 625, 426, 74, 'ACTION', True)
    for i in range(8): box(c, 134+(i%4)*143, 334-(i//4)*73, 135, 64, f'METRIC {i+1}', fill=WHITE)
    box(c, 134, 105, 307, 82, 'BAR CHART', fill=WHITE); box(c, 450, 105, 249, 82, 'RISK DISTRIBUTION', fill=WHITE)
    box(c, 134, 15, 307, 82, 'SIGNAL RANKING', fill=WHITE); box(c, 450, 15, 249, 82, 'RECENT REPORTS', fill=WHITE)
    note(c, 'ADMIN CONSOLE'); c.showPage()


def login(c):
    chrome(c, 'login', 8)
    text(c, 234, 395, 'PAGE CATEGORY', 7, True, color=MID); bars(c, 234, 360, [290, 160], 18, 10); bars(c, 234, 310, [300], 7, 0)
    box(c, 234, 65, 252, 228, fill=WHITE)
    text(c, 249, 269, 'EMAIL', 7, True); box(c, 249, 234, 222, 28, 'INPUT', fill=PAPER)
    text(c, 249, 217, 'PASSWORD', 7, True); box(c, 249, 182, 222, 28, 'INPUT', fill=PAPER)
    button(c, 249, 147, 222, 'SIGN IN', True); button(c, 249, 114, 222, 'ALTERNATIVE SIGN IN')
    bars(c, 290, 90, [140], 5, 0); box(c, 249, 72, 222, 14, 'HELPER / DEMO NOTE', fill=FILL)
    note(c, 'SIGN IN'); c.showPage()


def build():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(OUT), pagesize=(W, H))
    c.setTitle('Guard low-fidelity wireframes')
    for page in [home, detect, checker, result, report, dashboard, admin, login]: page(c)
    c.save()


if __name__ == '__main__': build()
