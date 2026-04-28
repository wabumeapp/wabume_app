# Standard Library
import os
import time
import math
import uuid
import random
import threading
import winsound

# Third-party libraries
import requests
import openpyxl
import pyperclip
from flask import session

# Selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# WebDriver Manager
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.driver_cache import DriverCacheManager

# UI
import tkinter as tk
from tkinter import messagebox, filedialog, ttk

SESSION_ID = None
USER_ID = None
DEVICE_ID = str(uuid.uuid4())

# --- Paths and Settings ---
USER_DATA_DIR = os.path.join(os.getcwd(), "whatsapp_bot_data")
LOG_FILE = "sent_numbers.log"

# --- WhatsApp Colors & Theme ---
PRIMARY_DARK = "#075E54"
PRIMARY_COLOR = "#128C7E"
SECONDARY_COLOR = "#25D366"
ACCENT_COLOR = "#1AB5D0"

BACKGROUND_COLOR = "#F0F2F5"
BG_DARK = "#0b0f14"       
CARD_DARK = "#111827"      
INPUT_BG = "#1f2937"       

CARD_COLOR = "#FFFFFF"
TEXT_COLOR = "#3B4A54"
LIGHT_TEXT = "#667781"

BORDER_COLOR = "#E0E0E0"

ERROR_COLOR = "#D21B2A"
WARNING_COLOR = "#EE0707"
SUCCESS_COLOR = "#4CAF50"

# --- Custom MessageBox Function ---
def show_custom_message(title, message, msg_type="info"):
    """Display a custom styled message box"""
    dialog = tk.Toplevel(root)
    dialog.title(title)
    dialog.configure(bg=BACKGROUND_COLOR)
    dialog.resizable(False, False)
    dialog.transient(root)
    dialog.grab_set()
    
    # --- Dynamic height (auto resize) ---
    lines = message.count("\n") + len(message) // 60
    height = 220 + lines * 12
    if height > 480:
        height = 480  # Limit window height
    dialog.geometry(f"500x{height}")

    # Center the dialog
    dialog.update_idletasks()
    x = root.winfo_x() + (root.winfo_width() - dialog.winfo_width()) // 2
    y = root.winfo_y() + (root.winfo_height() - dialog.winfo_height()) // 2
    dialog.geometry(f"+{x}+{y}")
    
    # Set colors based on message type
    if msg_type == "error":
        color = ERROR_COLOR
        icon = "❌"
    elif msg_type == "warning":
        color = WARNING_COLOR
        icon = "⚠"
    elif msg_type == "success":
        color = SUCCESS_COLOR
        icon = "✅"
    else:  # info
        color = ACCENT_COLOR
        icon = "ℹ"
    
    # Main container with rounded corners
    main_container = tk.Frame(dialog, bg=CARD_COLOR, padx=0, pady=0, relief="raised", bd=0)
    main_container.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Header with accent color
    header = tk.Frame(main_container, height=50, bg=color)
    header.pack(fill="x", expand=True)
    
    # Icon and title
    icon_label = tk.Label(header, text=icon, font=("Segoe UI", 18), bg=color, fg="white")
    icon_label.place(x=20, y=12)
    
    title_label = tk.Label(header, text=title, font=("Segoe UI", 14, "bold"), bg=color, fg="white")
    title_label.place(x=60, y=12)
    
    # Message content
    msg_frame = tk.Frame(main_container, bg=CARD_COLOR, padx=20, pady=20)
    msg_frame.pack(fill="both", expand=True)
    
    message_label = tk.Label(msg_frame, text=message, font=("Segoe UI", 11), 
                            bg=CARD_COLOR, fg=TEXT_COLOR, wraplength=380, justify="left")
    message_label.pack(fill="both", expand=True)

    # OK button
    btn_frame = tk.Frame(msg_frame, bg=CARD_COLOR)
    btn_frame.pack(fill="both", expand=True, pady=(15, 5))
    
    ok_btn = tk.Button(btn_frame, text="OK", command=dialog.destroy, 
                      bg=color, fg="white", font=("Segoe UI", 10, "bold"),
                      activebackground=color, activeforeground="white",
                      bd=0, padx=25, pady=6, cursor="hand2", relief="raised")
    ok_btn.pack(fill="both", expand=True)
    
    dialog.wait_window(dialog)

# --- Custom MessageBox Function for Partial Success only---
def show_partial_success_message(title, message):
    """Display a custom styled message box with centered text, scrollable content, and large OK button."""
    dialog = tk.Toplevel(root)
    dialog.title(title)
    dialog.configure(bg=BACKGROUND_COLOR)
    dialog.resizable(False, False)
    dialog.transient(root)
    dialog.grab_set()

    # --- Dynamic height (auto resize) ---
    lines = message.count("\n") + len(message) // 60
    height = 220 + lines * 12
    if height > 480:
        height = 480  # Limit window height
    dialog.geometry(f"500x{height}")

    # Center the dialog
    dialog.update_idletasks()
    x = root.winfo_x() + (root.winfo_width() - dialog.winfo_width()) // 2
    y = root.winfo_y() + (root.winfo_height() - dialog.winfo_height()) // 2
    dialog.geometry(f"+{x}+{y}")

    # Colors and icon
    color = ERROR_COLOR
    icon = "❌"

    # Header frame
    header = tk.Frame(dialog, bg=color, height=60)
    header.pack(fill="x")
    header.pack_propagate(False)

    icon_label = tk.Label(header, text=icon, font=("Segoe UI", 22), bg=color, fg="white")
    icon_label.pack(side="left", padx=15)

    title_label = tk.Label(header, text=title, font=("Segoe UI", 16, "bold"), bg=color, fg="white")
    title_label.pack(side="left", padx=5, pady=10)

    # Message frame with scrollable Text
    msg_frame = tk.Frame(dialog, bg=CARD_COLOR)
    msg_frame.pack(fill="both", expand=True, padx=15, pady=15)

    text_area = tk.Text(msg_frame, font=("Segoe UI", 12), bg=CARD_COLOR, fg=TEXT_COLOR,
                        wrap="word", height=8, relief="solid", bd=1)
    text_area.insert("1.0", message)
    text_area.config(state="disabled", padx=10, pady=10)
    text_area.pack(side="left", fill="both", expand=True)

    scrollbar = ttk.Scrollbar(msg_frame, orient="vertical", command=text_area.yview)
    scrollbar.pack(side="right", fill="y")
    text_area.configure(yscrollcommand=scrollbar.set)

    # Center text horizontally
    text_area.tag_configure("center", justify="center")
    text_area.tag_add("center", "1.0", "end")

    dialog.wait_window(dialog)

# --- Custom Confirmation MessageBox Function ---
def show_confirmation_message(title, message):
    """Custom confirmation window with OK and Cancel buttons"""
    dialog = tk.Toplevel(root)
    dialog.title(title)
    dialog.configure(bg=BACKGROUND_COLOR)
    dialog.resizable(False, False)
    dialog.transient(root)
    dialog.grab_set()

    # --- Dynamic height (auto resize) ---
    lines = message.count("\n") + len(message) // 60
    height = 220 + lines * 12
    if height > 480:
        height = 480  # Limit window height
    dialog.geometry(f"500x{height}")

    # Center the dialog
    dialog.update_idletasks()
    x = root.winfo_x() + (root.winfo_width() - dialog.winfo_width()) // 2
    y = root.winfo_y() + (root.winfo_height() - dialog.winfo_height()) // 2
    dialog.geometry(f"+{x}+{y}")

    color = ACCENT_COLOR  

    # Main container
    main_container = tk.Frame(dialog, bg=CARD_COLOR, padx=0, pady=0, relief="raised", bd=0)
    main_container.pack(fill="both", expand=True, padx=10, pady=10)

    # Header
    header = tk.Frame(main_container, height=50, bg=color)
    header.pack(fill="x", expand=True)

    # Title
    title_label = tk.Label(header, text=title, font=("Segoe UI", 14, "bold"), bg=color, fg="white")
    title_label.place(relx=0.5, rely=0.5, anchor="center")

    # Message content
    msg_frame = tk.Frame(main_container, bg=CARD_COLOR, padx=20, pady=20)
    msg_frame.pack(fill="both", expand=True)
    message_label = tk.Label(msg_frame, text=message, font=("Segoe UI", 11),
                             bg=CARD_COLOR, fg=TEXT_COLOR, wraplength=380, justify="left")
    message_label.pack(fill="both", expand=True)

    result = {"value": False}  # store the choice result

    # Buttons
    btn_frame = tk.Frame(msg_frame, bg=CARD_COLOR)
    btn_frame.pack(fill="both", expand=True, pady=(15, 5))

    def on_ok():
        result["value"] = True
        dialog.destroy()

    def on_cancel():
        result["value"] = False
        dialog.destroy()

    ok_btn = tk.Button(btn_frame, text="OK", command=on_ok,
                       bg=color, fg="white", font=("Segoe UI", 10, "bold"),
                       activebackground=color, activeforeground="white",
                       bd=0, padx=25, pady=6, cursor="hand2")
    ok_btn.pack(side="left", fill="both", expand=True, padx=(0,5))

    cancel_btn = tk.Button(btn_frame, text="Cancel", command=on_cancel,
                           bg="#D3D3D3", fg="black", font=("Segoe UI", 10, "bold"),
                           activebackground="#C0C0C0", activeforeground="black",
                           bd=0, padx=25, pady=6, cursor="hand2")
    cancel_btn.pack(side="left", fill="both", expand=True, padx=(5,0))

    dialog.wait_window(dialog)
    return result["value"]

# --- CSS Selector Helpers & Selenium Functions ---
def wait_css(driver, css, timeout=15, clickable=False, visible=False):
    if clickable:
        return WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.CSS_SELECTOR, css)))
    if visible:
        return WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((By.CSS_SELECTOR, css)))
    return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.CSS_SELECTOR, css)))

def is_valid_number(num):
    num = str(num).strip()
    if num.startswith('+') and num[1:].isdigit():
        return True
    elif num.isdigit() and 8 <= len(num) <= 15:
        return True
    return False

def search_and_select_number(driver, number):
    try:
        search_box = wait_css(driver, 'div[contenteditable="true"][data-tab="3"]', timeout=20, visible=True)
        search_box.click()
        search_box.send_keys(Keys.CONTROL, "a")
        search_box.send_keys(Keys.DELETE)
        search_box.send_keys(number)
        time.sleep(0.4)
        first_result = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="gridcell"] span[dir="auto"]'))
        )
        first_result.click()
        time.sleep(0.3)
        return True
    except Exception as e:
        print(f"[search_and_select_number] {e}")
        return False

def send_message_to_current_chat(driver, message, retries=3):
    """
    Send message to the current WhatsApp chat with maximum protection from WhatsApp UI changes.
    Uses Clipboard for pasting to avoid relying on send button or data-tab attributes.
    """
    for attempt in range(retries):
        try:
            # نحاول نلاقي الـ chat input بطريقة عامة
            chat_boxes = driver.find_elements(By.CSS_SELECTOR, 'div[contenteditable="true"]')
            
            # غالبًا العنصر الصحيح يكون داخل footer أو في آخر الـ chat_boxes
            msg_box = None
            for box in reversed(chat_boxes):
                if box.is_displayed():
                    msg_box = box
                    break
            
            if not msg_box:
                raise NoSuchElementException("No visible contenteditable found")
            
            msg_box.click()
            time.sleep(0.1)
            
            # الصق الرسالة من Clipboard
            pyperclip.copy(message)
            msg_box.send_keys(Keys.CONTROL, 'v')
            time.sleep(0.15)
            msg_box.send_keys(Keys.ENTER)
            time.sleep(0.25)
            
            return True  # نجاح الإرسال
        except Exception as e:
            print(f"[send_message_attempt {attempt+1}] {e}")
            time.sleep(0.8)  # وقت قصير قبل المحاولة التالية
    return False  # فشل بعد retries


def send_file(driver, file_path):
    try:
        print(">>> Clicking Attach...")

        # 1️⃣ اضغط زر المشبك Attach
        attach_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="Attach"]'))
        )
        attach_btn.click()
        time.sleep(1)

        # 2️⃣ حمل الملف عبر input[type=file]
        print(">>> Selecting file input...")
        file_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="file"]'))
        )
        file_input.send_keys(file_path)

        # ننتظر المعاينة
        time.sleep(2.5)

        print(">>> Searching for SEND button...")

        # 3️⃣ لائحة كل الأزرار المحتملة للإرسال
        send_selectors = [
            'span[data-icon="send"]',
            'span[data-icon="send-light"]',
            'button[aria-label="Send"]',
            'div[data-testid="send"]',
            'button[data-testid="send"]',
            'div[role="button"][aria-label="Send"]',
            'div[aria-label="Send"]',
        ]

        send_btn = None

        # 4️⃣ جرّب كل Selector لحد ما تلاقي زر ظاهر وقابل للنقر
        for selector in send_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for el in elements:
                    if el.is_displayed() and el.is_enabled():
                        send_btn = el
                        break
                if send_btn:
                    break
            except:
                pass

        if not send_btn:
            raise Exception(">>> Send button not found!")

        # 5️⃣ اضغط الإرسال
        send_btn.click()
        print(">>> File sent!")

        time.sleep(2)
        return True

    except Exception as e:
        print(f"[send_file ERROR] {e}")
        return False


    
# --- Load Numbers from Excel ---
def load_numbers_from_excel():
    file_path = filedialog.askopenfilename(title="Select Excel File", filetypes=[("Excel files", ".xlsx"), ("All files", ".*")])
    if not file_path:
        return
    try:
        wb = openpyxl.load_workbook(file_path)
        sheet = wb.active
        numbers = [str(row[0]).strip() for row in sheet.iter_rows(min_row=1, values_only=True) if row[0]]
        numbers_text.delete("1.0", tk.END)
        numbers_text.insert(tk.END, "\n".join(numbers))
        show_custom_message("Success", f"Loaded {len(numbers)} numbers from Excel", "success")
    except Exception as e:
        show_custom_message("Error", f"Failed to load Excel file:\n{e}", "error")

# --- Initialize Browser ---
def init_driver():

    # Kill any existing chromedriver
    try:
        os.system("taskkill /im chromedriver.exe /f")
        time.sleep(2)
    except:
        pass

    # create folder if not exists
    if not os.path.exists(USER_DATA_DIR):
        os.makedirs(USER_DATA_DIR)
        
    # --- Chrome Options ---
    options = webdriver.ChromeOptions()
    options.add_argument(f"--user-data-dir={USER_DATA_DIR}")
    options.add_argument("--profile-directory=Default")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-extensions")
    options.add_argument("--start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--disable-blink-features=AutomationControlled")

    # --- Launch Chrome with the correct driver ---
    # webdriver-manager automatically detects your Chrome version and downloads the matching chromedriver.
    # So you don’t need to manually match versions; this is the easiest and safest way.

    try:
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
    except Exception as e:
        print("⚠️ Profile may be corrupted, creating fresh profile...")
        # حذف الفولدر القديم
        try:
            import shutil
            shutil.rmtree(USER_DATA_DIR)
            os.makedirs(USER_DATA_DIR)
        except:
            pass

        # إعادة launch مع فولدر جديد
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )

    return driver

# --- Save Sent Messages Log ---
def log_message(phone, message):
    """Logs each sent message into DetailsGage with date, time, number, and content"""
    from datetime import datetime
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")

    if "messages" not in session:
        session["messages"] = []

    session["messages"].append({
        "date": date_str,
        "time": time_str,
        "phone": phone,
        "message": message
    })

# --- Progress Bar Helper (Smooth & Responsive) ---
def update_progress_bar_smoothly(current_value, target_value, duration=0.5):
    """Increment the progress bar smoothly from current_value to target_value"""
    steps = int(duration / 0.02)  # number of steps (every 20ms)
    increment = (target_value - current_value) / steps
    for _ in range(steps):
        current_value += increment
        progress_bar['value'] = current_value
        root.update_idletasks()
        time.sleep(0.02)
    progress_bar['value'] = target_value   # ensure final value
    root.update_idletasks()

# --- Info Label Control ---
def show_info_message(msg, duration=3000):
    info_label.config(text=msg)          # display the text
    root.update_idletasks()             # refresh UI immediately
    root.after(duration, lambda: info_label.config(text=""))   # clear text after duration

# --- Function to update visibility of inputs ---
def update_inputs_visibility():
    try:
        # عد الأرقام الموجودة
        numbers_list = [num.strip() for num in numbers_text.get("1.0", tk.END).splitlines() if num.strip()]
        n = len(numbers_list)
        selected_mode = mode_var.get()  # Radio Button variable

        if n > 200:
            # --- Safe Mode: كل Radios معطلة، Inputs مخفية ---
            rb_manual.config(state="disabled")
            rb_batch.config(state="disabled")
            rb_auto.config(state="disabled")

            delay_container.pack_forget()
            batch_size_container.pack_forget()
            pause_container.pack_forget()

            auto_distribute_label.config(
                text=f"⚠ Safe Sending Mode Activated Automatically.\n"
                     f"200 messages per batch over 16 hours. Inputs disabled.",
                fg="red"
            )
            auto_distribute_label.pack(anchor="w", padx=25)

        else:
            # --- Radios مفعلة ---
            rb_manual.config(state="normal")
            rb_batch.config(state="normal")
            rb_auto.config(state="normal")

            # ضبط الـ label للشروحات العامة
            if selected_mode == "manual":
                delay_container.pack(fill="x", padx=25, pady=2)
            else:
                delay_container.pack_forget()

            if selected_mode == "batch":
                batch_size_container.pack(fill="x", padx=25, pady=2)
                pause_container.pack(fill="x", padx=25, pady=2)
                batch_info_container.pack(fill="x", padx=25, pady=2)
            else:
                batch_size_container.pack_forget()
                pause_container.pack_forget()
                batch_info_container.pack_forget()

            if selected_mode == "auto":
                auto_distribute_label.config(
                    text="🔁 If activated, messages will be automatically distributed throughout the day.\n",
                    fg="gray"
                )
                auto_distribute_label.pack(anchor="w", padx=25)
            else:
                # إخفاء label التوزيع اليومي إذا لم يكن Auto
                auto_distribute_label.config(text="")
                auto_distribute_label.pack_forget()

    except Exception as e:
        print(f"[update_inputs_visibility] {e}")


# --- toggle function ---
def toggle_sending():
    global is_sending
    is_sending = not is_sending
    if is_sending:
        play_stop_button.config(text="⛔ Stop", bg="black", fg="white")
        show_custom_message("Resumed", "Message sending is now active again.")
    else:
        play_stop_button.config(text="▶ Play", bg="#ff8c00", fg="white")
        show_custom_message("Paused", "Message sending has been paused.")

# --- Main Sending Function ---
def send_messages(): 
    numbers_raw = numbers_text.get("1.0", tk.END).strip()
    message = message_entry.get("1.0", tk.END).strip()
    file_path = file_entry.get().strip()

    if not numbers_raw:
        show_custom_message("Warning", "Please enter at least one phone number", "warning")
        return
    
    if not message and not file_path:
        show_custom_message("Warning", "Please enter a message or select a file to send", "warning")
        return

    numbers_list = [num.strip() for num in numbers_raw.splitlines() if num.strip()]
    valid_numbers = [n for n in numbers_list if is_valid_number(n)]
    if not valid_numbers:
        show_custom_message("Warning", "No valid phone numbers found", "warning")
        return

    n = len(valid_numbers)
    selected_mode = mode_var.get()  # "manual", "auto", "batch"

    # --- Safe Mode for >200 numbers ---
    if n > 200:
        delay_time = 57600 / 200  # 16 hours / 200 messages
        delay_minutes = round(delay_time / 60, 1)
        total_days = math.ceil(n / 200)
        show_custom_message(
            "Safe Sending Mode",
            f"✅ Safe sending mode is activated.\n"
            f"200 messages will be sent over 16 hours, one every {delay_minutes} minutes.\n"
            f"Next batch starts automatically after 8 hours.\n\n"
            f"Total numbers: {n}\n"
            f"Days needed: {total_days}"
        )
        # لا نستخدم أي مدخلات
        selected_mode = "safe"
    else:
        # --- Handle each mode ---
        if selected_mode == "manual":
            try:
                delay_time = float(delay_entry.get())
                if delay_time < 2:
                    show_custom_message(
                        "Warning",
                        "Minimum delay is 2 seconds to protect your account.",
                        "warning"
                    )
                    return
            except ValueError:
                show_custom_message("Warning", "Please enter a valid number for the delay.", "warning")
                return

            show_custom_message(
                "Manual Delay",
                f"⏱ Messages will be sent with a delay of {delay_time} seconds between each message."
            )

        elif selected_mode == "auto":
            delay_time = 86400 / n  # 24 hours / number of numbers
            delay_minutes = round(delay_time / 60, 1)
            show_custom_message(
                "Messages Distribution Over the Day",
                f"🔔 A message will be sent approximately every {delay_minutes} minutes.\n"
                f"Total numbers: {n}\nFull duration: 24 hours."
            )

        elif selected_mode == "batch":
            try:
                batch_size = int(batch_size_entry.get())
                pause_hours = float(pause_entry.get())

                if batch_size <= 0 or pause_hours <= 0:
                    show_custom_message("Warning", "Please enter valid numbers for batch size and pause hours.", "warning")
                    return

                total_batches = math.ceil(n / batch_size)
                delay_time = 2  # delay between messages inside batch
                batch_delay = pause_hours * 60

                show_custom_message(
                    "Batch Sending With Pause",
                    f"✅ Batch sending mode is activated.\n"
                    f"Batch size: {batch_size} numbers\n"
                    f"Pause after each batch: {pause_hours} hour(s)\n"
                    f"⏱ Delay between numbers inside a batch: {delay_time} seconds\n\n"
                    f"📦 Total batches: {total_batches}\n"
                    f"📨 Total numbers: {n}"
                )
            except ValueError:
                show_custom_message("Warning", "Please enter valid numbers for batch size and pause hours.", "warning")
                return
        else:
            show_custom_message("Warning", "Please select a sending mode.", "warning")
            return

    # --- Confirmation ---
    if not show_confirmation_message(
        "Confirmation",
        "Are you sure you want to send the messages?\nClick OK to start sending."
    ):
        return

    # --- Initialize Browser ---
    try:
        driver = init_driver()
        driver.get("https://web.whatsapp.com")
        show_custom_message("Scan QR", "Please scan the WhatsApp QR code then click OK")
        
        print("⏳ Waiting for WhatsApp to fully load...")
        WebDriverWait(driver, 120).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        # تأكيد إضافي
        time.sleep(10)
        print("✅ WhatsApp fully ready")

        if not show_confirmation_message("Ready to Start", "WhatsApp is loaded.\nClick OK to start sending messages."):
            driver.quit()
            return
    except Exception as e:
        show_custom_message("Error", f"Failed to start browser:\n{str(e)}", "error")
        return

    # --- Sending Loop ---
    progress_bar['maximum'] = len(valid_numbers)
    progress_bar['value'] = 0
    root.update_idletasks()
    failed_numbers = []
    sent_numbers = []
    global is_sending
    is_sending = True  # بداية الإرسال
    play_stop_button.config(state="normal", text="⛔ Stop", bg="black", fg="white")  # تفعيل الزر عند الضغط على Start

    for i, num in enumerate(valid_numbers):

        # ⛔⛔ STOP BUTTON CHECK HERE ⛔⛔
        while not is_sending:
            root.update()
            time.sleep(0.5)  # انتظر حتى المستخدم يضغط PLAY

        try:
            print(f"Processing number {i+1}/{len(valid_numbers)}: {num}")
            url = f"https://web.whatsapp.com/send?phone={num}"
            driver.get(url)
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[contenteditable="true"][data-tab="10"]'))
            )
            time.sleep(0.5)
            time.sleep(5)

            if message:
                if not send_message_to_current_chat(driver, message):
                    failed_numbers.append(num)
                    continue
            if file_path:
                if not send_file(driver, file_path):
                    failed_numbers.append(num)
                    continue

            sent_numbers.append(num)
            last_number_label.config(text=f"Last number sent: {num}")
            update_progress_bar_smoothly(progress_bar['value'], i + 1)
            progress_label.config(text=f"{i+1}/{len(valid_numbers)}")
            root.update_idletasks()

            # --- Batch Delay ---
            if selected_mode == "batch" and (i + 1) % batch_size == 0 and i + 1 < len(valid_numbers):
                show_info_message(f"Messages for batch {(i + 1) // batch_size} sent. Waiting {batch_delay} seconds...")
                root.update_idletasks()
                time.sleep(batch_delay)

                for _ in range(int(batch_delay * 10)):
                    if not is_sending:
                        break
                    time.sleep(0.1)
                    root.update()

            else:
                for _ in range(int(delay_time * 10)):  # كل 100ms
                    if not is_sending:
                        break
                    time.sleep(0.1)
                    root.update()


        except Exception as e:
            print(f"Error with {num}: {str(e)}")
            failed_numbers.append(num)
            continue
    play_stop_button.config(state="disabled", text="⛔ Stop", bg="black", fg="white")
    is_sending = False
    driver.quit()
    winsound.Beep(1000, 300)

    if failed_numbers:
        failed_msg = f"Sent to {len(sent_numbers)} numbers successfully.\nFailed: {len(failed_numbers)} numbers:\n\n" + "\n".join(failed_numbers)
        show_partial_success_message("Partial Success", failed_msg)
    else:
        show_custom_message("Success", f"All messages sent successfully ({len(valid_numbers)} messages)", "success")


particles = []
# ---------------- PARTICLES ----------------
def create_particles(canvas, w, h, count=25):
    global particles

    for _ in range(count):
        x = random.randint(0, w)
        y = random.randint(0, h)

        dot = canvas.create_oval(x, y, x+3, y+3, fill="#25D366", outline="")

        particles.append({
            "id": dot,
            "x": x,
            "y": y,
            "dx": random.uniform(-0.4, 0.4),
            "dy": random.uniform(-0.4, 0.4)
        })


def animate(canvas, w, h):
    for p in particles:
        p["x"] += p["dx"]
        p["y"] += p["dy"]

        if p["x"] <= 0 or p["x"] >= w:
            p["dx"] *= -1
        if p["y"] <= 0 or p["y"] >= h:
            p["dy"] *= -1

        canvas.coords(p["id"], p["x"], p["y"], p["x"]+3, p["y"]+3)

    canvas.after(30, lambda: animate(canvas, w, h))


# ---------------- LOGIN ----------------
def show_login():
    win = tk.Toplevel(root)
    win.title("Verification")
    win.configure(bg=BG_DARK)

    w, h = 500, 380

    win.update_idletasks()

    # center
    x = (win.winfo_screenwidth() // 2) - (w // 2)
    y = (win.winfo_screenheight() // 2) - (h // 2)
    win.geometry(f"{w}x{h}+{x}+{y}")

    # background
    canvas = tk.Canvas(win, bg=BG_DARK, highlightthickness=0)
    canvas.place(relwidth=1, relheight=1)

    create_particles(canvas, w, h)
    animate(canvas, w, h)

    # card
    card = tk.Frame(win, bg=CARD_DARK)
    card.place(relx=0.07, rely=0.10, relwidth=0.86, relheight=0.8)

    tk.Label(
        card,
        text="Secure Login",
        bg=CARD_DARK,
        fg="white",
        font=("Segoe UI", 16, "bold")
    ).pack(pady=15)

    tk.Label(
        card,
        text="ENTER RECOVERY CODE",
        font=("Segoe UI", 10, "bold"),
        bg=CARD_DARK,
        fg="white"
    ).pack()

    entry = tk.Entry(
        card,
        bg=INPUT_BG,
        fg="white",
        insertbackground="white",
        justify="center",
        font=("Segoe UI", 12)
    )
    entry.pack(fill="x", padx=25, pady=15, ipady=10)

    status = tk.Label(card, text="", bg=CARD_DARK, fg="gray")
    status.pack()

    btn = tk.Button(
        card,
        text="LOGIN",
        bg=SECONDARY_COLOR,
        fg="black",
        font=("Segoe UI", 13, "bold"),
        bd=0,
        height=2,
        cursor="hand2"
    )
    btn.pack(fill="x", padx=20, pady=15)


    # ---------------- NETWORK THREAD ----------------
    def login_request(code):
        try:
            res = requests.post(
                "http://127.0.0.1:5000/login",
                json={"recovery_code": code, "device_id": DEVICE_ID},
                timeout=5
            )

            data = res.json()

            if data.get("success"):
                winsound.Beep(1000, 300)

                def ok():
                    win.destroy()
                    root.deiconify()
                    start_heartbeat()

                win.after(0, ok)

            else:
                win.after(0, lambda: status.config(text="❌ Wrong Code"))

        except:
            win.after(0, lambda: status.config(text="❌ Server error"))


    # ---------------- CLICK ----------------
    def on_login():
        code = entry.get().strip()

        if not code:
            status.config(text="Enter code")
            return

        status.config(text="Checking...")
        threading.Thread(target=login_request, args=(code,), daemon=True).start()

    btn.config(command=on_login)


    # slide effect (simple)
    def slide(y=-100):
        if y < 0:
            win.geometry(f"{w}x{h}+{x}+{y}")
            win.after(10, lambda: slide(y+20))

    slide()

def heartbeat_loop():
    global SESSION_ID, RECOVERY_CODE

    while True:
        try:
            res = requests.post("http://127.0.0.1:5000/heartbeat", json={
                "recovery_code": RECOVERY_CODE,
                "session_id": SESSION_ID
            }).json()

            if not res.get("valid"):
                root.after(0, lambda: (
                    show_custom_message("Logged Out", "You logged in from another device!", "warning"),
                    os._exit(0)
                ))

        except:
            pass

        time.sleep(10)

def start_heartbeat():
    t = threading.Thread(target=heartbeat_loop, daemon=True)
    t.start()

# --- UI Setup ---
root = tk.Tk()
root.withdraw()   # نخفي التطبيق الأساسي
show_login()      # فقط login window

root.title("WhatsApp Bulk Messenger Pro")
root.geometry("850x950")
root.configure(bg=BACKGROUND_COLOR)
root.resizable(True, True)

# Custom fonts
font_title = ("Segoe UI", 18, "bold")
font_subtitle = ("Segoe UI", 12, "bold")
font_normal = ("Segoe UI", 10)
font_button = ("Segoe UI", 11, "bold")

# Configure styles
style = ttk.Style()
style.theme_use('clam')

# Configure progress bar style
style.configure("Green.Horizontal.TProgressbar", 
                background=SECONDARY_COLOR,
                troughcolor=BORDER_COLOR,
                bordercolor=BORDER_COLOR,
                lightcolor=SECONDARY_COLOR,
                darkcolor=PRIMARY_COLOR)

# Configure scrollbar style
style.configure("Custom.Vertical.TScrollbar", 
                background=PRIMARY_DARK,
                troughcolor=BACKGROUND_COLOR,
                bordercolor=PRIMARY_DARK,
                arrowcolor="white",
                gripcount=0)

style.map("Custom.Vertical.TScrollbar", 
          background=[('active', '#FFFFFF')])

# Main container with scrollbar
main_container = tk.Frame(root, bg=BACKGROUND_COLOR)
main_container.pack(fill="both", expand=True)

# Create a canvas and scrollbar
canvas = tk.Canvas(main_container, bg=BACKGROUND_COLOR, highlightthickness=0)
scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview, style="Custom.Vertical.TScrollbar")
scrollable_frame = tk.Frame(canvas, bg=BACKGROUND_COLOR)

window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

def update_scrollregion(event=None):
    canvas.configure(scrollregion=canvas.bbox("all"))
    canvas.itemconfig(window_id, width=canvas.winfo_width())
scrollable_frame.bind("<Configure>", update_scrollregion)
canvas.bind("<Configure>", update_scrollregion)

canvas.pack(side="left", fill="both", expand=True, padx=(0, 2))
scrollbar.pack(side="right", fill="y", padx=(0, 2))


# Bind mouse wheel to canvas
def _on_mousewheel(event):
    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

canvas.bind_all("<MouseWheel>", _on_mousewheel)

# Header Frame with Gradient
header_frame = tk.Frame(scrollable_frame, height=200, bg=PRIMARY_DARK)
header_frame.pack(fill="x", pady=(0, 20))
header_frame.pack_propagate(False)

# Create gradient canvas
gradient_canvas = tk.Canvas(header_frame, bg=PRIMARY_DARK, highlightthickness=0, height=140)
gradient_canvas.pack(fill="both", expand=True)

# Header content inside the canvas using create_window
header_content = tk.Frame(gradient_canvas, bg=PRIMARY_DARK)
header_window = gradient_canvas.create_window(0, 0, window=header_content, anchor="center")

def center_header(event):
    gradient_canvas.coords(header_window, event.width // 2, event.height // 2)

gradient_canvas.bind("<Configure>", center_header)

# WhatsApp icon
icon_label = tk.Label(header_content, text="📱", font=("Segoe UI", 38), 
                     bg=PRIMARY_DARK, fg="white")
icon_label.pack(pady=(15, 5))

header_label = tk.Label(header_content, text="WHATSAPP BULK MESSENGER", font=("Segoe UI", 24, "bold"), 
                       fg="white", bg=PRIMARY_DARK)
header_label.pack(pady=(5, 5))

subheader_label = tk.Label(header_content, text="Send messages professionally at scale", 
                          font=("Segoe UI", 12), fg="white", bg=PRIMARY_DARK)
subheader_label.pack(pady=(5, 15))

# Main content container
content_container = tk.Frame(scrollable_frame, bg=BACKGROUND_COLOR, padx=30)
content_container.pack(fill="both", expand=True, pady=(0, 30))

# Numbers Frame
numbers_frame = tk.LabelFrame(content_container, text=" 📞 PHONE NUMBERS", bg=CARD_COLOR, fg=TEXT_COLOR, 
                            font=font_subtitle, relief="flat", bd=0, padx=15, pady=12)
numbers_frame.pack(fill="both", expand=True)

# Text area with scrollbar
text_frame = tk.Frame(numbers_frame, bg=CARD_COLOR)
text_frame.pack(fill="both", expand=True, pady=4)

numbers_text = tk.Text(text_frame, height=6, font=font_normal, bd=1, relief="solid", 
                     bg=CARD_COLOR, fg=TEXT_COLOR, selectbackground=ACCENT_COLOR,
                     wrap="word", padx=8, pady=8)
text_scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=numbers_text.yview, style="Custom.Vertical.TScrollbar")

numbers_text.configure(yscrollcommand=text_scrollbar.set)
numbers_text.pack(side="left", fill="both", expand=True)

# ➤ يربط الـ Text لتحديث تلقائي عند أي تغيير
numbers_text.bind("<KeyRelease>", lambda e: update_inputs_visibility())
numbers_text.bind("<FocusOut>", lambda e: update_inputs_visibility())
numbers_text.bind("<ButtonRelease>", lambda e: update_inputs_visibility())

text_scrollbar.pack(side="right", fill="y")

load_button = tk.Button(numbers_frame, text="📂 IMPORT EXCEL", command=load_numbers_from_excel, 
                      bg=SECONDARY_COLOR, fg="white", font=font_button, 
                      activebackground=PRIMARY_COLOR, activeforeground="white", 
                      bd=0, padx=15, pady=6, cursor="hand2", relief="raised")
load_button.pack(pady=8)

# Message Frame
message_frame = tk.LabelFrame(content_container, text=" 💬 MESSAGE CONTENT", bg=CARD_COLOR, fg=TEXT_COLOR,
                            font=font_subtitle, relief="flat", bd=0, padx=15, pady=12)
message_frame.pack(fill="x", pady=(0, 15))

msg_text_frame = tk.Frame(message_frame, bg=CARD_COLOR)
msg_text_frame.pack(fill="both", expand=True, pady=4)

message_entry = tk.Text(msg_text_frame, height=10, font=font_normal, bd=1, relief="solid",
                      bg=CARD_COLOR, fg=TEXT_COLOR, selectbackground=ACCENT_COLOR,
                      wrap="word", padx=8, pady=8)
msg_scrollbar = ttk.Scrollbar(msg_text_frame, orient="vertical", command=message_entry.yview, style="Custom.Vertical.TScrollbar")

message_entry.configure(yscrollcommand=msg_scrollbar.set)

message_entry.pack(side="left", fill="both", expand=True)
msg_scrollbar.pack(side="right", fill="y")

# File Frame
file_frame = tk.LabelFrame(content_container, text=" 📎 ATTACHMENT", bg=CARD_COLOR, fg=TEXT_COLOR,
                         font=font_subtitle, relief="flat", bd=0, padx=15, pady=12)
file_frame.pack(fill="x", pady=(0, 15))

file_container = tk.Frame(file_frame, bg=CARD_COLOR)
file_container.pack(fill="x", padx=5, pady=8)

tk.Label(file_container, text="Select File:", bg=CARD_COLOR, fg=TEXT_COLOR, 
        font=font_normal).pack(side="left", padx=(0, 10))

file_entry = tk.Entry(file_container, width=28, font=font_normal, bd=1, relief="solid",
                    bg=CARD_COLOR, fg=TEXT_COLOR, justify="left")
file_entry.pack(side="left", fill="both", expand=True, padx=(0, 10))

file_button = tk.Button(file_container, text="BROWSE", font=font_normal, 
                      command=lambda: file_entry.insert(0, filedialog.askopenfilename()),
                      bg=SECONDARY_COLOR, fg="white", activebackground=PRIMARY_COLOR,
                      activeforeground="white", bd=0, padx=12, pady=4, cursor="hand2")
file_button.pack(side="left")

 
# --- Settings Frame ---
settings_frame = tk.LabelFrame(
    content_container,
    text=" ⚙ SETTINGS",
    bg=CARD_COLOR,
    fg=TEXT_COLOR,
    font=font_subtitle,
    relief="flat",
    bd=0,
    padx=15,
    pady=12
)
settings_frame.pack(fill="x", pady=(0, 15))

# --- Delay Input (Manual Delay) ---
delay_container = tk.Frame(settings_frame, bg=CARD_COLOR)
tk.Label(
    delay_container,
    text="Delay between messages (seconds):",
    bg=CARD_COLOR,
    fg=TEXT_COLOR,
    font=font_normal
).pack(side="left")

delay_entry = tk.Entry(
    delay_container,
    width=8,
    font=font_normal,
    bd=1,
    relief="solid",
    bg=CARD_COLOR,
    fg=TEXT_COLOR,
    justify="center"
)
delay_entry.pack(side="left", padx=5)
delay_entry.insert(0, "2")
delay_container.pack_forget()  # مخفي افتراضيًا

# --- Batch Mode Info Label ---
batch_info_container = tk.Frame(settings_frame, bg=CARD_COLOR)
batch_info_label = tk.Label(
    batch_info_container,
    text="Batch mode: Sends numbers in groups with a pause between each group for testing.",
    bg=CARD_COLOR,
    fg=TEXT_COLOR,
    font=font_normal,
    wraplength=400,  # لتقسيم النص لو طويل
    justify="left"
)
batch_info_label.pack(side="left")
batch_info_container.pack_forget()

# --- Batch Inputs ---
batch_size_container = tk.Frame(settings_frame, bg=CARD_COLOR)
batch_size_label = tk.Label(
    batch_size_container,
    text="Batch size (how many numbers):",
    bg=CARD_COLOR,
    fg=TEXT_COLOR,
    font=font_normal
)
batch_size_entry = tk.Entry(
    batch_size_container,
    width=5,
    font=font_normal,
    bd=1,
    relief="solid",
    bg=CARD_COLOR,
    fg=TEXT_COLOR,
    justify="center"
)
batch_size_label.pack(side="left")
batch_size_entry.pack(side="left", padx=5)
batch_size_container.pack_forget()

pause_container = tk.Frame(settings_frame, bg=CARD_COLOR)
pause_label = tk.Label(
    pause_container,
    text="Pause after each batch (hours):",
    bg=CARD_COLOR,
    fg=TEXT_COLOR,
    font=font_normal
)
pause_entry = tk.Entry(
    pause_container,
    width=5,
    font=font_normal,
    bd=1,
    relief="solid",
    bg=CARD_COLOR,
    fg=TEXT_COLOR,
    justify="center"
)
pause_label.pack(side="left")
pause_entry.pack(side="left", padx=5)
pause_container.pack_forget()

# --- Auto Distribute Label ---
auto_distribute_label = tk.Label(
    settings_frame,
    text="",  # يظهر عند اختيار Auto
    bg=CARD_COLOR,
    fg=TEXT_COLOR,
    font=font_normal
)
auto_distribute_label.pack_forget()

# --- Radio Buttons ---
mode_var = tk.StringVar(value="manual")  # القيم: "manual", "batch", "auto"
tk.Label(
    settings_frame,
    text="Choose sending mode:",
    bg=CARD_COLOR,
    fg=TEXT_COLOR,
    font=font_normal
).pack(anchor="w", padx=5, pady=(10,2))

rb_manual = tk.Radiobutton(
    settings_frame,
    text="Manual Delay",
    variable=mode_var,
    value="manual",
    bg=CARD_COLOR,
    fg=TEXT_COLOR,
    font=font_normal,
    selectcolor=CARD_COLOR,
    cursor="hand2",
    command=update_inputs_visibility
)
rb_manual.pack(anchor="w", padx=20)

rb_batch = tk.Radiobutton(
    settings_frame,
    text="Batch Sending With Pause",
    variable=mode_var,
    value="batch",
    bg=CARD_COLOR,
    fg=TEXT_COLOR,
    font=font_normal,
    selectcolor=CARD_COLOR,
    cursor="hand2",
    command=update_inputs_visibility
)
rb_batch.pack(anchor="w", padx=20)

rb_auto = tk.Radiobutton(
    settings_frame,
    text="Auto Distribute Over The Day",
    variable=mode_var,
    value="auto",
    bg=CARD_COLOR,
    fg=TEXT_COLOR,
    font=font_normal,
    selectcolor=CARD_COLOR,
    cursor="hand2",
    command=update_inputs_visibility
)
rb_auto.pack(anchor="w", padx=20)


# Progress Frame
progress_frame = tk.Frame(content_container, bg=BACKGROUND_COLOR)
progress_frame.pack(fill="x", pady=(0, 15))

progress_container = tk.Frame(progress_frame, bg=BACKGROUND_COLOR)
progress_container.pack(fill="both", expand=True) 

progress_label = tk.Label(progress_container, text="0/0", bg=BACKGROUND_COLOR, 
                        fg=LIGHT_TEXT, font=font_normal)
progress_label.pack(side="right")

tk.Label(progress_container, text="📊 PROGRESS", bg=BACKGROUND_COLOR, 
        fg=TEXT_COLOR, font=font_normal).pack(side="left")

progress_bar = ttk.Progressbar(progress_frame, orient="horizontal", length=600, 
                              mode="determinate", style="Green.Horizontal.TProgressbar")
progress_bar.pack(fill="both", expand=True, pady=(8, 0))

# label frame
info_label = tk.Label(progress_frame, text="", bg=BACKGROUND_COLOR, fg=TEXT_COLOR, font=font_normal)
info_label.pack(fill="x", pady=(5, 5))  # Temporary text shown after each batch

# Last Number Sent Label (optional to add the new feature)
last_number_label = tk.Label(progress_frame, text="Last number sent: None", bg=BACKGROUND_COLOR, fg=TEXT_COLOR, font=font_normal)
last_number_label.pack(fill="x", pady=(0, 0))

# --- Create Play/Stop button initially disabled ---
play_stop_button = tk.Button(
    progress_frame,
    text="⛔ Stop",
    bg="black",
    fg="white",
    font=font_normal,
    state="disabled",   # غير مفعل قبل الضغط على Start
    command=lambda: toggle_sending()
)
play_stop_button.pack(pady=5)


# Send Button with hover effect
def on_enter(e):
    send_button.config(bg=PRIMARY_COLOR, relief="sunken")

def on_leave(e):
    send_button.config(bg=SECONDARY_COLOR, relief="raised")

send_button = tk.Button(content_container, text="🚀 START BULK SENDING", command=send_messages, 
                      bg=SECONDARY_COLOR, fg="white", font=("Segoe UI", 14, "bold"), 
                      activebackground=PRIMARY_COLOR, activeforeground="white", 
                      bd=0, padx=35, pady=12, cursor="hand2", relief="raised")
send_button.pack(pady=20)
send_button.bind("<Enter>", on_enter)
send_button.bind("<Leave>", on_leave)

# Footer
footer_frame = tk.Frame(scrollable_frame, bg=BACKGROUND_COLOR, height=35)
footer_frame.pack(fill="both", expand=True)
footer_frame.pack_propagate(False)

footer_label = tk.Label(footer_frame, text="© 2024 WhatsApp Bulk Messenger Pro • Professional Messaging Solution", 
                       bg=BACKGROUND_COLOR, fg=LIGHT_TEXT, font=("Segoe UI", 9))
footer_label.pack(fill="both", expand=True)

# Update scrollregion after everything is drawn
def update_scrollregion():
    canvas.update_idletasks()
    canvas.configure(scrollregion=canvas.bbox("all"))

root.after(100, update_scrollregion)

root.mainloop()