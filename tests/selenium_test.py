from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import random

# ==========================================
# SMART HELPERS (Auto-clickers and fillers)
# ==========================================

def smart_fill(driver, possible_names, text, delay=0.15):
    for name in possible_names:
        try:
            element = driver.find_element(By.NAME, name)
            element.clear()
            for char in text:
                element.send_keys(char)
                time.sleep(delay)
            return True 
        except:
            continue 
    return False

def slow_scroll(driver, steps=6, pause=1.5):
    try:
        total_height = int(driver.execute_script("return document.body.scrollHeight"))
        for i in range(1, steps + 1):
            scroll_position = (total_height / steps) * i
            driver.execute_script(f"window.scrollTo(0, {scroll_position});")
            time.sleep(pause)
    except:
        pass

def click_by_text(driver, text_to_find):
    try:
        element = driver.find_element(By.XPATH, f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text_to_find.lower()}')]")
        element.click()
        return True
    except:
        return False

# ==========================================
# FULL TEST EXECUTION
# ==========================================

test_username = f"tamanna_{random.randint(1000, 9999)}"
test_password = "Secure@Password2026!"

driver = webdriver.Chrome()

try:
    # --- 1. REGISTRATION & LOGIN ---
    print("\n[1/8] Registering...")
    driver.get("http://127.0.0.1:5000/register") 
    driver.maximize_window()
    time.sleep(3)
    
    smart_fill(driver, ["username", "user_name", "uname"], test_username)
    smart_fill(driver, ["password", "pass", "pwd"], test_password)
    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    time.sleep(4)

    print("[2/8] Logging In...")
    driver.get("http://127.0.0.1:5000/login")
    time.sleep(3)
    smart_fill(driver, ["username", "user_name", "uname"], test_username)
    smart_fill(driver, ["password", "pass", "pwd"], test_password)
    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    time.sleep(5)

    # --- 2. PROFILE COMPLETION ---
    print("[3/8] Navigating to Profile...")
    try:
        driver.find_element(By.PARTIAL_LINK_TEXT, "Profile").click()
    except:
        driver.get("http://127.0.0.1:5000/profile") 
    time.sleep(4)

    print("[4/8] Aggressively Filling Profile Data...")
    all_inputs = driver.find_elements(By.TAG_NAME, "input")
    for input_box in all_inputs:
        try:
            if input_box.get_attribute("type") in ["text", "email"]:
                input_box.clear()
                input_box.send_keys("Demo Data")
                time.sleep(0.1)
        except:
            pass 
            
    time.sleep(2)
    print("Saving Profile...")
    try:
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
    except:
        driver.execute_script("document.forms[0].submit();")
    time.sleep(4)

    # --- 3. THE JOBFIT ENGINE SEQUENCE ---
    print("[5/8] Opening JobFit Engine...")
    if not click_by_text(driver, "jobfit engine"):
        try:
            driver.find_element(By.PARTIAL_LINK_TEXT, "JobFit").click()
        except:
            driver.get("http://127.0.0.1:5000/jobs") 
    time.sleep(4)

    print("[6/8] Clicking View Details & Predict...")
    click_by_text(driver, "view details")
    time.sleep(3)
    click_by_text(driver, "predict")
    time.sleep(3)
    
    print("Clicking Initialize Engine...")
    click_by_text(driver, "initialize engine")
    time.sleep(4)

    print("Filling Random Number Data for Prediction...")
    number_inputs = driver.find_elements(By.XPATH, "//input[@type='number']")
    for num_box in number_inputs:
        try:
            num_box.clear()
            random_val = str(random.randint(75, 99)) 
            for char in random_val:
                num_box.send_keys(char)
                time.sleep(0.2)
        except:
            pass
            
    smart_fill(driver, ["aptitude", "score", "percentage", "marks"], str(random.randint(75, 99)))
    time.sleep(3)

    # --- 4. THE GRAND FINALE: AI ANALYSIS ---
    print("[7/8] Initiating AI Analysis Server...")
    driver.find_element(By.XPATH, "//button[contains(text(), 'Run AI Analysis Server')]").click()
    
    print("Waiting for the Radar Loader to finish (Awesome 10-second pause for video!)...")
    time.sleep(10) 
    
    print("Scrolling to reveal prediction results...")
    slow_scroll(driver, steps=5, pause=2) 
    time.sleep(5)

    # --- 5. TRAINER & RESUME PAGES ---
    print("[8/8] Visiting AI Trainer & Resume Pages...")
    
    # Force Navigation directly to avoid any dashboard/sidebar clicking issues
    driver.get("http://127.0.0.1:5000/trainer")
    time.sleep(4)
    slow_scroll(driver, steps=3, pause=1)

    driver.get("http://127.0.0.1:5000/build_resume") 
    time.sleep(4)
    slow_scroll(driver, steps=3, pause=1)

    # --- 6. LOGOUT ---
    print("Logging out to return to homepage...")
    driver.get("http://127.0.0.1:5000/logout")
    time.sleep(4)

    print("\n================================================")
    print("SUCCESS! Test complete. Stop your recording now!")
    print("================================================")

except Exception as e:
    print(f"\n--- SCRIPT ENCOUNTERED AN ERROR --- \nDetails: {e}")

finally:
    time.sleep(5)
    driver.quit()