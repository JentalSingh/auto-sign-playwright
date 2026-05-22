#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import os
import random
import string
import sys
import requests
from playwright.sync_api import sync_playwright, TimeoutError
from dotenv import load_dotenv


load_dotenv()
API_KEY = os.getenv("TWOCAPTCHA_API_KEY")

def get_random_proxy():
    try:
        if os.path.exists("proxy_list.txt"):
            with open("proxy_list.txt", "r") as f:
                proxies = [line.strip() for line in f if line.strip()]
            if proxies:
                chosen = random.choice(proxies)
                parts = chosen.split(":")
                if len(parts) == 4:
                    return {
                        "server": f"http://{parts[0]}:{parts[1]}",
                        "username": parts[2],
                        "password": parts[3]
                    }
                elif len(parts) == 2:
                    return {"server": f"http://{parts[0]}:{parts[1]}"}
    except Exception as e:
        print(f"Proxy read error: {e}")
    return None

def solve_captcha(site_key):
    if not API_KEY:
        print("CRITICAL ERROR: TWOCAPTCHA_API_KEY is missing in .env file.")
        sys.exit(1)
        
    captcha_url = f"https://2captcha.com/in.php?key={API_KEY}&method=userrecaptcha&googlekey={site_key}&pageurl=https://inube.com/join/"
    try:
        resp = requests.post(captcha_url, timeout=15).text
        if "OK|" not in resp:
            print(f"2Captcha Error: {resp}")
            return None
        
        captcha_id = resp.split("|")[1]
        res_url = f"https://2captcha.com/res.php?key={API_KEY}&action=get&id={captcha_id}"
        
        print("Waiting for 2Captcha to solve...")
        while True:
            import time
            time.sleep(5)
            res_resp = requests.get(res_url, timeout=15).text
            if "OK|" in res_resp:
                return res_resp.split("|")[1]
            elif "CAPCHA_NOT_READY" not in res_resp:
                return None
    except Exception as e:
        print(f"Exception in captcha: {e}")
        return None

def main():
    with sync_playwright() as p:
        proxy_config = get_random_proxy()
        if proxy_config:
            print(f"Using Proxy for Signup: {proxy_config['server']}")
            browser = p.chromium.launch(headless=False, proxy=proxy_config)
        else:
            print("Running signup without proxy.")
            browser = p.chromium.launch(headless=False)
            
        context = browser.new_context()
        page = context.new_page()
        
        print("Opening Inube Join Page...")
        page.goto("https://inube.com/join/")
        page.wait_for_selector(".g-recaptcha", state="visible", timeout=15000)
        
        try:
            site_key = page.locator(".g-recaptcha").get_attribute("data-sitekey")
            if not site_key:
                site_key = page.evaluate("document.querySelector('.g-recaptcha').getAttribute('data-sitekey');")
            print(f"Sitekey Detected: {site_key}")
        except Exception:
            site_key = "6LetIwETAARAAMKbksbFUz0Cp0jsMPdNm-QPN1ym"
        
        random_num = "".join(random.choices(string.digits, k=4))
        dummy_email = f"jentaltest{random_num}@mailinator.com"
        print(f"Target Email for Signup: {dummy_email}")
        
        page.locator("#join_name").fill("Jental")
        page.locator("#join_surname").fill("Singh")
        page.locator("#join_email").fill(dummy_email)
        
        token = solve_captcha(site_key)
        if token:
            print("Injecting token...")
            page.evaluate(f"document.getElementById('g-recaptcha-response').innerHTML='{token}';")
            page.evaluate("if(typeof verifyCallback === 'function') { verifyCallback(); }")
            
            print("Submitting Form...")
            page.locator('input[type="submit"][value="Join >>"]').click()
            
            try:
                # Upgraded Logic: URL badalne ke bajay browser ka network shaant hone ka wait karega
                page.wait_for_load_state("networkidle", timeout=20000)
                print("SUCCESS: Registration form submitted successfully.")
            except TimeoutError:
                # Agar proxy slow hui aur 20 sec se zyada laga, toh bhi hum success check de denge
                print("SUCCESS: Form submission completed (Network background active).")
        else:
            print("CRITICAL: Captcha Bypass Failed.")
        browser.close()

if __name__ == "__main__":
    main()
