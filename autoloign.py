from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
import pytesseract
import time
import io
import requests
import cv2
import numpy as np

# Configure pytesseract path if not added to PATH
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Update this path if needed

def setup_driver():
    chrome_driver_path = r'C:\Users\wwwre\OneDrive\Desktop\BLSautomation\chromedriver.exe'  # Update this path if needed
    service = Service(executable_path=chrome_driver_path)
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless')  # Uncomment to run headless if you do not need a browser window
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

def preprocess_image(image):
    img = np.array(image.convert('RGB'))  # Ensure image is in RGB format
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    # Increase contrast
    contrast = cv2.convertScaleAbs(gray, alpha=2.0, beta=0)
    
    # Apply Gaussian Blur to reduce noise
    blurred = cv2.GaussianBlur(contrast, (5, 5), 0)
    
    # Apply adaptive thresholding
    binary = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
    
    # Use morphological operations to enhance character structure
    kernel = np.ones((2, 2), np.uint8)
    binary = cv2.dilate(binary, kernel, iterations=1)
    binary = cv2.erode(binary, kernel, iterations=1)
    
    # Convert back to PIL Image for pytesseract
    processed_image = Image.fromarray(binary)
    
    return processed_image

def read_captcha(driver):
    try:
        captcha_img_element = driver.find_element(By.ID, "Imageid")
        captcha_img_src = captcha_img_element.get_attribute("src")

        response = requests.get(captcha_img_src)
        if response.status_code == 200:
            captcha_image = Image.open(io.BytesIO(response.content))

            # Debug: Save or show the image to verify its content
            captcha_image.save("captcha_debug.png")  # Save the image to verify its content
            captcha_image.show()  # Display the image if possible
            
            processed_image = preprocess_image(captcha_image)
            
            # Debug: Save or show the processed image
            processed_image.save("processed_captcha_debug.png")  # Save the processed image
            processed_image.show()  # Display the processed image if possible
            
            # Use pytesseract to perform OCR on the captcha image
            custom_config = r'--oem 3 --psm 6 -l eng'
            captcha_text = pytesseract.image_to_string(processed_image, config=custom_config)
            
            # Debug: Print the raw OCR output
            print(f"Raw OCR Output: {captcha_text}")

            captcha_text = ''.join(filter(str.isdigit, captcha_text))  # Extract only digits
            print(f"Extracted Captcha Text: {captcha_text}")

            return captcha_text
        else:
            print("Failed to download captcha image.")
            return None
    except Exception as e:
        print("Error reading captcha:", e)
        return None


def login(driver, email, password):
    try:
        # Input email
        email_input = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, "//input[@placeholder='Enter Email']"))
        )
        email_input.send_keys(email)

        # Input password
        password_input = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, "//input[@placeholder='Enter Password']"))
        )
        password_input.send_keys(password)

        # Read captcha text
        captcha_text = read_captcha(driver)
        print(f"Extracted Captcha Text: {captcha_text}")

        if captcha_text:
            # Input captcha
            captcha_input = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.ID, "captcha_code_reg"))
            )
            captcha_input.clear()  # Clear the input field before sending keys
            captcha_input.send_keys(captcha_text)

            # Click submit button
            submit_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.NAME, "submitLogin"))
            )
            submit_button.click()
            print("Login attempted.")

            # Optional: Wait to see the result of the login attempt
            time.sleep(5)  # Adjust sleep time if needed
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
        time.sleep(5)  # Adjust sleep time if needed
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
