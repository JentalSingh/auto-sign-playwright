#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import os
import random
import sys
from playwright.sync_api import sync_playwright, TimeoutError

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

def main():
    # Nick ke bataye flow ke mutabik email par aaye credentials yahan input karne hain
    username = input("Enter your Inube username (from email): ")
    password = input("Enter your Inube password (from email): ")
    
    if not username or not password:
        print("Username and password are required to login.")
        sys.exit(1)

    with sync_playwright() as p:
        proxy_config = get_random_proxy()
        if proxy_config:
            print(f"Using Proxy for Login: {proxy_config['server']}")
            browser = p.chromium.launch(headless=False, proxy=proxy_config)
        else:
            print("Running login without proxy.")
            browser = p.chromium.launch(headless=False)
            
        context = browser.new_context()
        page = context.new_page()
        
        print("Navigating to login page...")
        page.goto("https://inube.com/join/") 
        
        print("Filling login credentials...")
        page.locator('input[name="login_username"]').fill(username)
        page.locator('input[name="login_password"]').fill(password)
        
        print("Clicking login button...")
        # Inube ke login button element ko target kar raha hai
        page.locator('input[name="login_username"] ~ input[type="image"], .loginBoxInput + input').first.click()
        
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
            print("SUCCESS: Login action completed.")
        except TimeoutError:
            print("WARNING: Login confirmation timed out.")
            
        import time
        time.sleep(5)
        browser.close()

if __name__ == "__main__":
    main()
