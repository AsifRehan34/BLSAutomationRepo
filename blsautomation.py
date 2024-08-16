from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time
import requests
import io
import base64
import sys

# 2Captcha API Key
API_KEY = '878a2aa4e68c0415e7a5ae50730dfdd3'

def setup_driver():
    chrome_driver_path = r'C:\Users\wwwre\OneDrive\Desktop\BLSautomation\chromedriver.exe'
    service = Service(executable_path=chrome_driver_path)
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless')  # Uncomment to run headless
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def close_popup_if_present(driver):
    try:
        popup_close_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "pop-close"))
        )
        popup_close_button.click()
        print("Popup closed successfully.")
    except Exception as e:
        print("Popup not found or already closed:", e)

def navigate_to_login(driver):
    try:
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//span[@class='header-link d-xl-block']/a[@class='btn btn-default btn-sm']"))
        )
        login_button.click()
        print("Navigated to the login page successfully.")
    except Exception as e:
        print("Error navigating to the login page:", e)

def get_captcha_image_base64(driver):
    try:
        # Wait for captcha image to be visible
        captcha_img_element = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, "Imageid"))
        )
        captcha_img_src = captcha_img_element.get_attribute("src")
        
        response = requests.get(captcha_img_src)
        image_bytes = io.BytesIO(response.content)
        encoded_string = base64.b64encode(image_bytes.read()).decode('ascii')
        return encoded_string
    except Exception as e:
        print("Error fetching captcha image:", e)
        return None

def solve_captcha_with_2captcha(encoded_image):
    try:
        url = 'http://2captcha.com/in.php'
        data = {
            'key': API_KEY,
            'method': 'base64',
            'body': encoded_image,
            'json': 1
        }
        response = requests.post(url, data=data)
        result = response.json()
        if result['status'] == 1:
            request_id = result['request']
            print(f"Captcha submitted. Request ID: {request_id}")
            
            # Poll for captcha result
            result_url = 'http://2captcha.com/res.php'
            for _ in range(20):  # Poll up to 20 times
                time.sleep(5)
                result_response = requests.get(result_url, params={
                    'key': API_KEY,
                    'action': 'get',
                    'id': request_id,
                    'json': 1
                })
                result_data = result_response.json()
                if result_data['status'] == 1:
                    return result_data['request']
                elif result_data['status'] == 0 and result_data['request'] != 'CAPCHA_NOT_READY':
                    print("Error in captcha solving:", result_data['request'])
                    return None
        else:
            print("Error in captcha submission:", result['request'])
            return None
    except Exception as e:
        print("Error solving captcha with 2Captcha:", e)
        return None


def login(driver, email, password, max_attempts=3):
    attempt = 0
    while attempt < max_attempts:
        try:
            attempt += 1
            print(f"Login attempt {attempt} of {max_attempts}.")

            email_input = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, "//input[@placeholder='Enter Email']"))
            )
            email_input.clear()
            email_input.send_keys(email)

            password_input = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, "//input[@placeholder='Enter Password']"))
            )
            password_input.clear()
            password_input.send_keys(password)

            captcha_base64 = get_captcha_image_base64(driver)

            if captcha_base64:
                captcha_text = solve_captcha_with_2captcha(captcha_base64)

                if captcha_text:
                    captcha_input = driver.find_element(By.ID, "captcha_code_reg")
                    captcha_input.clear()
                    captcha_input.send_keys(captcha_text)

                    submit_button = driver.find_element(By.NAME, "submitLogin")
                    submit_button.click()
                    print("Login submitted.")

                    # Check for login success or failure
                    time.sleep(5)  # Wait to ensure login attempt is processed

                    # Verify if login was successful by checking for the presence of a logout button or any other element that appears after a successful login
                    if "login failed" not in driver.page_source.lower():
                        print("Login successful.")
                        return True
                    else:
                        print("Login failed due to incorrect captcha or credentials.")
                        raise Exception("Login failed. Stopping script.")  # Stop the script if login fails

                else:
                    print("Failed to get captcha text.")
            else:
                print("Failed to get captcha image.")
        
        except Exception as e:
            print("Error during login attempt:", e)

    print("Max login attempts reached. Login failed.")
    sys.exit("Login failed. Exiting script.")  # Exit the script if all attempts fail

def check_balance():
    try:
        url = 'http://2captcha.com/res.php'
        response = requests.get(url, params={
            'key': API_KEY,
            'action': 'getbalance',
            'json': 1
        })
        result = response.json()
        if result['status'] == 1:
            print(f"Current balance: ${result['request']}")
            return float(result['request'])
        else:
            print("Error checking balance:", result['request'])
            return 0.0
    except Exception as e:
        print("Error checking balance:", e)
        return 0.0

def close_post_login_popup(driver):
    try:
        popup_close_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "post-login-popup-close"))
        )
        popup_close_button.click()
        print("Post-login popup closed successfully.")
    except Exception as e:
        print("Post-login popup not found or already closed:", e)

def book_appointment(driver):
    try:
        # Wait for the "Book Appointment" button to be clickable and click it
        book_button = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Book Appointment"))
        )
        book_button.click()
        print("Clicked on 'Book Appointment'.")

        # Wait for the location dropdown to be present and select Islamabad
        location_select = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.ID, "valCenterLocationId"))
        )
        select = Select(location_select)
        select.select_by_visible_text("Quetta (Pakistan)")
        print("Selected Quetta location.")

        # Wait for the visa type dropdown to be present and select Study Visa
        visa_select = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.ID, "valCenterLocationTypeId"))
        )
        select = Select(visa_select)
        select.select_by_visible_text("Legalisation")
        print("Selected Legalisation Visa.")

        # Wait for the page to update and ensure the application type dropdown is present
        app_type_dropdown = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.ID, "valAppointmentForMembers"))
        )

        # Use JavaScript to select the "Individual" option
        individual_option = app_type_dropdown.find_element(By.XPATH, ".//option[contains(text(), 'Individual')]")
        driver.execute_script("arguments[0].setAttribute('selected', 'selected')", individual_option)
        driver.execute_script("window.location.href = arguments[0].value", individual_option)

        print("Selected application type: Individual and navigated.")

        # Wait for the page to load after selecting the individual option
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "Imageid"))  # Wait for the captcha image to appear
        )

        # Solve captcha to proceed
        captcha_base64 = get_captcha_image_base64(driver)
        if captcha_base64:
            captcha_text = solve_captcha_with_2captcha(captcha_base64)
            if captcha_text:
                captcha_input = driver.find_element(By.ID, "captcha_code_reg")
                captcha_input.send_keys(captcha_text)
                print("Solved captcha after booking steps.")
            else:
                print("Failed to solve captcha after booking steps.")
        else:
            print("Failed to get captcha image after booking steps.")

    except Exception as e:
        print("Error during booking steps:", e)

def click_date_dropdown(driver):
    try:
        # Find and click the date dropdown
        date_dropdown = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "valAppointmentDate"))
        )
        date_dropdown.click()
        print("Date dropdown clicked.")
    except TimeoutException:
        print("Timeout while waiting for the date dropdown to be clickable.")
    except NoSuchElementException:
        print("Date dropdown not found.")
    except Exception as e:
        print(f"Error clicking the date dropdown: {e}")


def monitor_and_book_slot(driver):
    try:
        print("Starting to monitor available slots...")

        while True:
            try:
                # Find all the days with available slots
                available_slots = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//td[contains(@class, 'day') and contains(@class, 'label-available')]"))
                )

                if available_slots:
                    # Click the first available slot
                    available_slots[0].click()
                    print("Available slot selected. Checking for appointment type dropdown.")
                    
                    # Check if the appointment type dropdown appears
                    if select_appointment_type(driver):
                        print("Appointment type selected.")
                    else:
                        print("Appointment type not available. Skipping this step.")
                    
                    break
                else:
                    print("No available slots. Still monitoring...")

            except TimeoutException:
                print("Timeout occurred while waiting for available slots. Retrying...")
            except NoSuchElementException:
                print("No available slots found. Retrying...")
            except Exception as e:
                print(f"Unexpected error during slot monitoring: {e}")

            # Sleep before trying again
            time.sleep(1)  # Check every second

    except Exception as e:
        print(f"Error monitoring and booking slots: {e}")

def select_appointment_type(driver):
    try:
        # Wait for the appointment type dropdown to appear within a reasonable time
        app_type_dropdown = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "valAppointmentType"))
        )
        print("Appointment type dropdown found.")

        # Select "Normal Time"
        select = Select(app_type_dropdown)
        select.select_by_value("normal")
        print("Selected 'Normal Time' as appointment type.")
        
        return True  # Indicate that the appointment type was successfully selected

    except TimeoutException:
        print("Appointment type dropdown not found. It may not be available on this page.")
        return False  # Indicate that the appointment type was not available
    except NoSuchElementException:
        print("Appointment type dropdown element not found.")
        return False  # Indicate that the appointment type was not available
    except Exception as e:
        print(f"Error selecting appointment type: {e}")
        return False  # Indicate that the appointment type was not available
def fill_details_and_proceed_to_payment(driver):
    try:
        # Wait for the first name field to be present
        first_name_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "valApplicant[1][first_name]"))
        )
        first_name_field.clear()
        first_name_field.send_keys("Waleed")
        print("First name entered.")

        # Wait for the last name field to be present
        last_name_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "valApplicant[1][last_name]"))
        )
        last_name_field.clear()
        last_name_field.send_keys("Wahab")
        print("Last name entered.")

        # Check the condition box
        agree_checkbox = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "agree"))
        )
        if not agree_checkbox.is_selected():
            agree_checkbox.click()
        print("Condition box checked.")

        # # Proceed to the payment page
        # proceed_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Proceed to Payment')]")
        # proceed_button.click()
        # print("Proceeding to the payment page...")

    except Exception as e:
        print(f"Error filling details or proceeding to payment: {str(e)}")


# Start monitoring and booking
def main():
    driver = setup_driver()

    try:
        driver.get("https://blsitalypakistan.com/")
        close_popup_if_present(driver)
        navigate_to_login(driver)
        if login(driver, "walees.wahab321@gmail.com", "Italianuni#123"):
            close_post_login_popup(driver)
            book_appointment(driver)
            click_date_dropdown(driver)  # Click the date dropdown first
            monitor_and_book_slot(driver)  # Start monitoring and booking slots
            fill_details_and_proceed_to_payment(driver)
    finally:
        # Keep the browser open for manual work
        print("Browser is open for manual work. Close it when done.")
        input("Press Enter to close the browser...")  # Wait for user input
        # driver.quit()  # Ensure this line is commented out to keep the browser open
        

if __name__ == "__main__":
    main()

