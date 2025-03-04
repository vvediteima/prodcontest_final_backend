import argparse
import sys
import unittest
import requests
import json
import uuid
import base64

# Разбор аргументов для тестового окружения
parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('--url', type=str, default="http://localhost")
parser.add_argument('--port', type=str, default="5000")
parser.add_argument('--prefix', type=str, default="/")
args, remaining = parser.parse_known_args()

# Перезаписываем sys.argv для unittest, чтобы наши аргументы не мешали
sys.argv = [sys.argv[0]] + remaining

def get_base_url(args):
    # Если префикс задан без начального слеша, добавить его
    prefix = args.prefix if args.prefix.startswith("/") else "/" + args.prefix
    return f"{args.url}:{args.port}{prefix}"

TEST_USER = {
    "name": "TestName",
    "surname": "TestSurname",
    "password": "TestPass123!",
    "login": "testuser123",
    "tags": ["tester", "python"],
    "description": "Тестовый пользователь",
    "job": "QA Engineer",
    "company": "TestCorp"
}

def decode_jwt(token):
    """Декодирование части JWT (payload) для отладки (без проверки подписи)"""
    try:
        parts = token.split('.')
        if len(parts) < 2:
            return None
        padded = parts[1] + '=' * ((4 - len(parts[1]) % 4) % 4)
        payload = base64.urlsafe_b64decode(padded)
        return payload.decode('utf-8')
    except Exception as e:
        return f"Ошибка декодирования: {str(e)}"

def print_curl(method, url, headers=None, data=None):
    """Формирует и выводит эквивалентную команду curl для отладки."""
    headers_str = ""
    if headers:
        for key, value in headers.items():
            headers_str += f" -H '{key}: {value}'"
    data_str = f" -d '{data}'" if data else ""
    cmd = f"curl -X {method.upper()} '{url}'{headers_str}{data_str}"
    print("Эквивалентная команда curl:")
    print(cmd)
    print("-" * 80)

class APITestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_url = get_base_url(args)
        print("Тестируем API по базовому URL:", cls.base_url)
        cls.headers = {"Content-Type": "application/json", "accept": "application/json"}
        cls.token = None

    def debug_response(self, response):
        print("Response status:", response.status_code)
        try:
            body = json.dumps(response.json(), indent=2, ensure_ascii=False)
            print("Response body:", body)
        except Exception:
            print("Response body (raw):", response.text)

    def test_01_registration(self):
        url = f"{self.base_url}/auth/reg/"
        data = json.dumps(TEST_USER)
        print("\nТест: Регистрация пользователя по URL:", url)
        print_curl("POST", url, headers=self.headers, data=data)
        response = requests.post(url, headers=self.headers, data=data)
        self.debug_response(response)
        self.assertEqual(response.status_code, 200, f"Регистрация не прошла: {response.text}")
        data_json = response.json()
        self.assertIn("token", data_json, "JWT токен не получен при регистрации")
        self.__class__.token = data_json["token"]
        print("Получен JWT токен:", self.token)
        print("Декодированный payload:", decode_jwt(self.token))

    def test_02_login(self):
        url = f"{self.base_url}/auth/login"
        credentials = {
            "login": TEST_USER["login"],
            "password": TEST_USER["password"]
        }
        data = json.dumps(credentials)
        print("\nТест: Логин по URL:", url)
        print_curl("POST", url, headers=self.headers, data=data)
        response = requests.post(url, headers=self.headers, data=data)
        self.debug_response(response)
        self.assertEqual(response.status_code, 200, f"Логин не прошёл: {response.text}")
        data_json = response.json()
        self.assertIn("token", data_json, "JWT токен не получен при логине")
        self.__class__.token = data_json["token"]
        print("Получен JWT токен:", self.token)
        decoded = decode_jwt(self.token)
        print("Декодированный payload:", decoded)
        try:
            payload = json.loads(decoded)
            print("sub из токена:", payload.get("sub"))
        except Exception as e:
            print("Ошибка при разборе payload:", e)

    def test_03_update_user(self):
        url = f"{self.base_url}/auth/"
        update_data = {
            "name": "UpdatedName",
            "job": "Senior QA Engineer"
        }
        data = json.dumps(update_data)
        headers = self.headers.copy()
        headers["Authorization"] = f"Bearer {self.token}"
        print("\nТест: Обновление пользователя по URL:", url)
        print_curl("PATCH", url, headers=headers, data=data)
        response = requests.patch(url, headers=headers, data=data)
        self.debug_response(response)
        if response.status_code != 200:
            print("Ошибка обновления пользователя. Проверьте, что идентификатор из токена совпадает с записью в базе.")
            try:
                payload = json.loads(decode_jwt(self.token))
                sub = payload.get("sub")
                print("Тип sub из токена:", type(sub), "Значение:", sub)
                # Для сравнения выводим тип из базы (ожидается UUID)
                try:
                    uuid_sub = uuid.UUID(sub)
                    print("Преобразованное значение sub (UUID):", uuid_sub)
                except Exception as ex:
                    print("Ошибка преобразования sub в UUID:", ex)
            except Exception as e:
                print("Ошибка при разборе payload:", e)
        self.assertEqual(response.status_code, 200, f"Обновление пользователя не прошло: {response.text}")

    def test_04_get_admin_stats(self):
        url = f"{self.base_url}/admin/stats/"
        print("\nТест: Получение статистики по URL:", url)
        print_curl("GET", url, headers=self.headers)
        response = requests.get(url, headers=self.headers)
        self.debug_response(response)
        self.assertEqual(response.status_code, 200, f"Получение статистики не прошло: {response.text}")
        data_json = response.json()
        self.assertIn("total_users", data_json, "В ответе статистики отсутствует total_users")

    def test_05_get_all_users(self):
        url = f"{self.base_url}/admin/users/"
        print("\nТест: Получение списка пользователей по URL:", url)
        print_curl("GET", url, headers=self.headers)
        response = requests.get(url, headers=self.headers)
        self.debug_response(response)
        self.assertEqual(response.status_code, 200, f"Получение списка пользователей не прошло: {response.text}")
        data_json = response.json()
        self.assertIsInstance(data_json, list, "Ожидался список пользователей")

    def test_06_get_mentors_by_question(self):
        '''        # Используем произвольный UUID для вопроса (замените на существующий, если есть тестовые данные)
        question_uuid = "6540db7b-8531-4889-a2b6-ba4020ea5d44"
        url = f"{self.base_url}/question/{question_uuid}/"
        headers = self.headers.copy()
        headers["Authorization"] = f"Bearer {self.token}"
        print("\nТест: Получение менторов по вопросу по URL:", url)
        print_curl("GET", url, headers=headers)
        response = requests.get(url, headers=headers)
        self.debug_response(response)
        self.assertIn(response.status_code, [200, 404], f"Получение менторов по вопросу вернул неожиданный код: {response.text}")
        '''
    def test_07_get_mentors_by_tags(self):
        # Согласно спецификации эндпоинт для поиска менторов по тегам имеет адрес /tags/mentors/
        url = f"{self.base_url}/tags/mentors/"
        tags = ["python", "flask"]
        data = json.dumps(tags)
        print("\nТест: Поиск менторов по тегам по URL:", url)
        print_curl("POST", url, headers=self.headers, data=data)
        response = requests.post(url, headers=self.headers, data=data)
        self.debug_response(response)
        self.assertEqual(response.status_code, 200, f"Поиск менторов по тегам не прошёл: {response.text}")
        data_json = response.json()
        self.assertIsInstance(data_json, list, "Ожидался список менторов")
        self.assertIn("X-Total-Count", response.headers, "Отсутствует заголовок X-Total-Count")

if __name__ == '__main__':
    unittest.main()
