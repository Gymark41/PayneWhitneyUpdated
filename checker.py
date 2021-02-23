import os
import time

from pathlib import Path
from datetime import timedelta, date, datetime

from selenium import webdriver
from selenium.webdriver.common.keys import Keys

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from collections import namedtuple

# Import smtplib for the actual sending function
import smtplib

# Here are the email package modules we'll need
from email.mime.text import MIMEText

from typing import NamedTuple
import pickle

WeekTime = namedtuple('WeekTime', 'Time Week')
People_File = "People_File"


class Person(NamedTuple):
    first_name: str
    last_name: str
    user_email: str
    user_phone_num: str
    completed_dates: [datetime]
    hour_interval: [WeekTime]


class AutoSigner:

    def __init__(self):
        self.users = self.get_people()

    def send_email(self, last_date: datetime):
        # creates SMTP session
        s = smtplib.SMTP('smtp.gmail.com', 587)

        # start TLS for security
        s.starttls()

        # Authentication
        s.login("testingsmtpyale@gmail.com", "!@#QWEqwe")

        # message to be sent
        message = "Slots on " + datetime.strftime(last_date, '%m/%d/%Y') + " are now open for the weight room"

        # sending the mail
        s.sendmail("testingsmtpyale@gmail.com", "5025338718@tmomail.net", message)
        s.sendmail("testingsmtpyale@gmail.com", "9084487684@vtext.com", message)
        s.sendmail("testingsmtpyale@gmail.com", "mark.ge@yale.edu", message)

        # s.sendmail("testingsmtpyale@gmail.com", "mark.ge@yale.edu", message)

        # terminating the session
        s.quit()


    def sign_up_loop(self):
        on_cycle = 0
        while True:
            try:
                chrome_options = Options()
                chrome_options.add_argument("--headless")

                path = os.path.dirname(__file__) + "/chromedriver"

                driver = webdriver.Chrome(executable_path=path, options=chrome_options)
                driver.get("https://www.picktime.com/yalepwg")  # put here the adress of your page
                time.sleep(5)
                WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="Close"]'))).click()

                fitness_box = driver.find_element_by_xpath("//*[contains(text(), 'Fitness Center Strength')]")

                fitness_box.find_element_by_xpath("..").click()
                time.sleep(5)
                last_line = driver.find_element_by_xpath("//div[@class='booking-list-box']/ul/li[last()]")
                date_string = last_line.get_attribute('data-date')

                last_date = date(2021, 1, 1)

                if Path("last_date.txt").is_file():
                    file = open("last_date.txt", 'r')
                    saved_date = file.read()
                    last_date = datetime.strptime(saved_date, '%Y%m%d')
                    file.close()

                latest_date_string = date_string[0:8]
                latest_date_available = datetime.strptime(latest_date_string, '%Y%m%d')

                if last_date < latest_date_available:
                    print("Changed")
                    self.send_email(latest_date_available)

                file = open("last_date.txt", 'w')
                file.write(latest_date_string)
                file.close()

                driver.close()
                on_cycle += 1
                print("On Cycle: " + str(on_cycle) + ", Time: " + str(datetime.now()))
                time.sleep(600)
            except ValueError:
                print("Error")


    def set_times(self):
        kevin_zhong = Person(first_name="Kevin", last_name="Zhong", user_email="Kevin.Zhong@yale.edu",
                             user_phone_num="9084487684", completed_dates=[], hour_interval=[WeekTime(18, 0), WeekTime(18, 4)])

        mark_ge = Person(first_name="Mark", last_name="Ge", user_email="Mark.Ge@yale.edu",
                         user_phone_num="5025338718", completed_dates=[], hour_interval=[WeekTime(18, 0), WeekTime(18, 4)])

        peoples = [kevin_zhong, mark_ge]
        with open(People_File, 'w+') as handle:
            pickle.dump(peoples, handle, protocol=pickle.HIGHEST_PROTOCOL)

    def get_people(self) -> [Person]:
        if Path(People_File).is_file():
            with open(People_File, 'rb') as handle:
                return pickle.load(handle)
        else:
            return []



def main():
    my_signup = AutoSigner()
    my_signup.sign_up_loop()


if __name__ == "__main__":
    main()
