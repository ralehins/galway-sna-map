"""
Scrape EducationPosts.ie for Galway SNA vacancies with Roll Numbers.
Designed to run locally (with getpass) or in GitHub Actions (with env vars).
Outputs vacancies.json for the map dashboard.
"""
import requests
import re
import json
import os
import sys
from html import unescape
from datetime import datetime

# Configuration
LISTING_URL = "https://www.educationposts.ie/posts/primary_level"
LISTING_PARAMS = {
    "sb": "application_closing_date",
    "sd": "0",
    "p": "1",
    "cy": "7",   # Galway
    "pd": "",
    "vc": "13",  # SNA
    "ptl": "",
    "ga": "0",
}
LOGIN_URL = "https://www.educationposts.ie/auth/login"
POST_VIEW_URL = "https://www.educationposts.ie/post/view/{post_id}"


def get_credentials():
    """Get credentials from env vars (CI) or prompt (local)."""
    email = os.environ.get("EP_EMAIL", "")
    password = os.environ.get("EP_PASSWORD", "")
    if not email or not password:
        import getpass
        email = input("EducationPosts.ie email: ")
        password = getpass.getpass("EducationPosts.ie password: ")
    return email, password


def login(session, email, password):
    """Authenticate and return True if successful."""
    session.get(LOGIN_URL, timeout=15)
    data = {
        "username": email,
        "password": password,
        "returnTo": "/posts/primary_level?cy=7&vc=13",
        "forceUser": "",
    }
    r = session.post(LOGIN_URL, data=data, timeout=15, allow_redirects=True)
    if "/auth/login" in r.url:
        print("ERROR: Login failed. Check credentials.")
        return False
    print("Logged in successfully.")
    return True


def get_vacancy_listing(session):
    """Fetch the listing page and extract vacancy IDs and basic info."""
    r = session.get(LISTING_URL, params=LISTING_PARAMS, timeout=15)
    
    rows = re.findall(
        r'href="/post/view/(\d+)"[^>]*title="View Advert Detail"[^>]*>([^<]+)<',
        r.text
    )
    
    from collections import OrderedDict
    seen_ids = OrderedDict()
    for post_id, text in rows:
        text = text.strip()
        if text == post_id:
            continue
        if post_id not in seen_ids:
            seen_ids[post_id] = []
        seen_ids[post_id].append(text)
    
    vacancies = []
    for post_id, texts in seen_ids.items():
        vacancy = {
            "post_id": post_id,
            "school_name": unescape(texts[0]) if len(texts) > 0 else "",
            "post_title": texts[1] if len(texts) > 1 else "",
            "post_type": texts[2] if len(texts) > 2 else "",
            "county": texts[3] if len(texts) > 3 else "Galway",
        }
        vacancies.append(vacancy)
    
    # Extract closing dates
    dates = re.findall(r'(\d{2}/\d{2}/\d{4})', r.text)
    for i, v in enumerate(vacancies):
        if i < len(dates):
            v["closing_date"] = dates[i]
    
    print(f"Found {len(vacancies)} vacancies on listing page.")
    return vacancies


def get_vacancy_detail(session, post_id):
    """Fetch a single vacancy detail page and extract Roll Number."""
    url = POST_VIEW_URL.format(post_id=post_id)
    r = session.get(url, timeout=15)
    
    if "/auth/login" in r.url:
        print(f"  WARNING: Session expired for post {post_id}")
        return None
    
    roll_patterns = [
        r'Roll\s*(?:Number|No\.?)\s*[:：]?\s*(\d{5}[A-Z])',
        r'Roll\s*(?:Number|No\.?)\s*[:：]?\s*([A-Z0-9]{5,7})',
        r'roll.number[^>]*>([^<]+)<',
        r'Roll No[^:]*:\s*(\S+)',
    ]
    
    roll_number = None
    for pat in roll_patterns:
        match = re.search(pat, r.text, re.IGNORECASE)
        if match:
            roll_number = match.group(1).strip()
            break
    
    if not roll_number:
        idx = r.text.lower().find('roll')
        if idx > 0:
            chunk = r.text[idx:idx+200]
            match = re.search(r'(\d{5}[A-Za-z])', chunk)
            if match:
                roll_number = match.group(1).upper()
    
    return {"roll_number": roll_number}


def main():
    email, password = get_credentials()
    
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })
    
    if not login(session, email, password):
        sys.exit(1)
    
    vacancies = get_vacancy_listing(session)
    
    for v in vacancies:
        print(f"  Fetching {v['post_id']}: {v['school_name']}...")
        detail = get_vacancy_detail(session, v["post_id"])
        if detail:
            v["roll_number"] = detail["roll_number"]
            if detail["roll_number"]:
                print(f"    Roll: {detail['roll_number']}")
            else:
                print(f"    No Roll Number found")
    
    output = {
        "scraped_at": datetime.utcnow().isoformat() + "Z",
        "county": "Galway",
        "category": "SNA",
        "vacancies": vacancies,
    }
    
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vacancies.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\nSaved {len(vacancies)} vacancies to vacancies.json")
    matched = sum(1 for v in vacancies if v.get("roll_number"))
    print(f"Roll Numbers found: {matched}/{len(vacancies)}")


if __name__ == "__main__":
    main()
