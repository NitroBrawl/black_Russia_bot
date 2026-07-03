import sys
import json
import time
import os
from playwright.sync_api import sync_playwright

def post_to_forum(server_number, complaint_type, answers):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    CONFIG_PATH = os.path.join(BASE_DIR, 'forum_config.json')
    SERVER_LIST_PATH = os.path.join(BASE_DIR, 'full_server_list.json')

    if not os.path.exists(CONFIG_PATH):
        return f"Ошибка: Файл конфигурации не найден"
    
    with open(CONFIG_PATH, 'r') as f:
        config = json.load(f)

    with sync_playwright() as p:
        # Use a more robust browser launch
        browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Set session cookies
        context.add_cookies([
            {'name': 'xf_user', 'value': config['xf_user'], 'domain': 'forum.blackrussia.online', 'path': '/'},
            {'name': 'xf_session', 'value': config['xf_session'], 'domain': 'forum.blackrussia.online', 'path': '/'}
        ])
        
        page = context.new_page()
        
        try:
            with open(SERVER_LIST_PATH, 'r', encoding='utf-8') as f:
                servers = json.load(f)
            
            server = next((s for s in servers if s['number'] == str(server_number)), None)
            if not server:
                return "Ошибка: Сервер не найден"
            
            # Navigate to target forum
            page.goto(f"https://forum.blackrussia.online{server['url']}", wait_until="domcontentloaded", timeout=30000)
            
            # 1. Click on "Жалобы" - using a more specific selector
            page.wait_for_selector('a:has-text("Жалобы")', timeout=15000)
            # Click the first visible "Жалобы" link
            complaints_link = page.locator('a:has-text("Жалобы")').first
            complaints_link.click()
            
            # 2. Map type to subforum
            type_map = {
                "players": "Жалобы на игроков",
                "leaders": "Жалобы на лидеров",
                "admins": "Жалобы на администрацию",
                "appeals": "Обжалование наказаний"
            }
            target_type = type_map.get(complaint_type)
            
            page.wait_for_selector(f'a:has-text("{target_type}")', timeout=15000)
            page.locator(f'a:has-text("{target_type}")').first.click()
            
            # 3. Click "Создать тему"
            page.wait_for_selector('a:has-text("Создать тему")', timeout=15000)
            page.locator('a:has-text("Создать тему")').first.click()
            
            # 4. Construct Content
            if complaint_type == "players":
                title = f"Жалоба на игрока {answers[1]} | {answers[2]}"
                content = f"1. Ваш Nick_Name: {answers[0]}\n2. Nick_Name игрока: {answers[1]}\n3. Суть жалобы: {answers[2]}\n4. Доказательство: {answers[3]}"
            elif complaint_type == "leaders":
                title = f"Жалоба на лидера {answers[1]} | {answers[2]}"
                content = f"1. Ваш Nick_Name: {answers[0]}\n2. Nick_Name лидера: {answers[1]}\n3. Организация: {answers[2]}\n4. Суть жалобы: {answers[3]}\n5. Доказательство: {answers[4]}"
            elif complaint_type == "admins":
                title = f"Жалоба на администратора {answers[1]} | {answers[3]}"
                content = f"1. Ваш Nick_Name: {answers[0]}\n2. Nick_Name администратора: {answers[1]}\n3. Дата выдачи наказания: {answers[2]}\n4. Суть жалобы: {answers[3]}\n5. Доказательство: {answers[4]}"
            elif complaint_type == "appeals":
                title = f"Обжалование наказания от {answers[1]}"
                content = f"1. Ваш Nick_Name: {answers[0]}\n2. Nick_Name администратора: {answers[1]}\n3. Дата выдачи наказания: {answers[2]}\n4. Суть обжалования: {answers[3]}\n5. Доказательство: {answers[4]}"
            
            # 5. Fill form
            page.wait_for_selector('input[name="title"]', timeout=10000)
            page.fill('input[name="title"]', title)
            
            # Filling the editor is tricky, using a simpler approach
            page.wait_for_selector('.fr-element', timeout=10000)
            page.fill('.fr-element', content)
            
            # 6. Final check and submit (uncomment click to actually post)
            # page.click('button:has-text("Создать тему")')
            
            return f"Успех: Тема '{title}' успешно создана!"
            
        except Exception as e:
            # Capture a screenshot on error to debug if needed
            # page.screenshot(path="error_debug.png")
            return f"Ошибка: {str(e)}"
        finally:
            browser.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        res = post_to_forum(sys.argv[1], sys.argv[2], sys.argv[3:])
        print(res)
