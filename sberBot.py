import requests
from datetime import datetime
import pprint


class SberBot:
    server_url = "http://localhost:8000"
    login = None

    """Бот запускатеся функцией login_and_start
    При успешном бронировании порядок вызова функций выглядит следующим образом:
    login_and_start --> __start --> __enter_start_booking_time --> __enter_end_booking_time -->
     __enter_number_of_persons --> __check_availability --> __create_booking --> __send_booking_request -->
     login_and_start"""

    def login_and_start(self):
        login = input("Пожалуйста, введите свой логин: ")
        if login.isascii():
            self.login = login
            self.__start()
        else:
            print("Пожалуйста введите логин используя латинские буквы")
            self.login_and_start()

    def __start(self):
        action = input(
            "Если хотите забронировать столик, введите 1\n"
            "Если хотите посмотреть историю бронирования, введите 2\n"
            "Если хотите заново ввести логин, введите 3\n"
            "Если хотите выйти, введите 4\n"
        )

        if action.isdigit():
            action = int(action)
        else:
            print("Пожалуйста, введите число из предложенных вариантов")
            self.__start()

        if action == 1:
            self.__enter_start_booking_time()
        elif action == 2:
            try:
                response_history = requests.get(
                    self.server_url + "/api/booking/",
                    headers={"Authorization": f"login {self.login}"},
                )
                pprint.pprint(response_history.json())
                self.__start()
            except requests.exceptions.ConnectionError as e:
                # logger.error(e)
                print("Нет подключения к серверу")
                self.__start()
        elif action == 3:
            self.login_and_start()
        elif action == 4:
            exit()
        else:
            self.__start()

    def __enter_start_booking_time(self):
        time_str = input(
            "Введите время начала бронирования в форматее: ЧЧ:ММ ДД.ММ.ГГ\n"
        )
        try:
            start_booking_time = datetime.strptime(time_str, "%H:%M %d.%m.%y")
            self.__enter_end_booking_time(start_booking_time)
        except ValueError:
            print("Некорректный ввод")
            self.__enter_start_booking_time()

    def __enter_end_booking_time(self, start_booking_time):
        time_str = input(
            "Введите время конца бронирования в форматее: ЧЧ:ММ ДД.ММ.ГГ\n"
        )
        try:
            end_booking_time = datetime.strptime(time_str, "%H:%M %d.%m.%y")
            if end_booking_time <= start_booking_time:
                print(
                    "Ошибка: Время конца бронирования меньше времени начала бронирования"
                )
                self.__start()
            self.__enter_number_of_persons(start_booking_time, end_booking_time)
        except ValueError:
            print("Некорректный ввод")
            self.__enter_end_booking_time(start_booking_time)

    def __enter_number_of_persons(self, start_booking_time, end_booking_time):
        number_of_persons = input(
            "Введите кол-во человек для которого вы хотите забронировать столик\n"
        )
        if number_of_persons.isdigit():
            number_of_persons = int(number_of_persons)
        else:
            print("Некорректный ввод")
            self.__enter_number_of_persons(start_booking_time, end_booking_time)
        self.__check_availability(
            start_booking_time, end_booking_time, number_of_persons
        )

    def __check_availability(
            self, start_booking_time, end_booking_time, number_of_persons
    ):
        try:
            is_available_response = requests.post(
                self.server_url + "/api/check_availability/",
                data={
                    "start_time": str(start_booking_time),
                    "end_time": str(end_booking_time),
                    "person_number": str(number_of_persons),
                },
                headers={"Authorization": f"login {self.login}"},
            )

            if is_available_response:
                is_available_response_dict = is_available_response.json()
                if is_available_response_dict["available"]:
                    self.__create_booking(
                        is_available_response_dict,
                        start_booking_time,
                        end_booking_time,
                        number_of_persons,
                    )
                else:
                    print(
                        "Извините, к сожалению все столы для данного кол-ва человек на это время заняты"
                    )
                    self.__start()
            else:
                print("Что-то не так с сервером, попробуйсте сначала")
                self.__start()
        except requests.exceptions.ConnectionError as e:
            # logger.error(e)
            print("Нет подключения к серверу")
            self.__start()

    def __create_booking(
            self,
            is_available_response,
            start_booking_time,
            end_booking_time,
            number_of_persons,
    ):
        name = input(
            "Пожалуйста, введите имя человека на которого хотите забронировать\n"
        )

        if is_available_response["table_size"] > number_of_persons:
            print(
                "В данный момент можем предложить вам стол на "
                + str(is_available_response["table_size"])
                + " человек"
            )
            answer = input(
                "Если вы согласны, нажмите 1, для того чтобы вернуться в начало нажмите 2\n"
            )
            if answer.isdigit() and int(answer) == 2:
                self.__start()
            elif answer.isdigit() and int(answer) == 1:
                self.__send_booking_request(
                    number_of_persons,
                    start_booking_time,
                    end_booking_time,
                    name,
                    is_available_response["table"],
                )
            else:
                print("Wrong Input")
                self.__create_booking(
                    is_available_response,
                    start_booking_time,
                    end_booking_time,
                    number_of_persons,
                )
        else:
            self.__send_booking_request(
                number_of_persons,
                start_booking_time,
                end_booking_time,
                name,
                is_available_response["table"],
            )

    def __send_booking_request(
            self, number_of_persons, start_booking_time, end_booking_time, name, table_id
    ):
        response_book = requests.post(
            self.server_url + "/api/booking/",
            data={
                "people": number_of_persons,
                "reservation_start": str(start_booking_time),
                "reservation_end": str(end_booking_time),
                "person_name": name,
                "table": table_id,
            },
            headers={"Authorization": f"login {self.login}"},
        )
        if response_book.status_code == 201:
            print("Столик успешно забронирован")
            print("Детали бронирования: ", end="")
            pprint.pprint(response_book.json())
        else:
            print("Что-то пошло не так, статус:", response_book.status_code)
            # logger.error(f"Booking failed: {response_book.json()}")
        self.__start()
