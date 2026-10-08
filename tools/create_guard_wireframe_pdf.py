from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.pdfbase.pdfmetrics import stringWidth

OUT = Path('output/pdf/guard-low-fidelity-prototype.pdf')
W, H = 720, 500
INK = colors.HexColor('#202326'); DARK = colors.HexColor('#34373a')
MID = colors.HexColor('#73787c'); LINE = colors.HexColor('#b8bdc1')
SOFT = colors.HexColor('#e6e8e9'); PALE = colors.HexColor('#f4f5f5'); WHITE = colors.white

def text(c,x,y,s,size=8,bold=False,color=INK,align='left'):
    c.setFillColor(color); c.setFont('Helvetica-Bold' if bold else 'Helvetica',size)
    if align=='center': c.drawCentredString(x,y,s)
    elif align=='right': c.drawRightString(x,y,s)
    else: c.drawString(x,y,s)

def wrapped(c,x,y,s,width,size=8,leading=11,color=MID,bold=False,max_lines=5):
    font='Helvetica-Bold' if bold else 'Helvetica'; words=s.split(); lines=[]; current=''
    for word in words:
        candidate=(current+' '+word).strip()
        if stringWidth(candidate,font,size)<=width or not current: current=candidate
        else: lines.append(current); current=word
    if current: lines.append(current)
    for i,value in enumerate(lines[:max_lines]): text(c,x,y-i*leading,value,size,bold,color)

def rect(c,x,y,w,h,fill=WHITE,stroke=LINE,radius=5,dash=False,width=.7):
    c.setFillColor(fill); c.setStrokeColor(stroke); c.setLineWidth(width)
    c.setDash(4,3) if dash else c.setDash(); c.roundRect(x,y,w,h,radius,fill=1,stroke=1); c.setDash()

def line(c,x1,y1,x2,y2,color=LINE,width=.7):
    c.setStrokeColor(color); c.setLineWidth(width); c.line(x1,y1,x2,y2)

def pill(c,x,y,w,s,fill=INK,color=WHITE,outline=None):
    c.setFillColor(fill); c.setStrokeColor(outline or fill); c.setLineWidth(.8); c.roundRect(x,y,w,24,12,fill=1,stroke=1)
    text(c,x+w/2,y+8,s,7.4,True,color,'center')

def browser(c,path,n):
    c.setFillColor(colors.HexColor('#d7d9da')); c.rect(0,H-22,W,22,fill=1,stroke=0)
    for i,shade in enumerate(['#8c9093','#a7abad','#c2c5c7']): c.setFillColor(colors.HexColor(shade)); c.circle(12+i*12,H-11,3,fill=1,stroke=0)
    rect(c,62,H-18,500,14,fill=PALE,stroke=LINE,radius=7); text(c,72,H-14,f'guard.local{path}',6.5,color=MID); text(c,W-12,H-14,f'{n:02d}',6.5,True,MID,'right')

def site_header(c,y,dark=False):
    bg=DARK if dark else WHITE; fg=WHITE if dark else INK
    c.setFillColor(bg); c.rect(0,y-40,W,40,fill=1,stroke=0)
    if not dark: line(c,0,y-40,W,y-40,SOFT)
    c.setStrokeColor(fg); c.setLineWidth(2); c.circle(82,y-20,8,fill=0,stroke=1); line(c,76,y-20,88,y-20,fg,2); text(c,95,y-24,'GUARD',10,True,fg)
    for s,x in [('Home',414),('Check Fraud',460),('Community',524),('Business',592)]: text(c,x,y-24,s,6.5,True,fg)
    pill(c,644,y-32,45,'Login',fill=INK if not dark else MID,color=WHITE)

def image_placeholder(c,x,y,w,h,s='IMAGE PLACEHOLDER',dark=False):
    fill=colors.HexColor('#595d60') if dark else SOFT; stroke=colors.HexColor('#8c9296') if dark else LINE
    rect(c,x,y,w,h,fill=fill,stroke=stroke,radius=0); line(c,x,y,x+w,y+h,stroke); line(c,x+w,y,x,y+h,stroke); text(c,x+w/2,y+h/2-3,s,7,True,WHITE if dark else MID,'center')

def label(c,x,y,s,color=MID): text(c,x,y,s.upper(),6.2,True,color)
def input_box(c,x,y,w,h,s,multi=False): rect(c,x,y,w,h,fill=WHITE,stroke=LINE,radius=4); wrapped(c,x+10,y+h-15,s,w-20,7.5,10,colors.HexColor('#999da0'),max_lines=4 if multi else 1)

def home(c):
    browser(c,'/',1); top=H-22; c.setFillColor(DARK); c.rect(0,48,W,top-48,fill=1,stroke=0); site_header(c,top,True)
    image_placeholder(c,354,48,366,top-88,'HERO PHOTO',True); c.setFillColor(colors.Color(.17,.18,.19,alpha=.88)); c.rect(0,48,410,top-88,fill=1,stroke=0)
    label(c,78,360,'Mobile Money fraud prevention',WHITE); text(c,78,320,'Keep your money',31,True,WHITE); text(c,78,286,'safe from fraud.',31,True,WHITE)
    wrapped(c,78,252,'Check a Mobile Money request, payment screenshot, recipient, message, number or link before you send money or release goods.',285,9.5,14,colors.HexColor('#dddddd'),max_lines=4)
    rect(c,78,160,300,40,fill=WHITE,stroke=LINE,radius=20); text(c,94,176,'Describe the payment request or paste a link',7.8,color=MID); pill(c,258,168,112,'Check before paying')
    text(c,82,142,'Never submit a PIN, password, or OTP.',6.2,color=SOFT); text(c,82,120,'[shield]  Check before you pay. No account needed.',6.8,color=WHITE)
    c.setFillColor(PALE); c.rect(0,0,W,48,fill=1,stroke=0); label(c,78,25,'Growing the safety ecosystem')
    for i,s in enumerate(['Mobile Money','Merchants','Banking partners','CSA Ghana','Community networks']): text(c,390+i*54,24,s,5.3,True,MID,'center')
    c.showPage()

def detect(c):
    browser(c,'/detect',2); top=H-22; site_header(c,top); c.setFillColor(DARK); c.rect(0,175,W,top-215,fill=1,stroke=0)
    label(c,78,389,'Mobile Money fraud detection',WHITE); text(c,78,350,'Check before your',30,True,WHITE); text(c,78,316,'money moves.',30,True,WHITE)
    wrapped(c,78,285,'Guard examines suspicious Mobile Money requests, recipient details, screenshots, messages, numbers, links, and calls.',290,8.8,13,SOFT)
    pill(c,78,220,105,'Check before I pay',fill=WHITE,color=INK); pill(c,190,220,115,'Report a payment scam',fill=DARK,color=WHITE,outline=LINE); text(c,80,198,'[shield] Explainable guidance. No account needed.',6.2,color=SOFT)
    rect(c,407,210,248,185,fill=colors.HexColor('#292c2f'),stroke=MID,radius=9); text(c,421,374,'[icon] Guard payment review',6.6,True,WHITE); label(c,606,374,'Before you pay',WHITE); line(c,421,365,641,365,MID)
    c.setStrokeColor(WHITE); c.setLineWidth(5); c.circle(444,332,25,fill=0,stroke=1); text(c,444,328,'72',15,True,WHITE,'center'); label(c,482,342,'Payment assessment',SOFT); text(c,482,325,'CAUTION',14,True,WHITE)
    for i,(a,b) in enumerate([('Request pattern','Urgent payment'),('Recipient signal','Name changed'),('Community signal','Related reports')]):
        y=292-i*25; rect(c,420,y,220,18,fill=DARK,stroke=MID,radius=3); text(c,428,y+6,a,5.8,color=SOFT); text(c,631,y+6,b,5.8,True,WHITE,'right')
    rect(c,420,218,220,20,fill=SOFT,stroke=SOFT,radius=3); text(c,430,225,'[check] Pause and verify the recipient',6.2,True)
    c.setFillColor(PALE); c.rect(0,125,W,50,fill=1,stroke=0)
    for i,(n,a) in enumerate([('MoMo','Payment-first protection'),('7','Ways to add evidence'),('1','Clear next action'),('0','PINs or OTPs required')]):
        x=90+i*150; text(c,x,151,n,13,True); label(c,x,136,a)
        if i<3: line(c,x+120,125,x+120,175)
    label(c,100,91,'Protect your money'); text(c,100,66,'What happened before',19,True); text(c,100,44,'the payment?',19,True); wrapped(c,420,82,'Start with the payment request or choose the message, screenshot, number, link, or call connected to it.',220,7.5,11,MID)
    c.showPage()

def checker(c):
    browser(c,'/detect/payment',3); top=H-22; site_header(c,top); label(c,82,398,'Fraud check'); text(c,82,366,'Check before you send money',25,True)
    wrapped(c,82,345,'Submit only what you are comfortable sharing. Treat everything you upload as private, untrusted content.',450,8.4,12,MID)
    rect(c,82,75,470,245,fill=WHITE,stroke=LINE,radius=6); text(c,99,296,'Tell Guard about the Mobile Money or payment request',7.5,True); input_box(c,99,258,436,28,'Individual or business')
    input_box(c,99,129,436,118,'Include the amount, recipient name or number, what they claimed, and how they asked you to pay...',True); pill(c,99,92,116,'Check before paying')
    rect(c,573,170,92,150,fill=PALE,stroke=LINE,radius=5,dash=True); text(c,619,258,'[ + ]',18,True,MID,'center'); text(c,619,235,'OPTIONAL',6.5,True,MID,'center'); wrapped(c,586,218,'Add a screenshot or supporting evidence',66,6.8,9,MID,max_lines=5)
    text(c,82,46,'Low-fidelity placement: title + primary form + optional evidence.',6.5,color=MID); c.showPage()

def result(c):
    browser(c,'/result',4); c.setFillColor(PALE); c.rect(0,0,W,H-22,fill=1,stroke=0); rect(c,52,30,616,425,fill=DARK,stroke=DARK,radius=10)
    text(c,72,432,'< Back to Guard',6.5,color=SOFT); label(c,72,397,'Guard intelligence result - phone number',SOFT); text(c,72,350,'[ ! ]',24,True,WHITE); text(c,112,354,'CAUTION',29,True,WHITE)
    wrapped(c,112,334,'The request contains warning signs that should be verified independently.',430,9,13,SOFT); wrapped(c,72,302,'This assessment is decision support based on the information submitted. It is not a legal determination of fraud or safety.',520,6.7,10,SOFT)
    cards=[('LIKELY PATTERN','Urgent payment request'),('SUBMITTED ITEM','024 XXX XXXX'),('RECOMMENDED ACTION','Pause and verify'),('GUARD STATUS','Reviewed just now')]
    for i,(a,b) in enumerate(cards):
        x=72+(i%2)*273; y=235-(i//2)*54; rect(c,x,y,265,48,fill=colors.HexColor('#414548'),stroke=MID,radius=3); label(c,x+12,y+30,a,SOFT); text(c,x+12,y+13,b,8.5,True,WHITE)
    text(c,72,152,'Why Guard flagged it',11,True,WHITE)
    for i,s in enumerate(['Urgent language or pressure','Recipient details need verification','Related report pattern found']): text(c,76,132-i*16,f'( ! )  {s}',7.2,color=SOFT)
    line(c,345,92,345,155,MID); text(c,372,152,'What to do next',11,True,WHITE); wrapped(c,372,132,'Pause the payment and verify the recipient through a different trusted channel.',220,7.5,11,SOFT)
    pill(c,372,91,78,'Report this',fill=DARK,color=WHITE,outline=LINE); pill(c,456,91,105,'Check something else',fill=WHITE,color=INK); c.showPage()

def report(c):
    browser(c,'/report',5); top=H-22; site_header(c,top); label(c,155,399,'Help prevent financial loss'); text(c,155,368,'Report a suspicious payment.',24,True)
    wrapped(c,155,346,'Share a payment route, account, screenshot, number, message, or link. Your report can help identify recurring patterns.',410,8.2,12,MID)
    rect(c,155,25,410,292,fill=WHITE,stroke=LINE,radius=6); text(c,171,294,'What are you reporting?',7,True); input_box(c,171,260,378,26,'Mobile Money or payment account')
    rect(c,171,223,378,28,fill=PALE,stroke=LINE,radius=4); text(c,182,238,'[icon]  Mobile Money or payment fraud',6.8,True); text(c,182,228,'Recipient details, reversal requests, fake alerts, or payment pressure.',5.6,color=MID)
    text(c,171,207,'Fraud category',7,True); input_box(c,171,178,378,24,'Mobile Money Fraud'); text(c,171,163,'Recipient number, account name, or reference',7,True); input_box(c,171,133,378,24,'Add the payment identifier you can safely share')
    text(c,171,117,'What happened?',7,True); input_box(c,171,54,378,54,'Describe the amount, recipient, payment route, and what you were told...',True); pill(c,171,28,90,'Submit report'); c.showPage()

def dashboard(c):
    browser(c,'/dashboard',6); top=H-22; site_header(c,top); label(c,78,393,'Your dashboard'); text(c,78,362,'Good to see you.',25,True); text(c,78,340,'A calm view of your recent decisions and reports.',8.5,color=MID)
    for i,(a,b,d) in enumerate([('Total checks','24','+4 this month'),('Reports submitted','3','1 under review'),('Saved results','8','Keep what matters')]):
        x=78+i*143; rect(c,x,250,135,70); text(c,x+10,301,a,6.5,color=MID); text(c,x+10,277,b,15,True); text(c,x+10,261,d,5.8,color=MID)
    rect(c,78,105,565,128); text(c,90,212,'Recent checks',8.5,True); text(c,629,212,'View all >',6.5,True,MID,'right'); c.setFillColor(PALE); c.rect(88,177,545,23,fill=1,stroke=0)
    for x,s in [(95,'TYPE'),(255,'RESULT'),(465,'WHEN')]: label(c,x,185,s)
    for i,row in enumerate([('Phone Number','Caution','Today'),('Message','High Risk','Yesterday'),('Link','Unable to Determine','18 Sep')]):
        y=159-i*24; line(c,88,y-7,633,y-7,SOFT); text(c,95,y,row[0],6.8); rect(c,255,y-5,72 if i==2 else 45,14,fill=SOFT,stroke=SOFT,radius=7); text(c,261,y,row[1],5.5,True); text(c,465,y,row[2],6.8); text(c,590,y,'(check)',6.2,color=MID)
    c.showPage()

def admin(c):
    browser(c,'/admin',7); c.setFillColor(PALE); c.rect(0,0,W,H-22,fill=1,stroke=0); c.setFillColor(DARK); c.rect(0,0,116,H-22,fill=1,stroke=0)
    text(c,16,447,'(C) GUARD',11,True,WHITE); label(c,16,422,'Intelligence console',SOFT)
    nav=['Overview','Fraud Reports','Phone Numbers','Fraud Intelligence','Fraud Checks','Fraud Patterns','Detection Rules','Users','Analytics','Education Content','Audit Logs','Settings']
    for i,s in enumerate(nav):
        y=394-i*29
        if i==0: rect(c,8,y-9,100,24,fill=colors.HexColor('#505356'),stroke=colors.HexColor('#505356'),radius=3)
        text(c,16,y,f'[ ]  {s}',6.3,i==0,WHITE if i==0 else SOFT)
    label(c,134,445,'Tuesday, 22 September 2026'); text(c,134,419,'Risk overview',20,True); text(c,134,404,'Signals, reports and emerging patterns across Guard.',7.3,color=MID); pill(c,625,426,74,'+ Create alert')
    metrics=[('Total fraud checks','18,426'),('High-risk checks','2,184'),('Reports received','642'),('Pending reviews','48'),('Reported numbers','1,204'),('Active users','8,921'),('Evidence-backed','71%'),('Entities tracked','3,487')]
    for i,(a,b) in enumerate(metrics):
        x=134+(i%4)*143; y=334-(i//4)*73; rect(c,x,y,135,64); text(c,x+9,y+45,a,6.1,color=MID); text(c,x+9,y+23,b,13.5,True); text(c,x+9,y+9,'+12.4%',5.5,color=MID)
    rect(c,134,105,307,82); text(c,144,170,'Fraud checks over time',7.5,True)
    for i,h in enumerate([24,36,29,43,32,52,44,58,48,63,55,68]): c.setFillColor(MID if i<9 else INK); c.rect(148+i*22,119,14,h*.65,fill=1,stroke=0)
    rect(c,450,105,249,82); text(c,461,170,'Risk distribution',7.5,True)
    for i,(a,p) in enumerate([('Low',58),('Caution',27),('High',11),('Unknown',4)]):
        y=149-i*14; text(c,461,y,a,5.8,color=MID); c.setFillColor(SOFT); c.rect(507,y-1,145,4,fill=1,stroke=0); c.setFillColor(INK); c.rect(507,y-1,145*p/100,4,fill=1,stroke=0); text(c,680,y,f'{p}%',5.8,True,MID,'right')
    rect(c,134,15,307,82); text(c,144,80,'Most common warning signals',7.5,True)
    for i,(a,p) in enumerate([('OTP request',82),('Suspicious link',71),('Advance payment',55),('Urgency',49)]):
        y=61-i*13; text(c,144,y,a,5.6,color=MID); c.setFillColor(SOFT); c.rect(210,y-1,190,4,fill=1,stroke=0); c.setFillColor(INK); c.rect(210,y-1,190*p/100,4,fill=1,stroke=0)
    rect(c,450,15,249,82); text(c,461,80,'Recent reports',7.5,True)
    for i,row in enumerate([('024 555 0182','MoMo','Review'),('pay-now-gh.com','Phishing','Verified'),('+233 20...','Delivery','Pending')]): y=61-i*15; text(c,461,y,row[0],5.5); text(c,540,y,row[1],5.5); text(c,630,y,row[2],5.5,True)
    c.showPage()

def login(c):
    browser(c,'/login',8); top=H-22; site_header(c,top); label(c,234,394,'Your Guard'); text(c,234,362,'Sign in to keep your checks',22,True); text(c,234,337,'together.',22,True); text(c,234,315,'Save results, review reports and manage privacy settings.',8,color=MID)
    rect(c,234,65,252,228); text(c,249,267,'Email address',7,True); input_box(c,249,235,222,26,'admin@guard.test'); text(c,249,218,'Password',7,True); input_box(c,249,186,222,26,'********')
    pill(c,249,149,222,'Sign in'); pill(c,249,116,222,'Continue with Google',fill=WHITE,color=INK,outline=LINE); text(c,360,94,'New to Guard?  Create an account',6.4,True,MID,'center'); rect(c,249,73,222,15,fill=PALE,stroke=PALE,radius=3); text(c,360,78,'Demo credentials placeholder',5.8,color=MID,align='center'); c.showPage()

def build():
    OUT.parent.mkdir(parents=True,exist_ok=True); c=canvas.Canvas(str(OUT),pagesize=(W,H)); c.setTitle('Guard low-fidelity website screens'); c.setAuthor('Guard team')
    for page in [home,detect,checker,result,report,dashboard,admin,login]: page(c)
    c.save()

if __name__=='__main__': build()
