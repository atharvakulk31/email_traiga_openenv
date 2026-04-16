"""
generate_emails.py
Generates 1000 realistic synthetic training emails
and saves to backend/data/emails_1000.json
"""

import json, random, os
from itertools import product

random.seed(42)

# ── Sender name pool ──────────────────────────────────────────────────────────
FIRST = ["James","Sarah","Michael","Emma","David","Lisa","Robert","Anna","Chris",
         "Priya","Marcus","Sofia","Nathan","Rachel","Carlos","Nina","Oliver","Amy",
         "Derek","Jessica","Thomas","Linda","Alex","Hannah","Ben","Vivian","Paul",
         "Mary","Greg","Ines","Eli","Amara","Nathaniel","Monica","Kevin","Fatima",
         "Ryan","Claire","Aaron","Zoe","Tyler","Leila","Connor","Aisha","Jordan",
         "Maya","Dylan","Chloe","Brandon","Layla"]
LAST  = ["Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis",
         "Wilson","Moore","Taylor","Anderson","Thomas","Jackson","White","Harris",
         "Martin","Thompson","Young","Hall","Walker","Allen","King","Scott","Green",
         "Baker","Adams","Nelson","Carter","Mitchell","Perez","Roberts","Turner",
         "Phillips","Campbell","Parker","Evans","Edwards","Collins","Stewart",
         "Nguyen","Patel","Kumar","Singh","Okafor","Mensah","Andersen","Müller"]
DOMAINS = ["gmail.com","outlook.com","techcorp.io","cloudworks.net","devteam.co",
           "enterprise.org","startup.io","consulting.biz","agency.com","labs.tech",
           "solutions.net","systems.dev","ventures.co","group.com","media.io"]

def rand_sender():
    f, l = random.choice(FIRST), random.choice(LAST)
    return f"{f.lower()}.{l.lower()}@{random.choice(DOMAINS)}"

# ── Templates per (category, priority) ───────────────────────────────────────

TEMPLATES = {

    # ══ ACCOUNT ══════════════════════════════════════════════════════════════
    ("Account","High"): [
        ("Cannot access my account - urgent deadline today",
         "I have been locked out of my account since {time} and I cannot access any of my work. "
         "I have a {deadline} deadline in {hours} hours. I tried resetting my password {n} times "
         "but keep getting an error. Please escalate this immediately and help me regain access."),
        ("Account locked after failed login attempts - payroll due",
         "My account is locked following {n} failed login attempts this morning. This is critical "
         "because {event} is due today and I need access immediately. I have tried the automated "
         "recovery but it is not working. Please unlock my account urgently."),
        ("Two-factor authentication broken - completely locked out",
         "Since {time}, my 2FA codes are being rejected even though my authenticator app is "
         "generating them correctly. I cannot log in at all. I have synced my phone's clock and "
         "regenerated codes but nothing works. This is a serious issue - please help immediately."),
        ("Password reset link expires before I can click it",
         "Every password reset link I receive expires within seconds. I have been trying for "
         "{hours} hours and am now fully locked out. My work has completely stopped. "
         "Please investigate this urgently and help me reset my password manually."),
        ("Account suspended without notice - losing business",
         "My account was suspended without any prior warning or email notification. I was in the "
         "middle of {task} when I was suddenly logged out and now cannot access anything. "
         "I have an important {event} in {hours} hours. Please restore access immediately."),
    ],
    ("Account","Medium"): [
        ("Request to update account email address",
         "I recently changed my professional email and would like to update my account from "
         "{old_email} to {new_email}. Please let me know if you need any verification. I "
         "appreciate your help with this straightforward change."),
        ("Changing account username",
         "I would like to change my username on the platform. My current username is "
         "{old_user} and I would like it changed to {new_user}. Please let me know the "
         "process for doing this and if there are any restrictions I should know about."),
        ("Update profile information",
         "I need to update several fields in my account profile including my job title, "
         "company name, and phone number. I tried updating through account settings but "
         "the changes are not saving. Could you please help me update this information?"),
        ("Merge two accounts under same email",
         "I have two accounts on your platform that I created at different times with "
         "different email addresses. I would like to merge them into a single account "
         "and keep all my data. Is this possible and how would I go about doing it?"),
        ("Change password - forgot current one",
         "I would like to change my account password but I have forgotten my current "
         "password. The automated reset process is not working for me. Could you please "
         "help me reset it manually after verifying my identity?"),
    ],
    ("Account","Low"): [
        ("How to update notification preferences",
         "I would like to change my email notification settings. I am receiving too many "
         "notifications and would like to only receive the most important ones. "
         "Could you guide me on where to find these settings in my account?"),
        ("Question about account data export",
         "I would like to know how I can export all the data associated with my account. "
         "I want to keep a local backup of my content. Is there an export feature available "
         "and what formats are supported?"),
        ("How to delete my account",
         "I would like to permanently delete my account and all associated data. "
         "Could you please guide me through the account deletion process? "
         "I want to make sure all my personal data is also removed."),
        ("Setting up account for a new team member",
         "I would like to invite a new colleague to our team account. Could you walk me "
         "through the invitation process? I also want to understand what permissions "
         "a new member gets by default."),
    ],

    # ══ BILLING REFUND ═══════════════════════════════════════════════════════
    ("Billing Refund","High"): [
        ("Unauthorized charge after cancellation - demand refund",
         "I cancelled my subscription on {date} and received a cancellation confirmation, "
         "yet I was still charged {amount} on {charge_date}. This is completely unauthorized. "
         "I am demanding an immediate refund and will file a chargeback with my bank if "
         "I do not receive confirmation within 24 hours."),
        ("Duplicate charge on my account - urgent",
         "I was charged twice for my subscription this month - both charges of {amount} "
         "appeared on {date}. I only have one active subscription. I need an immediate "
         "refund for the duplicate charge. Please review my billing history and process "
         "the refund as quickly as possible."),
        ("Charged wrong amount - significant overcharge",
         "My invoice shows {amount} but I should have been billed {correct_amount} "
         "based on my current plan. This is an overcharge of {diff} and I need it corrected "
         "immediately. I have attached my contract showing the agreed price."),
        ("Refund for damaged product - Order #{order}",
         "My order #{order} arrived damaged. The {product} was broken on arrival and "
         "the packaging was clearly tampered with. I have photos of the damage. "
         "I want a full refund of {amount} to my original payment method immediately."),
        ("Fraudulent charges on my account",
         "I noticed {n} unauthorized charges totaling {amount} on my account that I "
         "did not make. These charges appeared between {date1} and {date2}. I believe "
         "my account may have been compromised. Please refund these immediately and "
         "secure my account."),
    ],
    ("Billing Refund","Medium"): [
        ("Invoice amount does not match agreed price",
         "My invoice for this month shows {amount} but our contract states {correct_amount}. "
         "I have attached both documents. Please review and issue a corrected invoice "
         "or refund the difference of {diff}."),
        ("Overcharged for plan I did not choose",
         "I signed up for the {plan} plan at {price}/month but was charged {wrong_price}. "
         "I never upgraded my plan. Please correct this billing error and refund the "
         "overpayment."),
        ("Request partial refund for unused subscription days",
         "I cancelled my account on {date} with {days} days remaining in my billing cycle. "
         "I would like a prorated refund for the unused period. Please confirm the refund "
         "amount and when I can expect it."),
        ("VAT incorrectly applied to my invoice",
         "VAT has been applied to my invoice but as a business registered in {country}, "
         "I am VAT exempt. Please issue a corrected invoice without VAT and refund the "
         "incorrectly charged tax amount."),
        ("Inquiry about bulk discount - enterprise plan",
         "We are evaluating your platform for {n} seats. I would like to know what bulk "
         "pricing discounts are available for organizations of our size. A comparison "
         "of enterprise vs standard features would also be helpful."),
    ],
    ("Billing Refund","Low"): [
        ("Switching from monthly to annual billing",
         "I would like to switch from monthly to annual billing to take advantage of your "
         "discount. Could you confirm the annual rate and whether any prorated credit "
         "will be applied for my current month?"),
        ("Question about billing cycle date",
         "My billing cycle currently runs from the {date}. I would like to change it to "
         "the 1st of each month. Is this possible and would it affect my current plan?"),
        ("Request copy of old invoice",
         "I need a copy of my invoice from {month} {year} for my company expense records. "
         "Could you please resend it or let me know where I can download it?"),
        ("Updating billing address",
         "Our company recently moved and I need to update the billing address on my account. "
         "The new address is {address}. Please let me know how to update this."),
        ("Question about free trial to paid conversion",
         "My free trial ends on {date} and I would like to know exactly what happens "
         "to my data and account when it converts to paid. What is the first charge date "
         "and amount?"),
    ],

    # ══ FEATURE REQUEST ═══════════════════════════════════════════════════════
    ("Feature Request","Medium"): [
        ("API rate limit too low for our use case",
         "We are integrating your API and consistently hitting the rate limit of "
         "{limit} requests/minute. Our use case requires {needed} requests/minute "
         "during peak processing. Could you offer a higher tier plan or batch endpoint?"),
        ("Request for Zapier or Make integration",
         "We use Zapier extensively to automate our workflows and would love to see "
         "your platform integrated with it. This would allow us to connect {platform} "
         "with hundreds of other tools without custom development."),
        ("Bulk import feature for data migration",
         "We are migrating from {old_tool} and have {n} records to import. A bulk "
         "import feature with CSV or JSON support would make this much easier. "
         "Is this on your roadmap?"),
        ("Request for custom webhook events",
         "We need webhooks to fire on specific events like {event1} and {event2}. "
         "Your current webhook support is limited to basic events. Custom webhook "
         "triggers would greatly improve our integration capabilities."),
        ("Multi-language support needed",
         "Our team operates in {n} countries and we need the platform to support "
         "{language1} and {language2} in addition to English. Is internationalization "
         "on your product roadmap?"),
    ],
    ("Feature Request","Low"): [
        ("Feature suggestion: dark mode",
         "I spend long hours in your app and would love a dark mode option. It would "
         "reduce eye strain significantly especially during late night work sessions. "
         "Many competing apps already have this - hope it makes your roadmap!"),
        ("Feature request: keyboard shortcuts",
         "As a power user I would love keyboard shortcuts for common actions. "
         "Shortcuts for {action1}, {action2}, and {action3} would speed up my "
         "workflow dramatically. Any plans to add them?"),
        ("Suggestion: CSV export for reports",
         "The reporting section is great but having a one-click CSV export would "
         "save our team hours each week. We currently copy data manually into "
         "spreadsheets. This seems like a relatively simple but very useful addition."),
        ("Feature idea: calendar view for tasks",
         "I would love to see a calendar view in the task manager. Currently everything "
         "is in list format which makes it hard to visualize deadlines. A monthly "
         "or weekly calendar view would be perfect."),
        ("Request: Slack integration",
         "Our whole team communicates through Slack. It would be amazing to receive "
         "notifications and updates from your platform directly in our Slack channels. "
         "Many other tools we use already have Slack integrations."),
        ("Suggestion: customizable dashboard widgets",
         "I would love to be able to rearrange and customize the widgets on my dashboard. "
         "Being able to choose which metrics are most visible would help me focus on "
         "what matters most. Even a basic drag-and-drop would be great."),
        ("Feature request: mobile app",
         "I often need to check things on the go but your platform is not optimized "
         "for mobile. A native iOS and Android app would be incredibly valuable for "
         "remote and field workers like myself."),
        ("Idea: custom tags and labels",
         "I would find it very useful to create custom tags and labels to organize "
         "my content. Right now the categorization options are fixed and do not "
         "match how my team thinks about our work."),
    ],

    # ══ TECHNICAL SUPPORT ════════════════════════════════════════════════════
    ("Technical Support","High"): [
        ("App completely down - critical demo in {hours} hours",
         "Your application is completely unresponsive for our entire team. We have "
         "tried multiple browsers, cleared cache, and tested from different networks. "
         "This is a critical emergency as we have a {event} in {hours} hours. "
         "Please respond immediately with an ETA for resolution."),
        ("500 server error on login page",
         "Since {time}, the login page returns a 500 Internal Server Error for all "
         "users on our team across different networks. We cannot log in at all and "
         "all work has stopped. Please investigate immediately and provide an ETA."),
        ("Data loss after update - urgent recovery needed",
         "After your latest update deployed at {time}, approximately {n} records "
         "in our {data_type} are missing. This data is critical for {business_purpose}. "
         "Please restore from backup immediately - we cannot operate without it."),
        ("Integration with {service} completely broken",
         "Our {service} integration stopped working at {time} and is causing "
         "failures in our automated pipeline. {n} jobs have failed since then. "
         "Please treat this as critical - we process {volume} per day through this."),
        ("App crashes when uploading files - blocking all work",
         "Every file upload over {size}MB causes the app to crash completely. "
         "This happens on all devices and browsers. Most of our files are {size2}MB. "
         "This is completely blocking our team's work. Please fix urgently."),
    ],
    ("Technical Support","Medium"): [
        ("Notification emails landing in spam",
         "For the past {n} weeks, all notification emails from your platform go to spam. "
         "I have added your domain to safe senders but it persists. My IT team checked "
         "our mail filters and found no rules causing this. Please advise."),
        ("Dashboard charts not loading correctly",
         "The charts on my dashboard are either blank or showing incorrect data. "
         "I have tried refreshing and clearing my cache. The issue started after "
         "your recent update on {date}. Is this a known bug?"),
        ("Export feature generating corrupted files",
         "When I export my data as {format}, the downloaded file is corrupted and "
         "cannot be opened. I have tried multiple times and with different date ranges. "
         "The issue has been consistent for the past {n} days."),
        ("Slow performance affecting productivity",
         "Your platform has been extremely slow for the past {n} days. Pages take "
         "{seconds} seconds to load and sometimes time out completely. My internet "
         "connection is fine - this appears to be a server-side issue."),
        ("Third-party integration returning errors",
         "The {service} integration is returning {error_code} errors intermittently. "
         "This affects approximately {percent}% of our automated tasks. Is there a "
         "known issue with the {service} connector?"),
    ],
    ("Technical Support","Low"): [
        ("Minor bug in date formatting",
         "I noticed that dates in the {section} section are displaying in MM/DD/YYYY "
         "format instead of DD/MM/YYYY as set in my account preferences. This is a "
         "minor issue but makes dates confusing for our international team."),
        ("Search results not matching expected content",
         "When I search for '{query}', the results do not include some content that "
         "clearly contains that word. The search seems to miss items created before "
         "{date}. Is there a known indexing delay or issue?"),
        ("UI alignment issue on mobile browser",
         "On mobile browsers, the sidebar menu overlaps the main content area. "
         "This makes it hard to read. It happens on both iOS Safari and Android Chrome. "
         "Your desktop experience is great though!"),
        ("Email template has formatting issue",
         "The automatic emails sent when {event} happens have a broken layout - "
         "the images are not displaying and the text appears unstyled. "
         "This only started happening recently after what I assume was an update."),
    ],
}

# ── Fill-in variable pools ────────────────────────────────────────────────────
VARS = {
    "time"    : ["this morning","earlier today","last night","yesterday afternoon",
                 "2:30 PM","around 9 AM","just now","an hour ago"],
    "deadline": ["client presentation","board meeting","project submission",
                 "investor demo","product launch","audit report"],
    "hours"   : ["2","3","4","1","6","24"],
    "n"       : ["2","3","4","5","10","several","multiple"],
    "event"   : ["payroll processing","the quarterly audit","a client demo",
                 "our product launch","a board presentation","team standup"],
    "task"    : ["processing invoices","running reports","updating records",
                 "completing a client order","submitting the audit"],
    "old_email": ["john.doe@oldcompany.com","user@previous.org","me@legacy.net"],
    "new_email": ["john.doe@newcompany.com","user@newdomain.io","me@current.co"],
    "old_user" : ["john_doe_2020","user123","my_old_handle"],
    "new_user" : ["johndoe","newusername","my_new_handle"],
    "date"    : ["February 28th","March 1st","last Tuesday","the 15th","January 31st"],
    "date1"   : ["March 1st","February 10th","last Monday"],
    "date2"   : ["March 15th","February 28th","last Friday"],
    "charge_date": ["March 10th","February 15th","last Wednesday"],
    "amount"  : ["$29","$49","$79","$99","$149","$199","$299"],
    "correct_amount": ["$19","$29","$49","$69","$99"],
    "diff"    : ["$10","$20","$30","$50","$100"],
    "order"   : ["847291","123456","789012","456789","234567"],
    "product" : ["laptop stand","monitor","keyboard","headset","webcam"],
    "limit"   : ["100","200","500","1000"],
    "needed"  : ["500","1000","2000","5000"],
    "platform": ["Salesforce","HubSpot","Notion","Airtable","Jira"],
    "old_tool": ["Trello","Asana","Monday.com","Basecamp","Jira"],
    "event1"  : ["user signup","payment completed","item deleted"],
    "event2"  : ["status changed","file uploaded","comment added"],
    "language1": ["Spanish","French","German","Japanese","Portuguese"],
    "language2": ["Arabic","Chinese","Hindi","Italian","Dutch"],
    "action1" : ["creating new items","saving","searching"],
    "action2" : ["navigating sections","opening settings","closing dialogs"],
    "action3" : ["refreshing data","exporting","bulk selecting"],
    "service" : ["Salesforce","HubSpot","Slack","Stripe","QuickBooks","Zapier"],
    "volume"  : ["10,000 records","500 transactions","1,000 emails","50 reports"],
    "size"    : ["10","15","20","25","50"],
    "size2"   : ["15-50","20-100","10-30","25-75"],
    "data_type": ["customer records","project files","invoice data","user accounts"],
    "business_purpose": ["invoicing clients","processing payroll","generating reports"],
    "seconds" : ["10-15","20-30","5-10","30-60"],
    "percent" : ["20","30","40","50"],
    "section" : ["reports","invoices","the dashboard","calendar","notifications"],
    "query"   : ["password reset","invoice","account update","feature request"],
    "format"  : ["CSV","Excel","PDF","JSON"],
    "error_code": ["403","500","422","503","timeout"],
    "address" : ["880 Congress Ave, Floor 5, Austin TX 78701",
                 "123 Main St, Suite 100, San Francisco CA 94105"],
    "plan"    : ["Basic","Starter","Professional","Standard"],
    "price"   : ["$19","$29","$49","$69"],
    "wrong_price": ["$79","$99","$149","$199"],
    "days"    : ["10","15","20","25"],
    "month"   : ["January","February","March","April","May","June"],
    "year"    : ["2024","2023"],
    "country" : ["Germany","France","UK","Netherlands","Ireland"],
    "correct_amount": ["$19","$29","$49","$69"],
}

def fill(template: str) -> str:
    """Replace {var} placeholders with random values."""
    import re
    def replacer(m):
        key = m.group(1)
        return random.choice(VARS.get(key, [f"[{key}]"]))
    return re.sub(r"\{(\w+)\}", replacer, template)

# ── Generate emails ───────────────────────────────────────────────────────────
CATEGORY_MAP = {
    "Account":          [("Account","High"), ("Account","Medium"), ("Account","Low")],
    "Billing Refund":   [("Billing Refund","High"), ("Billing Refund","Medium"), ("Billing Refund","Low")],
    "Feature Request":  [("Feature Request","Medium"), ("Feature Request","Low")],
    "Technical Support":[("Technical Support","High"), ("Technical Support","Medium"), ("Technical Support","Low")],
}

# Targets per (category, priority)
TARGETS = {
    ("Account","High"):           80,
    ("Account","Medium"):         70,
    ("Account","Low"):            50,
    ("Billing Refund","High"):    80,
    ("Billing Refund","Medium"):  70,
    ("Billing Refund","Low"):     50,
    ("Feature Request","Medium"): 80,
    ("Feature Request","Low"):   120,
    ("Technical Support","High"): 100,
    ("Technical Support","Medium"):80,
    ("Technical Support","Low"):   70,
}
# Total = 850; pad to 1000 by duplicating with variation

emails = []
eid = 1

for (cat, pri), count in TARGETS.items():
    templates = TEMPLATES.get((cat, pri), [])
    if not templates:
        continue
    for i in range(count):
        subj_tmpl, body_tmpl = random.choice(templates)
        subject = fill(subj_tmpl)
        body    = fill(body_tmpl)
        emails.append({
            "id"       : f"email_{eid:04d}",
            "subject"  : subject,
            "sender"   : rand_sender(),
            "body"     : body,
            "category" : cat,
            "priority" : pri,
            "timestamp": f"2024-0{random.randint(1,9)}-{random.randint(10,28):02d}T"
                         f"{random.randint(8,18):02d}:{random.randint(0,59):02d}:00Z",
        })
        eid += 1

# Pad to 1000
while len(emails) < 1000:
    (cat, pri) = random.choice(list(TARGETS.keys()))
    templates  = TEMPLATES.get((cat, pri), [])
    if not templates:
        continue
    subj_tmpl, body_tmpl = random.choice(templates)
    emails.append({
        "id"       : f"email_{eid:04d}",
        "subject"  : fill(subj_tmpl),
        "sender"   : rand_sender(),
        "body"     : fill(body_tmpl),
        "category" : cat,
        "priority" : pri,
        "timestamp": f"2024-0{random.randint(1,9)}-{random.randint(10,28):02d}T"
                     f"{random.randint(8,18):02d}:{random.randint(0,59):02d}:00Z",
    })
    eid += 1

random.shuffle(emails)
# Re-assign IDs after shuffle
for i, e in enumerate(emails):
    e["id"] = f"email_{i+1:04d}"

OUT_PATH = os.path.join("backend", "data", "emails_1000.json")
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(emails, f, indent=2, ensure_ascii=False)

# Print distribution
from collections import Counter
cat_dist = Counter(e["category"] for e in emails)
pri_dist = Counter(e["priority"] for e in emails)
print(f"Generated {len(emails)} emails -> {OUT_PATH}")
print(f"Category distribution : {dict(cat_dist)}")
print(f"Priority distribution : {dict(pri_dist)}")
