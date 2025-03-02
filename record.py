import json
import time
import os
from pynput import mouse, keyboard
import threading

class InputTracker:
    def __init__(self, output_file="input_data.json"):
        self.start_time = time.time()
        self.data = {}
        self.output_file = output_file
        self.running = True
        self.lock = threading.Lock()
        self.old_mouse_pos = {"x": 0, "y": 0}
        self.new_mouse_pos = {"x": 0, "y": 0}
        self.buffer = ""  # Buffer to store typed characters
        
        # Set up listeners
        self.keyboard_listener = keyboard.Listener(on_press=self.on_key_press)
        self.mouse_listener = mouse.Listener(
            on_move=self.on_mouse_move, 
            on_click=self.on_click,
            on_scroll=self.on_scroll
        )
        
        # Set up periodic mouse position checking
        self.mouse_thread = threading.Thread(target=self.check_mouse_position)
    
    def get_time_interval(self):
        """Get the current time interval in 10ms intervals since start"""
        return str(int((time.time() - self.start_time) * 100))
    
    def on_key_press(self, key):
        """Handle key press events"""
        char = None
        try:
            # Try to get the character
            char = key.char
            # Add to buffer
            self.buffer += char
            
            # Check if buffer ends with ///
            if self.buffer.endswith("///"):
                print("\nShutdown sequence detected. Saving data...")
                self.stop()
                return False  # Stop listener
            
            # Reset buffer if it gets too long
            if len(self.buffer) > 10:
                self.buffer = self.buffer[-10:]
                
        except AttributeError:
            # Special key
            char = str(key)
        
        with self.lock:
            time_interval = self.get_time_interval()
            self.data[time_interval] = {
                "x": False,
                "y": False,
                "k": char,
                "c": False,
                "up": False,
                "down": False
            }
            
        return True
    
    def on_mouse_move(self, x, y):
        """Handle mouse movement"""
        self.new_mouse_pos = {"x": x, "y": y}
    
    def on_click(self, x, y, button, pressed):
        """Handle mouse clicks - both press and release"""
        print(f"Mouse {'press' if pressed else 'release'} at ({x}, {y})")
        
        with self.lock:
            time_interval = self.get_time_interval()
            
            if pressed:  # Mouse button down
                self.data[time_interval] = {
                    "x": x,
                    "y": y,
                    "k": False,
                    "c": True,
                    "down": True,  # Mouse button pressed down
                    "up": False
                }
            else:  # Mouse button up
                self.data[time_interval] = {
                    "x": x,
                    "y": y,
                    "k": False,
                    "c": True,  # Keep c for compatibility
                    "down": False,
                    "up": True  # Mouse button released
                }
                
        return True
    
    def on_scroll(self, x, y, dx, dy):
        """Handle mouse scroll events"""
        with self.lock:
            time_interval = self.get_time_interval()
            self.data[time_interval] = {
                "x": x,
                "y": y,
                "k": False,
                "c": False,
                "up": False,
                "down": False,
                "scroll": dy  # Positive for up, negative for down
            }
    
    def check_mouse_position(self):
        """Periodically check if mouse position has changed"""
        while self.running:
            if (self.old_mouse_pos["x"] != self.new_mouse_pos["x"] or 
                self.old_mouse_pos["y"] != self.new_mouse_pos["y"]):
                with self.lock:
                    time_interval = self.get_time_interval()
                    self.data[time_interval] = {
                        "x": self.new_mouse_pos["x"],
                        "y": self.new_mouse_pos["y"],
                        "k": False,
                        "c": False,
                        "up": False,
                        "down": False
                    }
                self.old_mouse_pos = self.new_mouse_pos.copy()
            time.sleep(0.1)
    
    def start(self):
        """Start tracking inputs"""
        print("Input tracking started.")
        print("Type /// to stop and save data.")
        
        # Start listeners
        self.keyboard_listener.start()
        self.mouse_listener.start()
        self.mouse_thread.start()
        
        # Wait for keyboard listener to end
        self.keyboard_listener.join()
        
        # Save data when done
        self.save_data()
    
    def stop(self):
        """Stop tracking inputs"""
        self.running = False
        if self.mouse_listener.is_alive():
            self.mouse_listener.stop()
        
        # Wait for mouse thread to complete
        self.mouse_thread.join(timeout=1.0)
    
    def save_data(self):
        """Save data to JSON file"""
        with self.lock:
            # Check for click events before saving
            down_events = sum(1 for v in self.data.values() if v.get('down') is True)
            up_events = sum(1 for v in self.data.values() if v.get('up') is True)
            
            print(f"Statistics:")
            print(f"- Total events: {len(self.data)}")
            print(f"- Mouse down events: {down_events}")
            print(f"- Mouse up events: {up_events}")
            
            # Create a timestamp for unique filename
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"input_data_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(self.data, f, indent=2)
            print(f"Data saved to {os.path.abspath(filename)}")
            
            # Also save to the default filename
            with open(self.output_file, 'w') as f:
                json.dump(self.data, f, indent=2)
            print(f"Data also saved to {os.path.abspath(self.output_file)}")

if __name__ == "__main__":
    tracker = InputTracker()
    try:
        tracker.start()
    except KeyboardInterrupt:
        print("\nProgram interrupted. Stopping...")
        tracker.stop()
        tracker.save_data()