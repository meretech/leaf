import sys
import os
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.camera import Camera
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.app import App
#from kivy.core.camera import Camera
from kivy.config import Config
from kivy.graphics.texture import Texture
from PIL import Image as PILImage
from datetime import datetime
from database.db_connection import create_connection 
from kivy.lang import Builder
from kivy.uix.floatlayout import FloatLayout
from datetime import datetime


# Set Kivy configurations
Config.set('kivy', 'camera', 'opencv')
Config.set('graphics', 'multisamples', '0')
Config.set('graphics', 'backend', 'sdl2')

# Load .kv files
Builder.load_file('app/login.kv')
Builder.load_file('app/register.kv')
Builder.load_file('app/home.kv')
Builder.load_file('app/capture.kv')
Builder.load_file('app/save.kv')
Builder.load_file('app/result.kv')

# Define Screens
class LoginScreen(Screen):
    def on_login(self):
        username = self.ids.username.text
        password = self.ids.password.text
        print(f"Attempting to log in User: {username}")

        if not username or not password:
            print("Please enter a username and password.")
            return
        # Database connection
        conn = App.get_running_app().conn
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM Users WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()
        # Record login time
        cursor.execute("INSERT INTO LoginTimes (user_id, login_time) VALUES (?, ?)", 
                           (user[0], datetime.now()))
        conn.commit()

        if user:
            print("Login successful!")
            self.manager.get_screen('capture').current_user_id = user[0]
            self.manager.current = 'capture'
           
        else:
            print("Invalid username or password.")

class RegisterScreen(Screen):
    def register_user(self, username, password, full_name, surname, email, id_number):
        print(f"Registering user: {username}")
        if not all([username, password, full_name, surname, email, id_number]):
            print("Please fill all fields.")
            return

        conn = App.get_running_app().conn
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM Users WHERE username=?", (username,))
        if cursor.fetchone():
            print("Username already taken.")
            return

        cursor.execute("INSERT INTO Users (username, password, full_name, surname, email, id_number) VALUES (?, ?, ?, ?, ?, ?)",
                       (username, password, full_name, surname, email, id_number))
        conn.commit()
        print("User registered successfully!")
        self.manager.current = 'login'

class HomeScreen(Screen):
    def on_enter(self):
        # Retrieve and display logged-in user's name
        if self.current_user_id is not None:
            conn = App.get_running_app().conn
            cursor = conn.cursor()
            cursor.execute("SELECT username FROM Users WHERE id=?", (self.current_user_id,))
            user = cursor.fetchone()
            if user:
                self.ids.welcome_label.text = f"Welcome, {user[0]}!"
        else:
            self.ids.welcome_label.text = "Welcome, Guest!"

class ResultScreen(Screen):
    def go_to_home(self):
        self.manager.current = 'home'   

class CaptureScreen(Screen):
    def capture_image(self):
        # 5/11 below added
        camera = self.ids.camera_widget 
        self.image_saved = False  # Flag to prevent multiple saves
        # Capture image and save it to a file
        self.file_path = os.path.join("captured_images", "captured_image.png")
        camera.export_to_png(self.file_path)
        Clock.schedule_once(self.go_to_save_screen, 2)
    
    def go_to_save_screen(self, *args):
        # Move to SaveScreen after capturing image
        self.manager.current = 'save'

    def on_logout(self):
        # Clear the text inputs for username and password
        self.manager.current = 'login'
        conn = App.get_running_app().conn
        cursor = conn.cursor()
        
        # Record logout time
        cursor.execute("INSERT INTO LogoutTimes (user_id, logout_time) VALUES (?, ?)", 
                       (self.current_user_id, datetime.now()))
        conn.commit()
        print("User logged out successfully!")
        

class SaveScreen(Screen):
    def on_enter(self):
        # Load the captured image from the path set in CaptureScreen
        capture_screen = self.manager.get_screen('capture')
        file_path = capture_screen.file_path
        self.ids.result_label.text = "Press Save to store image"
        # Ensure the image path is not empty
        if file_path and os.path.exists(file_path):
            # Load the image into the Image widget
            pil_image = PILImage.open(file_path)
            self.ids.saved_image.source = file_path
            self.ids.saved_image.reload()
            self.ids.saved_image.size = (200, 200)
            
        

    def save_image(self):
        try:
            #user_id = self.current_user_id
            user_id = App.get_running_app().current_user_id
            capture_screen = self.manager.get_screen('capture')
            file_path = capture_screen.file_path
            image_type = "png"
            image_size = os.path.getsize(file_path)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            image_name = os.path.basename(file_path)
            image_location = file_path

            # Your SQL Server code to save details here
            query = """
            INSERT INTO ImageDetails (user_id, image_type, image_size, image_location, image_name, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            """
            
            conn = App.get_running_app().conn
            cursor = conn.cursor()
                   
           
            # Execute the insert query
            cursor.execute(query, (user_id, image_type, image_size, image_location, image_name, timestamp))
            conn.commit()

            # Show a success message
            self.ids.result_label.text = "Image details saved successfully!"
            self.image_saved = True

        except Exception as e:
            print(f"Error saving image details: {e}")
            self.ids.result_label.text = "Failed to save image details."
            '''if conn:
                conn.rollback()
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()'''

    def on_logout(self):
        # Clear the text inputs for username and password
        self.manager.current = 'login'

class LeafApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_user_id = None  # Initialize current_user_id

    def set_user_id(self, user_id):
        self.current_user_id = user_id  # Method to set user ID

    def get_user_id(self):
        return self.current_user_id
    
    def build(self):
        self.conn = create_connection()  # Establish DB connection at app start
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(RegisterScreen(name='register'))
        sm.add_widget(HomeScreen(name='home'))
        sm.add_widget(CaptureScreen(name='capture'))
        sm.add_widget(SaveScreen(name='save'))
        sm.current = 'login'  # Set the default screen to login
        return sm

if __name__ == "__main__":
    LeafApp().run()
