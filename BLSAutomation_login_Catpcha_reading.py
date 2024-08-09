from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import io
import requests
import base64

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

def login(driver, email, password):
    try:
        email_input = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, "//input[@placeholder='Enter Email']"))
        )
        email_input.send_keys(email)

        password_input = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, "//input[@placeholder='Enter Password']"))
        )
        password_input.send_keys(password)

        captcha_base64 = get_captcha_image_base64(driver)

        if captcha_base64:
            captcha_text = solve_captcha_with_2captcha(captcha_base64)

            if captcha_text:
                captcha_input = driver.find_element(By.ID, "captcha_code_reg")
                captcha_input.send_keys(captcha_text)

                submit_button = driver.find_element(By.NAME, "submitLogin")
                submit_button.click()
                print("Login attempted.")

                time.sleep(15)  # Increase sleep time to observe result
            else:
                print("Failed to get captcha text.")
        else:
            print("Failed to get captcha image.")

    except Exception as e:
        print("Error during login:", e)

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

def main():
    driver = setup_driver()

    try:
        driver.get("https://blsitalypakistan.com/")
        close_popup_if_present(driver)
        navigate_to_login(driver)

        # Check 2Captcha balance
        balance = check_balance()
        if balance > 0.1:  # Check if balance is sufficient
            login(driver, "walees.wahab321@gmail.com", "Italianuni#123")
        else:
            print("Insufficient balance for captcha solving.")
    finally:
        # Keep the browser open for manual work
        print("Browser is open for manual work. Close it when done.")
        input("Press Enter to close the browser...")  # Wait for user input
        # driver.quit()  # Ensure this line is commented out to keep the browser open

if __name__ == "__main__":
    main()
