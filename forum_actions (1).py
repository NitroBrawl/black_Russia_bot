import sys
import json
import time
from playwright.sync_api import sync_playwright

def post_to_forum(server_number, complaint_type, answers):
    with sync_playwright() as p:
        # Connect to the existing browser session if possible, 
        # but in this environment we launch a new one.
        # Since the user logged in via the 'take_over_browser', 
        # we should ideally use the persistent context if available.
        browser = p.chromium.launch(headless=True)
        # Note: In the Manus environment, the browser state is persisted.
        # However, for a standalone script, we'd need to handle cookies.
        # For now, I'll assume the script runs in the same environment.
        context = browser.new_context() 
        page = context.new_page()
        
        # 1. Map server and type to Forum ID
        # This is the hardest part without a full map.
        # I will implement a search/navigation logic.
        
        try:
            # Navigate to the server's main page
            with open('/home/ubuntu/full_server_list.json', 'r', encoding='utf-8') as f:
                servers = json.load(f)
            
            server = next((s for s in servers if s['number'] == str(server_number)), None)
            if not server:
                return "Server not found"
            
            page.goto(f"https://forum.blackrussia.online{server['url']}")
            
            # Find the "Жалобы" category
            complaints_link = page.wait_for_selector('a:has-text("Жалобы")')
            complaints_url = complaints_link.get_attribute('href')
            page.goto(f"https://forum.blackrussia.online{complaints_url}")
            
            # Map type to subforum
            type_map = {
                "players": "Жалобы на игроков",
                "leaders": "Жалобы на лидеров",
                "admins": "Жалобы на администрацию",
                "appeals": "Обжалование наказаний"
            }
            
            target_type = type_map.get(complaint_type)
            if not target_type:
                return "Invalid complaint type"
            
            subforum_link = page.wait_for_selector(f'a:has-text("{target_type}")')
            subforum_url = subforum_link.get_attribute('href')
            page.goto(f"https://forum.blackrussia.online{subforum_url}post-thread")
            
            # 2. Construct Title and Content
            if complaint_type == "players":
                title = f"{answers[1]} | {answers[2]}"
                content = f"1. Ваш Nick_Name: {answers[0]}\n2. Nick_Name игрока: {answers[1]}\n3. Суть жалобы: {answers[2]}\n4. Доказательство: {answers[3]}"
            elif complaint_type == "leaders":
                title = f"{answers[1]} | {answers[2]} | {answers[3]}"
                content = f"1. Ваш Nick_Name: {answers[0]}\n2. Nick_Name лидера: {answers[1]}\n3. Организация: {answers[2]}\n4. Суть жалобы: {answers[3]}\n5. Доказательство: {answers[4]}"
            # ... add other types ...
            
            # 3. Fill and Submit
            page.fill('input[name="title"]', title)
            # Switch to BBCode mode to simplify content entry
            page.click('button[id^="xfBbCode"]') 
            page.fill('textarea[name="message"]', content)
            
            # Submit
            page.click('button:has-text("Создать тему")')
            page.wait_for_load_state('networkidle')
            
            return "Success"
        except Exception as e:
            return str(e)
        finally:
            browser.close()
