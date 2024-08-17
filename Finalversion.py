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

# 2Captcha API Key
API_KEY = '878a2aa4e68c0415e7a5ae50730dfdd3'

def setup_driver():
    chrome_driver_path = r'C:\Users\wwwre\OneDrive\Desktop\BLSautomation\chromedriver.exe'
    service = Service(executable_path=chrome_driver_path)
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-notifications')  # Disable pop-up notifications
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def close_popup_if_present(driver):
    try:
        popup_close_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "pop-close"))
        )
        popup_close_button.click()
        print("Popup closed successfully.")
    except TimeoutException:
        print("No popup found or it was already closed.")

def navigate_to_login(driver):
    try:
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//span[@class='header-link d-xl-block']/a[@class='btn btn-default btn-sm']"))
        )
        login_button.click()
        print("Navigated to the login page successfully.")
    except TimeoutException:
        print("Error navigating to the login page.")

def get_captcha_image_base64(driver):
    try:
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
    for attempt in range(1, max_attempts + 1):
        print(f"Login attempt {attempt} of {max_attempts}.")
        try:
            # Input email
            email_input = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, "//input[@placeholder='Enter Email']"))
            )
            email_input.clear()
            email_input.send_keys(email)

            # Input password
            password_input = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, "//input[@placeholder='Enter Password']"))
            )
            password_input.clear()
            password_input.send_keys(password)

            # Get and solve captcha
            captcha_base64 = get_captcha_image_base64(driver)
            if captcha_base64:
                captcha_text = solve_captcha_with_2captcha(captcha_base64)
                if captcha_text:
                    captcha_input = driver.find_element(By.ID, "captcha_code_reg")
                    captcha_input.clear()
                    captcha_input.send_keys(captcha_text)

                    # Click login
                    submit_button = driver.find_element(By.NAME, "submitLogin")
                    submit_button.click()
                    print("Login submitted.")

                    # Wait for the page to load and check for error message or logout button
                    time.sleep(5)  # Wait to ensure login attempt is processed

                    if is_login_successful(driver):
                        print("Login successful.")
                        return True
                    else:
                        print("Login failed. Retrying...")
                else:
                    print("Failed to solve captcha. Retrying...")
            else:
                print("Failed to get captcha image. Retrying...")
        
        except Exception as e:
            print(f"Error during login attempt {attempt}: {e}")

    print("Max login attempts reached. Login failed.")
    return False

def is_login_successful(driver):
    try:
        # Check if login was successful by looking for specific elements
        if "logout" in driver.page_source.lower() or "dashboard" in driver.page_source.lower():
            return True
        else:
            # Optionally, check for specific error messages
            error_message = driver.find_element(By.XPATH, "//div[contains(@class, 'error-message')]").text
            print(f"Login failed due to error: {error_message}.")
            return False
    except NoSuchElementException:
        return False

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
    except TimeoutException:
        print("Post-login popup not found or already closed.")

def book_appointment(driver):
    try:
        book_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Book Appointment"))
        )
        book_button.click()
        print("Clicked on 'Book Appointment'.")

        select_location_and_visa(driver)
        solve_post_booking_captcha(driver)
    except TimeoutException:
        print("Booking process timed out.")
    except Exception as e:
        print(f"Error during booking steps: {e}")

def select_location_and_visa(driver):
    try:
        location_select = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "valCenterLocationId"))
        )
        Select(location_select).select_by_visible_text("Quetta (Pakistan)")
        print("Selected Quetta location.")

        visa_select = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "valCenterLocationTypeId"))
        )
        Select(visa_select).select_by_visible_text("Legalisation")
        print("Selected Legalisation Visa.")

        app_type_dropdown = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "valAppointmentForMembers"))
        )
        select_individual_option(driver, app_type_dropdown)
    except TimeoutException:
        print("Error selecting location or visa type.")
    except Exception as e:
        print(f"Error during location and visa selection: {e}")

def select_individual_option(driver, app_type_dropdown):
    try:
        individual_option = app_type_dropdown.find_element(By.XPATH, ".//option[contains(text(), 'Individual')]")
        driver.execute_script("arguments[0].setAttribute('selected', 'selected')", individual_option)
        driver.execute_script("window.location.href = arguments[0].value", individual_option)
        print("Selected application type: Individual and navigated.")
    except Exception as e:
        print(f"Error selecting individual application type: {e}")

def solve_post_booking_captcha(driver):
    # Wait for the page to load after selecting the individual option
    WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.ID, "Imageid"))  # Wait for the captcha image to appear
        )
    try:
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
        print(f"Error during post-booking captcha solving: {e}")

def monitor_and_book_slot(driver):
    while True:
        try:
             # Find and click the date dropdown
            date_dropdown = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "valAppointmentDate"))
            )
            date_dropdown.click()
             # Find all the days with available slots
            available_slots = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//td[contains(@class, 'day') and contains(@class, 'label-available')]"))
            )
            if available_slots:
                    # Click the first available slot
                    available_slots[0].click()
                    print("Available slot selected. Checking for appointment type dropdown.")
                    
                    # Wait and retry mechanism for appointment type dropdown
                    appointment_type_selected = False
                    retries = 3
                    for _ in range(retries):
                        if select_appointment_type(driver):
                            appointment_type_selected = True
                            break
                        else:
                            print("Appointment type not available yet. Retrying...")
                            time.sleep(3)  # Wait before retrying
                    
                    if appointment_type_selected:
                        print("Appointment type selected successfully.")
                        break  # Exit the loop if the appointment type is selected
                    else:
                        print("Failed to select appointment type after multiple attempts. Retrying...")

            else:
                print("No available slots found. Retrying...")
                time.sleep(5)  # Wait before retrying to avoid rate limiting
                driver.refresh()
        except Exception as e:
            print(f"Error during slot monitoring: {e}")
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

        # Proceed to the payment page
        proceed_button = driver.find_element(By.ID, "valBookNow")
        proceed_button.click()
        print("Proceeding to the payment page...")

    except Exception as e:
        print(f"Error filling details or proceeding to payment: {str(e)}")

def make_payment(driver):
    try:
        # Enter Card Number
        card_number_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "cardNumber"))
        )
        card_number_field.clear()
        card_number_field.send_keys("4111111111111111")

        # Select Expiry Month
        expiry_month_dropdown = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@data-activates='select-options-eef6ca77-fbf4-eadd-0a90-dee7b31bf2bd']"))
        )
        expiry_month_dropdown.click()
        month_option = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='01']"))
        )
        month_option.click()

        # Select Expiry Year
        expiry_year_dropdown = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@data-activates='select-options-c4a3b2ba-117c-3036-090c-44b028317d7e']"))
        )
        expiry_year_dropdown.click()
        year_option = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='2025']"))
        )
        year_option.click()

        # Enter CVV Code
        cvv_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "ValidationCode"))
        )
        cvv_field.clear()
        cvv_field.send_keys("123")

        # Click Pay Button
        pay_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "btnPay"))
        )
        driver.execute_script("arguments[0].click();", pay_button)
        print("Payment submitted.")

        # Wait for response after payment
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'payment-success')]"))
        )
        print("Payment successful.")

    except TimeoutException:
        print("Payment failed due to timeout.")
    except NoSuchElementException:
        print("One or more elements not found during payment.")
    except Exception as e:
        print(f"Error during payment: {e}")

    # Optionally: Add a verification step to confirm payment
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'payment-confirmation')]"))
        )
        print("Payment confirmed.")
    except TimeoutException:
        print("Payment confirmation not found.")


def main():
    driver = setup_driver()
    driver.get("https://blsitalypakistan.com/")

    close_popup_if_present(driver)
    navigate_to_login(driver)

    email = "walees.wahab321@gmail.com"
    password = "Italianuni#123"

    if login(driver, email, password):
        close_post_login_popup(driver)
        book_appointment(driver)
        monitor_and_book_slot(driver)
        fill_details_and_proceed_to_payment(driver)
        make_payment(driver)
    else:
        print("Login failed. Terminating the process.")
    
    # Optionally, quit the driver
    # driver.quit()

if __name__ == "__main__":
    main()
