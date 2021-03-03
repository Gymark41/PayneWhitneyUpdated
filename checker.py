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
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from collections import namedtuple

# Import smtplib for the actual sending function
import smtplib

# Here are the email package modules we'll need
from email.mime.text import MIMEText

import sqlite3

User_Info = namedtuple("User_Info", "ID FirstName LastName Email PhoneNumber ServiceProvider")
Date_Preference = namedtuple("Date_Preference", "id DayOfWeek Time UserID")
People_File = "People_Database.sqlite"


class AutoSigner:

    def __init__(self):
        self.users = self.get_people()

    def send_email(self, message: str, recipients: [str]):
        # creates SMTP session
        s = smtplib.SMTP('smtp.gmail.com', 587)

        # start TLS for security
        s.starttls()

        # Authentication
        s.login("testingsmtpyale@gmail.com", "!@#QWEqwe")

        # message to be sent

        # sending the mail
        s.sendmail("testingsmtpyale@gmail.com", recipients, message)

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
                wait = WebDriverWait(driver, 10)
                wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="Close"]'))).click()

                fitness_box = driver.find_element_by_xpath("//*[contains(text(), 'Fitness Center Strength')]")
                time.sleep(2)
                fitness_box.find_element_by_xpath("..").click()
                time.sleep(5)

                try:
                    next_button = driver.find_element_by_xpath("//div[@class='date-item date-right classitem']")
                    next_button.click()
                    time.sleep(2)
                except NoSuchElementException:
                    None

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
                    emails = []
                    for user in self.users:
                        emails.append(user.Email)
                        emails.append(str(user.PhoneNumber) + "@" + user.ServiceProvider)
                    self.send_email("Slots on " + datetime.strftime(latest_date_available, '%m/%d/%Y')
                                    + " are now open for the weight room", emails)
                    self.book_times(latest_date_available, driver)

                # self.book_times(datetime(year=2021, month=3, day=8), driver)

                file = open("last_date.txt", 'w')
                file.write(latest_date_string)
                file.close()

                driver.close()
                on_cycle += 1
                print("On Cycle: " + str(on_cycle) + ", Time: " + str(datetime.now()))
                time.sleep(600)
            except ValueError:
                print("Error")

    def book_times(self, new_date: datetime, driver: webdriver.chrome):
        time_preferences = self.get_time_preferences(new_date.weekday())
        for preference in time_preferences:
            user_index = [y[0] for y in self.users].index(preference.UserID)
            user = self.users[user_index]
            book_time = new_date
            book_time = book_time.replace(hour=int(preference.Time[0:2]), minute=int(preference.Time[3:5]), )
            print(book_time.hour)
            time_string = datetime.strftime(book_time, "%-d" + self.get_suffix(book_time.day) + " %b %Y, %I:%M %p ")
            print(time_string)
            try:
                fitness_box = driver.find_element_by_xpath("//*[contains(text(), '" + time_string + "')]")
                scroll_element_into_middle = "var viewPortHeight = Math.max(document.documentElement.clientHeight, " \
                                             "window.innerHeight || 0); var elementTop = arguments[" \
                                             "0].getBoundingClientRect().top; window.scrollBy(0, elementTop-(" \
                                             "viewPortHeight/2)); "

                driver.execute_script(scroll_element_into_middle, fitness_box)
                time.sleep(1)
                fitness_box.find_element_by_xpath("..").click()
                time.sleep(1)
                driver.find_element_by_xpath("//input[@class='form-control firstname']").send_keys(user.FirstName)
                driver.find_element_by_xpath("//input[@class='form-control lastname']").send_keys(user.LastName)
                driver.find_element_by_xpath("//input[@class='form-control custemail']").send_keys(user.Email)
                driver.find_element_by_xpath("//input[@class='form-control custmobile mobilenumber']").send_keys(
                    user.PhoneNumber)
                driver.find_element_by_xpath("//input[@class='form-control other_of0']").send_keys("Yes")
                driver.find_element_by_xpath("//button[@class='btn btn-primary margin-bottom booknow']").click()

                time.sleep(2)
                driver.find_element_by_xpath("//button[@class='btn btn-primary margin-bottom bookanother']").click()
                time.sleep(2)
                emails = [user.Email, str(user.PhoneNumber) + "@" + user.ServiceProvider]
                self.send_email(
                    "Fitness Center Strength Booked on " + time_string + "completed. Check your email for Yale "
                                                                         "confirmation", emails)
                self.add_time_preference(book_time, user.ID)

                fitness_box = driver.find_element_by_xpath("//*[contains(text(), 'Fitness Center Strength')]")
                time.sleep(2)
                fitness_box.find_element_by_xpath("..").click()
                time.sleep(5)

            except NoSuchElementException:
                print('Book Time does not exist')

    def create_database(self):
        conn = sqlite3.connect(People_File)

        c = conn.cursor()

        # Create table
        c.execute('''CREATE TABLE Users (ID INTEGER NOT NULL PRIMARY KEY, FirstName TEXT, LastName TEXT, Email TEXT, 
        PhoneNumber INTEGER, ServiceProvider TEXT);''')

        # Create table
        c.execute('''CREATE TABLE DatePreferences
                                     (id INTEGER NOT NULL PRIMARY KEY, DayOfWeek INT, Time TEXT, UserID INTEGER, 
                                     FOREIGN KEY(UserID) REFERENCES Users(ID));''')

        # Create table
        c.execute('''CREATE TABLE Signups
                                     (ID INTEGER NOT NULL PRIMARY KEY, Date TEXT, UserID INTEGER, 
                                     FOREIGN KEY(UserID) REFERENCES Users(ID));''')

        # Insert a row of data
        c.execute("INSERT INTO Users (FirstName, LastName, Email, PhoneNumber) "
                  "VALUES ('Mark','Ge','mark.ge@yale.edu', 5025338178);")

        c.execute("INSERT INTO Users (FirstName, LastName, Email, PhoneNumber) "
                  "VALUES ('Kevin','Zhong','kevin.zhong@yale.edu', 9084487684);")

        # Save (commit) the changes
        conn.commit()

        # We can also close the connection if we are done with it.
        # Just be sure any changes have been committed or they will be lost.
        conn.close()

    def add_time_preference(self, date_booked, user_id):
        conn = sqlite3.connect(People_File)
        c = conn.cursor()

        c.execute("INSERT INTO Signups (Date, UserID) "
                  "VALUES ('" + str(date_booked) + "', " + str(user_id) + ");")

        conn.commit()
        conn.close()

    def set_time_preference(self):
        conn = sqlite3.connect(People_File)
        c = conn.cursor()

        c.execute("INSERT INTO DatePreferences (DayOfWeek, Time, UserID) "
                  "VALUES (0,'18:15', 1);")
        c.execute("INSERT INTO DatePreferences (DayOfWeek, Time, UserID) "
                  "VALUES (4,'18:15', 1);")
        c.execute("INSERT INTO DatePreferences (DayOfWeek, Time, UserID) "
                  "VALUES (0,'18:15', 2);")
        c.execute("INSERT INTO DatePreferences (DayOfWeek, Time, UserID) "
                  "VALUES (4,'18:15', 2);")
        c.execute("INSERT INTO DatePreferences (DayOfWeek, Time, UserID) "
                  "VALUES (0,'18:15', 1);")

        conn.commit()
        conn.close()

    def get_time_preferences(self, dayOfWeek: int) -> [Date_Preference]:
        conn = sqlite3.connect(People_File)
        c = conn.cursor()
        c.execute("SELECT * FROM DatePreferences where DayOfWeek = " + str(dayOfWeek))
        rows = c.fetchall()

        rows_adjusted = []
        for row in rows:
            print(row)
            rows_adjusted.append(Date_Preference(*row))
        conn.close()
        return rows_adjusted

    def get_people(self) -> [User_Info]:
        conn = sqlite3.connect(People_File)
        c = conn.cursor()
        c.execute("SELECT * FROM Users")
        rows = c.fetchall()
        rows_adjusted = []
        for row in rows:
            print(row)
            rows_adjusted.append(User_Info(*row))
        conn.close()
        return rows_adjusted

    def get_suffix(self, value):
        options = {
            0: 'th',
            1: 'st',
            2: 'nd',
            3: 'rd',
            4: 'th',
            5: 'th',
            6: 'th',
            7: 'th',
            8: 'th',
            9: 'th'
        }
        return options[value % 10]


def main():
    # chrome_options = Options()
    # chrome_options.add_argument("--headless")
    #
    # path = os.path.dirname(__file__) + "/chromedriver"
    # driver = webdriver.Chrome(executable_path=path, options=chrome_options)
    # driver.get("https://www.picktime.com/yalepwg")  # put here the adress of your page

    my_signup = AutoSigner()
    my_signup.sign_up_loop()


if __name__ == "__main__":
    main()
