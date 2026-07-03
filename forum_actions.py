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
        return f"Ошибка: Файл конфигурации не найден: {CONFIG_PATH}"
    
    with open(CONFIG_PATH, 'r') as f:
        config = json.load(f)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        
        # Set session cookies
        context.add_cookies([
            {
                'name': 'xf_user',
                'value': config['xf_user'],
                'domain': 'forum.blackrussia.online',
                'path': '/'
            },
            {
                'name': 'xf_session',
                'value': config['xf_session'],
                'domain': 'forum.blackrussia.online',
                'path': '/'
            }
        ])
        
        page = context.new_page()
        
        try:
            # Load server list
            if not os.path.exists(SERVER_LIST_PATH):
                return f"Ошибка: Список серверов не найден: {SERVER_LIST_PATH}"
                
            with open(SERVER_LIST_PATH, 'r', encoding='utf-8') as f:
                servers = json.load(f)
            
            server = next((s for s in servers if s['number'] == str(server_number)), None)
            if not server:
                return "Ошибка: Сервер не найден"
            
            # Navigate to target forum
            target_url = f"https://forum.blackrussia.online{server['url']}"
            page.goto(target_url)
            
            # Check if logged in
            if "Вход" in page.content() and "BLACK RUSSIA FORUMS BOT" not in page.content():
                return "Ошибка: Сессия устарела. Нужно обновить куки."

            # Find Complaints category
            page.wait_for_selector('a:has-text("Жалобы")', timeout=10000)
            page.click('a:has-text("Жалобы")')
            
            # Map type to subforum
            type_map = {
                "players": "Жалобы на игроков",
                "leaders": "Жалобы на лидеров",
                "admins": "Жалобы на администрацию",
                "appeals": "Обжалование наказаний"
            }
            
            target_type = type_map.get(complaint_type)
            page.wait_for_selector(f'a:has-text("{target_type}")', timeout=10000)
            page.click(f'a:has-text("{target_type}")')
            
            # Click "Create Thread"
            page.wait_for_selector('a:has-text("Создать тему")', timeout=10000)
            page.click('a:has-text("Создать тему")')
            
            # Construct Title and Content
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
            
            # Fill form
            page.fill('input[name="title"]', title)
            
            # Use BBCode editor if possible for easier formatting
            editor = page.locator('.fr-element.fr-view')
            editor.fill(content)
            
            # Submit
            # page.click('button:has-text("Создать тему")') # Disabled for safety during testing
            
            return f"Успех: Тема '{title}' подготовлена к публикации."
            
        except Exception as e:
            return f"Ошибка: {str(e)}"
        finally:
            browser.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        res = post_to_forum(sys.argv[1], sys.argv[2], sys.argv[3:])
        print(res)
