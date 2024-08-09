from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
import requests
import base64
import io
import time

def setup_driver():
    chrome_driver_path = r'C:\Users\wwwre\OneDrive\Desktop\BLSautomation\chromedriver.exe'
    service = Service(executable_path=chrome_driver_path)
    options = webdriver.ChromeOptions()
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

def resize_image(image_data, max_size=(400, 100)):
    with Image.open(io.BytesIO(image_data)) as img:
        img.thumbnail(max_size, Image.LANCZOS)  # Use LANCZOS for resizing
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=80)  # Adjust quality if needed
        return buffer.getvalue()

def solve_captcha_with_truecaptcha(image_data):
    url = 'https://api.apitruecaptcha.org/one/gettext'
    
    # Resize the image data
    resized_image_data = resize_image(image_data)
    
    # Encode image data to base64
    encoded_string = base64.b64encode(resized_image_data).decode('ascii')
    
    data = {
        'userid': 'rehanasif3454@gmail.com',
        'apikey': 'kYFFYtxjsjjHEDQm0wEq',
        'data': encoded_string
    }
    
    response = requests.post(url=url, json=data)
    
    # Log the full API response for debugging
    try:
        result = response.json()
        print("TrueCaptcha API response:", result)
        captcha_text = result.get('result', '').strip()
        return captcha_text
    except Exception as e:
        print("Failed to decode JSON response or retrieve captcha text:", e)
        return None

def read_captcha(driver):
    try:
        captcha_img_element = driver.find_element(By.ID, "Imageid")
        captcha_img_src = captcha_img_element.get_attribute("src")
        response = requests.get(captcha_img_src)
        captcha_image_data = response.content
        
        # Solve captcha using TrueCaptcha
        captcha_text = solve_captcha_with_truecaptcha(captcha_image_data)
        print(f"Captcha text: {captcha_text}")

        return captcha_text
    except Exception as e:
        print("Error reading captcha:", e)
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

        captcha_text = read_captcha(driver)

        if captcha_text:
            captcha_input = driver.find_element(By.ID, "captcha_code_reg")
            captcha_input.send_keys(captcha_text)

            submit_button = driver.find_element(By.NAME, "submitLogin")
            submit_button.click()
            print("Login attempted.")

            time.sleep(3)
        else:
            print("Failed to read captcha.")

    except Exception as e:
        print("Error during login:", e)

def main():
    driver = setup_driver()

    try:
        driver.get("https://blsitalypakistan.com/")
        close_popup_if_present(driver)
        navigate_to_login(driver)
        login(driver, "walees.wahab321@gmail.com", "Italianuni#123")
        time.sleep(5)

    finally:
        # Keep the browser open for manual work
        print("Browser is open for manual work. Close it when done.")
        # driver.quit()  # Comment out this line to keep the browser open

if __name__ == "__main__":
    main()
