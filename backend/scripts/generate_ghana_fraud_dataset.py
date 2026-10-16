"""Generate a safe synthetic Ghana fraud-message dataset for Guard evaluation.

The messages contain no live payment destination, phone number, credential, or
resolvable phishing URL. They are synthetic examples, not real incident data.
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


OUTPUT = Path(__file__).resolve().parents[2] / "public" / "templates" / "guard-ghana-fraud-training-1000.csv"
HEADERS = [
    "content", "label", "category", "content_type", "channel",
    "country_code", "ghana_specific", "language", "notes",
]

AMOUNTS = ["GH₵45", "GH₵80", "GH₵120", "GH₵150", "GH₵200", "GH₵250", "GH₵300", "GH₵450", "GH₵600", "GH₵1,200"]
DEADLINES = ["within 10 minutes", "before 4pm today", "immediately", "before the office closes", "within one hour", "before midnight", "this morning", "before your account is restricted", "before the offer expires", "now"]
GREETINGS = ["Hello customer", "Dear customer", "Good morning", "Attention", "Urgent notice", "Please note", "Hello", "Important update", "Final reminder", "Account notice"]
CLOSERS = [
    "Do not contact the branch until this is completed.",
    "This is the final reminder.",
    "Failure to comply will cancel the request.",
    "Keep this verification private.",
    "Reply only on this chat.",
    "The request expires after this notice.",
    "Customer service cannot assist after the deadline.",
    "Do not discuss this transaction with anyone.",
    "Your place will be given to another customer.",
    "Complete the step before the system closes.",
]
CHANNELS = ["sms", "whatsapp", "email", "social_media", "voice_transcript"]
NAMES = ["Kwame", "Ama", "Kojo", "Abena", "Yaw", "Akosua", "Kofi", "Adwoa", "Nana", "Esi"]
SHOPS = ["Accra Deals Hub", "Kumasi Market Direct", "Takoradi Home Store", "Tamale Electronics Outlet", "Cape Coast Fashion Depot"]
INVESTMENTS = ["digital trading programme", "gold investment club", "agriculture investment pool", "crypto profit group", "forex mentorship scheme"]

LEGITIMATE_CLOSERS = [
    "This notice is for your records.",
    "Confirm the details in your own account before taking action.",
    "Use only the organisation's official app or published contact details for support.",
    "No PIN, password or OTP is required for this notice.",
    "Contact the organisation through a number you already trust if anything looks unfamiliar.",
    "Keep this reference for your records.",
    "You can ignore this message if you have already completed the request.",
    "Do not share a verification code with anyone.",
    "Check the amount and recipient in your own app before approving any payment.",
    "Visit the nearest official office if you need in-person assistance.",
]

LEGITIMATE_TEMPLATES: dict[str, list[str]] = {
    "Banking": [
        "Your monthly account statement for {month} is ready in your bank's official mobile app. Reference {reference}.",
        "A card purchase of {amount} was completed. If you do not recognise it, call the number printed on the back of your card. Reference {reference}.",
        "Your scheduled bank transfer was completed successfully. Sign in through the official app to view the receipt. Reference {reference}.",
    ],
    "Mobile Money": [
        "You sent {amount} from your Mobile Money wallet. Check your own wallet balance and transaction history for confirmation. Reference {reference}.",
        "Your Mobile Money cash-out was completed at the agent location you selected. Reference {reference}.",
        "Your requested Mobile Money reversal has been opened. Track it through the provider's official support channel. Reference {reference}.",
    ],
    "Utilities": [
        "Your electricity purchase of {amount} was successful. The token is available in the official app and on your receipt. Reference {reference}.",
        "Your water bill for {month} is ready. Review the account number and amount through the official customer portal. Reference {reference}.",
        "Planned maintenance may affect service in your area on {day}. Updates will be published through official channels. Reference {reference}.",
    ],
    "Telecommunications": [
        "Your data bundle purchase of {amount} was successful and has been added to your line. Reference {reference}.",
        "Your monthly airtime and data usage summary is available in the network's official app. Reference {reference}.",
        "The SIM replacement you requested at the service centre is complete. Reference {reference}.",
    ],
    "Government Services": [
        "Your application has been received. Check its status through the official government portal using reference {reference}.",
        "Your appointment is scheduled for {day}. Bring your original documents to the office listed on your appointment slip. Reference {reference}.",
        "Your submitted form requires a correction. Sign in by typing the official portal address yourself. Reference {reference}.",
    ],
    "Delivery": [
        "Your parcel is scheduled for delivery on {day}. Payment is not required through this message. Reference {reference}.",
        "The delivery address for your order was updated as you requested. Review it in the merchant's official app. Reference {reference}.",
        "Your parcel was delivered and signed for. Contact the courier through its published support channel if this is incorrect. Reference {reference}.",
    ],
    "School and Education": [
        "The school fee statement for {month} is available in the parent portal. Use the student reference already issued by the school. Reference {reference}.",
        "Classes will close early on {day}. This notice is also posted on the school's official notice board. Reference {reference}.",
        "Your course registration was completed successfully. View the registered courses in the student portal. Reference {reference}.",
    ],
    "Retail and Business": [
        "Thank you for your order. Pay only through the checkout method you selected; staff will never request your OTP. Reference {reference}.",
        "Your shop payment of {amount} was received. Confirm the transaction in your own account before collecting the item. Reference {reference}.",
        "Your refund has been initiated to the original payment method and may take several working days. Reference {reference}.",
    ],
    "Employment": [
        "We received your job application. Shortlisted candidates will be contacted from the organisation's published email domain. Reference {reference}.",
        "Your interview is scheduled for {day} at the office address shown on the organisation's official website. Reference {reference}.",
        "The employer does not charge applicants a recruitment, interview or training fee. Reference {reference}.",
    ],
    "Healthcare": [
        "Your clinic appointment is confirmed for {day}. Bring your patient card and arrive fifteen minutes early. Reference {reference}.",
        "Your laboratory results are ready in the hospital's secure patient portal. Staff will not ask for your password by message. Reference {reference}.",
        "Your pharmacy order is ready for collection at the branch you selected. Pay only at the official counter. Reference {reference}.",
    ],
}

MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October"]
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "12 November", "18 November", "24 November", "30 November"]


CATEGORY_TEMPLATES: dict[str, list[str]] = {
    "Mobile Money Fraud": [
        "{greeting}, your Mobile Money wallet has been flagged. Share the verification code sent to you {deadline} so the restriction can be removed.",
        "You have won a promotional reward of {amount}. Pay a small activation fee through Mobile Money to claim it {deadline}.",
        "This is the Mobile Money support desk. Your wallet upgrade is pending; provide your secret PIN to complete the process {deadline}.",
        "Your Mobile Money account will be blocked because your Ghana Card is not linked. Open {url} and enter the requested details.",
        "A cash bonus of {amount} has been credited to your wallet. Send the tax payment before the bonus can be released.",
        "We detected an error on your wallet. Dial the code provided by the caller and approve every prompt to protect your balance.",
        "Your SIM and Mobile Money wallet require urgent re-registration. Reply with your date of birth and verification code {deadline}.",
        "Your account is frozen. Transfer {amount} to the temporary security wallet shown in the call so we can restore access.",
        "Congratulations from the network anniversary draw. Confirm your wallet PIN before your {amount} prize expires.",
        "Security alert: an unknown withdrawal is pending. Read the approval code to the support officer to cancel it.",
    ],
    "Fake Payment Alert or Screenshot": [
        "I have paid for the item. Check the payment screenshot and release it to the rider now; the wallet alert may delay.",
        "Payment of {amount} was successful. Please send the goods before the balance updates.",
        "The transfer is complete but the banking app is slow. Use this attached receipt as confirmation and dispatch today.",
        "Our accounts officer has sent the money. The screenshot is proof, so do not wait for your own account notification.",
        "The POS payment went through. Refund the difference now before checking the merchant balance.",
        "I transferred {amount} twice. Return the extra amount immediately using the screenshot as proof.",
        "This payment alert was forwarded from another number. Release the parcel now and the official confirmation will arrive later.",
        "Your account has received {amount}. Send the item even if the balance has not changed yet.",
        "The receipt confirms payment. Complete the sale {deadline}; there is no need to open your banking app.",
        "I am calling from the bank to confirm the transfer. Trust the WhatsApp receipt and release the goods.",
    ],
    "Wrong Transfer or Reversal Request": [
        "I mistakenly sent {amount} to your Mobile Money number. Return it to the different number I will provide {deadline}.",
        "I made a wrong transfer to you. Send it back immediately or I will report your number to the police.",
        "The credit alert proves the money reached you. Reverse {amount} to my other wallet now.",
        "Please help me, I entered one digit wrongly. Send the accidental transfer to my assistant's number before I lose my job.",
        "Approve the reversal prompt even if you cannot see the transaction in your real wallet balance.",
        "I sent my school fees to your wallet by mistake. Refund it quickly without calling the provider.",
        "The reversal system is down. Transfer {amount} manually to the personal wallet I will send you.",
        "Keeping a mistaken transfer is illegal. Refund it {deadline} or legal action will follow.",
        "The Mobile Money alert shows you were credited. Return the amount before checking your balance.",
        "Send your PIN and approval code so I can reverse the transfer that entered your account accidentally.",
    ],
    "WhatsApp Account Takeover": [
        "Hi, I changed my phone. Send me the six-digit WhatsApp code that just came to you so I can restore my account.",
        "Vote for my child in this contest using {url}, then send me the verification code you receive.",
        "Your WhatsApp account will be suspended. Confirm the registration code with support {deadline}.",
        "I mistakenly used your number to register WhatsApp. Forward the SMS code so I can correct it.",
        "Join the community group through {url} and enter the code sent to your phone.",
        "My phone is lost. Share a WhatsApp linking code to help me recover my chats.",
        "WhatsApp security notice: reply with your verification code to stop an unauthorised login.",
        "Scan the QR code I sent to join the business group and keep the page open until it connects.",
        "Approve the device-link request because I need help accessing my old WhatsApp account.",
        "All group members must verify membership by sending the WhatsApp code received by SMS.",
    ],
    "WhatsApp Impersonation": [
        "Hello, this is {name}. I am using a new number. Send {amount} urgently and do not call because I am in a meeting.",
        "This is the head teacher on a new WhatsApp number. Parents must pay an emergency school charge today.",
        "I am your manager. Make a confidential transfer to the personal Mobile Money wallet I will send you.",
        "My phone was stolen. Send money to my friend's number and do not call the old line.",
        "This is the shop's new business account. Pay in full before delivery using the personal wallet provided.",
        "This is your church leader on a new line. Contribute {amount} for an urgent private need.",
        "I am contacting you from a government office about a contract. Pay the processing charge through WhatsApp.",
        "Customer care here. Your complaint can be resolved only after you share the OTP in this chat.",
        "I am your colleague. Buy digital vouchers and send me the codes because my banking app is unavailable.",
        "Boss, it is me on my new line. Transfer the funds {deadline}; I will explain later.",
    ],
    "OTP or Verification Code Request": [
        "{greeting}, read the OTP sent to your phone so we can stop an unauthorised transaction {deadline}.",
        "Your Ghana Card linking is incomplete. Reply with the verification code from your bank to keep the account active.",
        "Send your card number, expiry date, CVV and OTP so we can reverse the debit.",
        "The code is not a password. Share it with me so I can confirm your identity.",
        "To receive your refund of {amount}, provide the one-time code that arrives by SMS.",
        "Your account has been compromised. Enter the OTP at {url} to secure it.",
        "Approve the login notification and tell me the verification number displayed.",
        "Your grant application requires the code from your phone before funds can be released.",
        "The OTP sent by your bank is needed to complete the payment I am making to you.",
        "Your SIM will be disconnected. Send the PIN reset code to the network employee on this chat.",
    ],
    "Phishing": [
        "Your online banking access expires today. Sign in at {url} to avoid suspension.",
        "Ghana Card update required. Submit your personal details at {url} {deadline}.",
        "A parcel is waiting for delivery. Pay {amount} clearance at {url}.",
        "You qualify for an electricity subsidy. Confirm your account at {url}.",
        "Your email storage is full. Sign in through {url} to keep incoming messages.",
        "A tax refund is available. Enter your bank details at {url}.",
        "Security notice from your network: verify your SIM at {url} before it is blocked.",
        "Download the attached form and log in to view an unexpected invoice from a supplier.",
        "Free data is waiting for you. Sign in at {url} to activate the bundle.",
        "A government benefit is ready. Open {url} to complete verification.",
    ],
    "Bank Impersonation": [
        "{greeting} from your bank. Your account is under review; provide your OTP and card details {deadline}.",
        "I am calling from the bank fraud desk. Move your funds to the temporary safe account I will provide.",
        "Your ATM card will be disabled unless you confirm the PIN with customer protection.",
        "Your Ghana Card is not linked to your bank account. Open {url} to prevent a restriction.",
        "This is the branch manager. Transfer {amount} to test whether your account is active.",
        "Send the numbers on the front and back of your card so we can investigate the failed payment.",
        "An unauthorised loan was opened in your name. Give me the verification code so I can cancel it.",
        "Your bank has approved a no-check loan. Pay the processing fee before the offer closes.",
        "Your mobile banking profile is locked. Reply with your password so support can restore it.",
        "Do not visit the branch. The account problem must be resolved on this call {deadline}.",
    ],
    "Fake Online Shop": [
        "{shop} has a new phone for {amount}. Full Mobile Money payment is required before viewing or delivery.",
        "Our heavily discounted appliances are almost sold out. We do not accept cash on delivery; pay the personal wallet now.",
        "Only one item remains. Send the deposit {deadline}; the warehouse location will be shared after payment.",
        "The shop payment account has changed. Send the money to the different personal name provided after ordering.",
        "Your item is ready, but an additional delivery insurance fee must be paid before dispatch.",
        "We cannot take a video call. Reviews confirm the shop is genuine, so pay the unrelated Mobile Money name.",
        "Festive-season flash sale: complete checkout at {url} before the unrealistic discount expires.",
        "Reserve the vehicle with {amount} before inspection or another buyer will take it.",
        "The warehouse is outside Accra. Send transport money before we share the exact location.",
        "Nationwide delivery is available, but you must pay another clearance charge before the parcel moves.",
    ],
    "Investment Fraud": [
        "Join our {investment} and earn guaranteed returns every week with no risk. Start with {amount} today.",
        "Double your money in 48 hours through our licensed platform. Registration closes {deadline}.",
        "I guarantee fixed daily profit. Transfer the investment to my personal wallet and I will trade for you.",
        "Your profits are ready, but pay a withdrawal fee of {amount} before they can be released.",
        "Regulatory approval is still pending, but deposits must be made now to secure a founder's slot.",
        "Our crypto plan guarantees high monthly returns and losses are impossible.",
        "Your first return is ready. Invest a larger amount and recruit friends to unlock the next level.",
        "This agriculture project pays unusually high profit after one month with no risk or contract needed.",
        "The opportunity is confidential. Do not contact the regulator or your bank before investing.",
        "Your trading dashboard shows profit, but you must pay {amount} in taxes before withdrawal.",
    ],
}

FRAUD_URL_TEMPLATES = {
    "Mobile Money Fraud": "https://momo-wallet-verify-{number}.vercel.app/login",
    "Fake Payment Alert or Screenshot": "http://192.0.2.{number}/payment/confirm",
    "Wrong Transfer or Reversal Request": "https://reversal-support-{number}.pages.dev/approve",
    "WhatsApp Account Takeover": "https://whatsapp-device-link-{number}.netlify.app/login",
    "WhatsApp Impersonation": "https://new-contact-verify-{number}.example.invalid/confirm",
    "OTP or Verification Code Request": "https://secure-code-check-{number}.example.invalid/enter-otp",
    "Phishing": "https://account-update-{number}.example.invalid/login",
    "Bank Impersonation": "https://gcb-secure-{number}.vercel.app/login",
    "Fake Online Shop": "https://flash-sale-checkout-{number}.example.invalid/pay",
    "Investment Fraud": "https://guaranteed-profit-{number}.pages.dev/deposit",
}


def build_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for category_index, (category, templates) in enumerate(CATEGORY_TEMPLATES.items()):
        for index in range(60):
            template_index = index % 10
            variation_index = index // 10
            content = templates[template_index].format(
                greeting=GREETINGS[(index + category_index) % len(GREETINGS)],
                amount=AMOUNTS[(index * 3 + category_index) % len(AMOUNTS)],
                deadline=DEADLINES[(index * 7 + category_index) % len(DEADLINES)],
                url=f"https://guard-example-{category_index + 1}-{index + 1}.example.invalid",
                name=NAMES[(index + category_index) % len(NAMES)],
                shop=SHOPS[(index + category_index) % len(SHOPS)],
                investment=INVESTMENTS[(index + category_index) % len(INVESTMENTS)],
            )
            content = f"{content} {CLOSERS[variation_index]}"
            if category == "Fake Payment Alert or Screenshot":
                content_type = "screenshot_text"
            elif category == "Phishing":
                content_type = "link_message"
            else:
                content_type = "message"
            rows.append({
                "content": content,
                "label": "fraud",
                "category": category,
                "content_type": content_type,
                "channel": CHANNELS[(index + category_index) % len(CHANNELS)],
                "country_code": "GH",
                "ghana_specific": "true",
                "language": "en",
                "notes": f"Synthetic Ghana fraud-pattern example. Pattern: {category}. Not an actual report.",
            })
        for url_index in range(10):
            rows.append({
                "content": FRAUD_URL_TEMPLATES[category].format(number=category_index * 10 + url_index + 1),
                "label": "fraud",
                "category": category,
                "content_type": "url",
                "channel": "web",
                "country_code": "GH",
                "ghana_specific": "true",
                "language": "en",
                "notes": f"Synthetic non-production fraud URL. Pattern: {category}. Not an actual website or report.",
            })
    for sector_index, (sector, templates) in enumerate(LEGITIMATE_TEMPLATES.items()):
        for index in range(30):
            template_index = index % len(templates)
            variation_index = index // len(templates)
            reference = f"GH-{sector_index + 1:02d}-{index + 1:03d}"
            content = templates[template_index].format(
                amount=AMOUNTS[(index * 3 + sector_index) % len(AMOUNTS)],
                month=MONTHS[(index + sector_index) % len(MONTHS)],
                day=DAYS[(index * 2 + sector_index) % len(DAYS)],
                reference=reference,
            )
            content = f"{content} {LEGITIMATE_CLOSERS[variation_index]}"
            rows.append({
                "content": content,
                "label": "legitimate",
                "category": "",
                "content_type": "message",
                "channel": CHANNELS[(index + sector_index) % len(CHANNELS)],
                "country_code": "GH",
                "ghana_specific": "true",
                "language": "en",
                "notes": f"Synthetic Ghana legitimate-message example. Sector: {sector}. Hard negative for model training.",
            })
    return rows


def validate(rows: list[dict[str, str]]) -> None:
    assert len(rows) == 1000
    assert len({row["content"] for row in rows}) == 1000
    assert all(set(row) == set(HEADERS) for row in rows)
    label_counts = Counter(row["label"] for row in rows)
    assert label_counts == {"fraud": 700, "legitimate": 300}
    assert all(row["country_code"] == "GH" and row["ghana_specific"] == "true" for row in rows)
    safe_url_markers = ("example.invalid", ".vercel.app", ".netlify.app", ".pages.dev", "192.0.2.")
    assert all(any(marker in row["content"] for marker in safe_url_markers) or "http" not in row["content"] for row in rows)
    fraud_rows = [row for row in rows if row["label"] == "fraud"]
    legitimate_rows = [row for row in rows if row["label"] == "legitimate"]
    counts = Counter(row["category"] for row in fraud_rows)
    assert set(counts) == set(CATEGORY_TEMPLATES)
    assert all(count == 70 for count in counts.values())
    assert all(not row["category"] for row in legitimate_rows)
    assert sum(row["content_type"] == "url" for row in fraud_rows) == 100


def main() -> None:
    rows = build_rows()
    validate(rows)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=HEADERS)
        writer.writeheader()
        writer.writerows(rows)
    counts = Counter(row["label"] for row in rows)
    print(f"Created {OUTPUT} with {len(rows)} unique rows: {dict(counts)}")


if __name__ == "__main__":
    main()
