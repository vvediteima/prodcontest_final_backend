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

# Передача оставшихся аргументов в unittest
sys.argv = [sys.argv[0]] + remaining

def get_base_url(args):
    prefix = args.prefix if args.prefix.startswith("/") else "/" + args.prefix
    return f"{args.url}:{args.port}{prefix}"

def decode_jwt(token):
    """Декодирование части JWT (payload) для отладки (без проверки подписи)"""
    try:
        parts = token.split('.')
        if len(parts) < 3:
            return ""
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
        cls.token = None         # Токен основного пользователя
        cls.mentor_token = None    # Токен ментора
        cls.test_question_uuid = None  # UUID созданного вопроса
        cls.mentor_id = None           # UUID ментора
        cls.test_request_id = None     # UUID созданного запроса

        # Регистрируем основного пользователя
        reg_url = f"{cls.base_url}/auth/reg/"
        user_data = {
            "name": "TestName",
            "surname": "TestSurname",
            "password": "TestPass123!",
            "login": "testuser123",
            "tags": ["tester", "python"],
            "description": "Тестовый пользователь",
            "job": "QA Engineer",
            "company": "TestCorp"
        }
        r = requests.post(reg_url, headers=cls.headers, data=json.dumps(user_data))
        if r.status_code == 200:
            print("Основной пользователь зарегистрирован.")
            cls.token = r.json()["token"]
        elif r.status_code == 409:
            print("Основной пользователь уже существует, выполняем логин.")
        else:
            print("Ошибка регистрации основного пользователя:", r.text)

        # Логинимся основным пользователем
        login_url = f"{cls.base_url}/auth/login/"
        login_data = {"login": "testuser123", "password": "TestPass123!"}
        r = requests.post(login_url, headers=cls.headers, data=json.dumps(login_data))
        if r.status_code == 200:
            cls.token = r.json()["token"]
            print("Логин основного пользователя успешен. Токен:", cls.token)
        else:
            print("Ошибка логина основного пользователя:", r.text)

        # Регистрируем ментора (с тегами 'mentor' и 'python')
        reg_url_mentor = f"{cls.base_url}/auth/reg/"
        mentor_data = {
            "name": "MentorName",
            "surname": "MentorSurname",
            "password": "MentorPass123!",
            "login": "testmentor",
            "tags": ["mentor", "python"],
            "description": "Тестовый ментор",
            "job": "Senior Developer",
            "company": "MentorCorp"
        }
        r = requests.post(reg_url_mentor, headers=cls.headers, data=json.dumps(mentor_data))
        if r.status_code == 200:
            print("Ментор зарегистрирован.")
            cls.mentor_token = r.json()["token"]
        elif r.status_code == 409:
            print("Ментор уже существует, выполняем логин для ментора.")
        else:
            print("Ошибка регистрации ментора:", r.text)
        # Логинимся ментором
        login_url_mentor = f"{cls.base_url}/auth/login/"
        mentor_login = {"login": "testmentor", "password": "MentorPass123!"}
        r = requests.post(login_url_mentor, headers=cls.headers, data=json.dumps(mentor_login))
        if r.status_code == 200:
            cls.mentor_token = r.json()["token"]
            try:
                payload = json.loads(decode_jwt(cls.mentor_token))
                cls.mentor_id = payload.get("sub")
            except Exception as e:
                print("Ошибка извлечения mentor_id:", e)
            print("Логин ментора успешен. mentor_id:", cls.mentor_id)
        else:
            print("Ошибка логина ментора:", r.text)

    def debug_response(self, response):
        print("Response status:", response.status_code)
        try:
            body = json.dumps(response.json(), indent=2, ensure_ascii=False)
            print("Response body:", body)
        except Exception:
            print("Response body (raw):", response.text)

    def test_03_update_user(self):
        url = f"{self.base_url}/auth/"
        update_data = {"name": "UpdatedName", "job": "Senior QA Engineer"}
        data = json.dumps(update_data)
        headers = self.headers.copy()
        headers["Authorization"] = f"Bearer {self.token}"
        print("\nТест: Обновление пользователя по URL:", url)
        print_curl("PATCH", url, headers=headers, data=data)
        response = requests.patch(url, headers=headers, data=data)
        self.debug_response(response)
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
        self.assertEqual(response.status_code, 200, f"Получение пользователей не прошло: {response.text}")
        data_json = response.json()
        self.assertIsInstance(data_json, list, "Ожидался список пользователей")

    def test_06_question_create_and_get(self):
        url = f"{self.base_url}/question/"
        headers = self.headers.copy()
        headers["Authorization"] = f"Bearer {self.token}"
        new_question = {
            "title": "Как настроить CI/CD?",
            "description": "Необходимо настроить процесс непрерывной интеграции и доставки для проекта на GitLab.",
            "tags": ["devops", "ci/cd", "gitlab"]
        }
        data = json.dumps(new_question)
        print("\nТест: Создание вопроса по URL:", url)
        print_curl("POST", url, headers=headers, data=data)
        response = requests.post(url, headers=headers, data=data)
        self.debug_response(response)
        self.assertEqual(response.status_code, 201, f"Создание вопроса не прошло: {response.text}")
        resp_data = response.json()
        self.assertIn("question_id", resp_data, "Не вернулся идентификатор вопроса")
        self.__class__.test_question_uuid = resp_data["question_id"]
        print("Создан вопрос с UUID:", self.__class__.test_question_uuid)

        # Получение списка вопросов
        url_get = f"{self.base_url}/question/"
        print("\nТест: Получение списка вопросов по URL:", url_get)
        print_curl("GET", url_get, headers=headers)
        response_get = requests.get(url_get, headers=headers)
        self.debug_response(response_get)
        self.assertIn(response_get.status_code, [200, 201], f"Получение вопросов не прошло: {response_get.text}")

    def test_07_request_create_many(self):
        if not self.test_question_uuid:
            self.skipTest("Нет тестового UUID вопроса для создания запроса.")
        url = f"{self.base_url}/request/{self.test_question_uuid}/many/"
        headers = self.headers.copy()
        headers["Authorization"] = f"Bearer {self.token}"
        req_body = {
            "mentors_id": [self.mentor_id],
            "description": "Нужна консультация по настройке сервера"
        }
        data = json.dumps(req_body)
        print("\nТест: Создание запросов ко множеству менторов по URL:", url)
        print_curl("POST", url, headers=headers, data=data)
        response = requests.post(url, headers=headers, data=data)
        self.debug_response(response)
        self.assertIn(response.status_code, [200, 201], f"Создание запросов не прошло: {response.text}")

    def test_08_request_create_single(self):
        if not self.test_question_uuid:
            self.skipTest("Нет тестового UUID вопроса для создания запроса.")
        url = f"{self.base_url}/request/{self.test_question_uuid}/{self.mentor_id}/"
        headers = self.headers.copy()
        headers["Authorization"] = f"Bearer {self.token}"
        req_body = {"description": "Нужна консультация по оптимизации базы данных"}
        data = json.dumps(req_body)
        print("\nТест: Создание запроса к ментору по URL:", url)
        print_curl("POST", url, headers=headers, data=data)
        response = requests.post(url, headers=headers, data=data)
        self.debug_response(response)
        # Если тело ответа не является валидным JSON, не пытаемся его декодировать
        self.assertEqual(response.status_code, 201, f"Создание запроса не прошло: {response.text}")
        try:
            resp_data = response.json()
            if "id" in resp_data:
                self.__class__.test_request_id = resp_data["id"]
                print("Создан запрос с UUID:", self.__class__.test_request_id)
        except Exception:
            print("Ответ не содержит JSON, принимаем статус 201 как корректный.")

    def test_09_request_incoming(self):
        url = f"{self.base_url}/request/incoming/"
        headers = self.headers.copy()
        headers["Authorization"] = f"Bearer {self.token}"
        print("\nТест: Получение входящих заявок по URL:", url)
        print_curl("GET", url, headers=headers)
        response = requests.get(url, headers=headers)
        self.debug_response(response)
        self.assertEqual(response.status_code, 200, f"Получение входящих заявок не прошло: {response.text}")

    def test_10_request_accepted(self):
        url = f"{self.base_url}/request/accepted/"
        headers = self.headers.copy()
        headers["Authorization"] = f"Bearer {self.token}"
        print("\nТест: Получение принятых заявок по URL:", url)
        print_curl("GET", url, headers=headers)
        response = requests.get(url, headers=headers)
        self.debug_response(response)
        self.assertEqual(response.status_code, 200, f"Получение принятых заявок не прошло: {response.text}")

    def test_11_admin_block_unblock(self):
        try:
            payload = json.loads(decode_jwt(self.token))
            user_id = payload.get("sub")
        except Exception as e:
            self.fail(f"Не удалось получить user_id из токена: {e}")
        url_block = f"{self.base_url}/admin/user/block/{user_id}/"
        url_unblock = f"{self.base_url}/admin/user/unblock/{user_id}/"
        print("\nТест: Блокировка пользователя по URL:", url_block)
        print_curl("PATCH", url_block, headers=self.headers)
        response_block = requests.patch(url_block, headers=self.headers)
        self.debug_response(response_block)
        self.assertEqual(response_block.status_code, 200, f"Блокировка не прошла: {response_block.text}")

        print("\nТест: Разблокировка пользователя по URL:", url_unblock)
        print_curl("PATCH", url_unblock, headers=self.headers)
        response_unblock = requests.patch(url_unblock, headers=self.headers)
        self.debug_response(response_unblock)
        self.assertEqual(response_unblock.status_code, 200, f"Разблокировка не прошла: {response_unblock.text}")

    def test_12_admin_set_verified(self):
        try:
            payload = json.loads(decode_jwt(self.token))
            user_id = payload.get("sub")
        except Exception as e:
            self.fail(f"Не удалось получить user_id из токена: {e}")
        url = f"{self.base_url}/admin/user/set_verified/{user_id}/true"
        print("\nТест: Изменение статуса верификации пользователя по URL:", url)
        print_curl("PATCH", url, headers=self.headers)
        response = requests.patch(url, headers=self.headers)
        self.debug_response(response)
        self.assertEqual(response.status_code, 200, f"Изменение статуса верификации не прошло: {response.text}")

    def test_13_admin_all_requests(self):
        url = f"{self.base_url}/admin/all_requests/"
        print("\nТест: Получение всех запросов по URL:", url)
        print_curl("GET", url, headers=self.headers)
        response = requests.get(url, headers=self.headers)
        self.debug_response(response)
        self.assertEqual(response.status_code, 200, f"Получение всех запросов не прошло: {response.text}")

    def test_14_request_mark_solved(self):
        # Тест для отметки запроса как решённого.
        # Если запрос не принят (нет поля accepted), ожидается 400.
        if not self.test_request_id:
            self.skipTest("Нет тестового UUID запроса для отметки как решённого.")
        url = f"{self.base_url}/request/{self.test_request_id}/solved/"
        headers = self.headers.copy()
        headers["Authorization"] = f"Bearer {self.token}"
        print("\nТест: Отметка запроса как решённого по URL:", url)
        print_curl("POST", url, headers=headers)
        response = requests.post(url, headers=headers)
        self.debug_response(response)
        self.assertEqual(response.status_code, 400, f"Отметка запроса как решённого не прошла (ожидался 400): {response.text}")

if __name__ == '__main__':
    unittest.main()
