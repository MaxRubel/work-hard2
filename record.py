import json
import time
import os
import logging
from pynput import mouse, keyboard
import threading

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger('InputTracker')

class InputTracker:
    def __init__(self, output_file="input_data.json"):
        self.start_time = time.time()
        self.data = {}
        self.dragging = {}
        self.output_file = output_file
        self.running = True
        self.lock = threading.Lock()
        self.old_mouse_pos = {"x": 0, "y": 0}
        self.new_mouse_pos = {"x": 0, "y": 0}
        self.buffer = ""  # Buffer to store typed characters
        self.mult_keys = set()
        
        # Drag mouse
        self.is_dragging = False
        self.drag_start_pos = {"x": 0, "y": 0}
        self.drag_start_time = 0
        self.drag_button = None
        self.current_drag_data = {
            "start_x": 0,
            "start_y": 0,
            "current_x": 0,
            "current_y": 0,
            "distance": 0,
            "duration": 0
        }
        
        # Event tracking info
        self.event_counters = {
            "key_presses": 0,
            "mouse_moves": 0,
            "mouse_clicks": 0,
            "mouse_releases": 0,
            "scrolls": 0,
            "drags": 0,
            "drag_distance_total": 0
        }
        
        logger.info("Start Input Tracker")
        
        # Set up event listeners
        self.keyboard_listener = keyboard.Listener(
            on_press=self.on_key_press,
            on_release=self.on_key_release
            )
        self.mouse_listener = mouse.Listener(
            on_move=self.on_mouse_move, 
            on_click=self.on_click,
            on_scroll=self.on_scroll
        )
        
        # Set up interval to check mouse position
        self.mouse_thread = threading.Thread(target=self.check_mouse_position)
        logger.info("InputTracker initialized successfully")
    
    def get_time_interval(self):
        """Get the current time interval in 10ms intervals since start"""
        return str(int((time.time() - self.start_time) * 100))
    
    def on_key_press(self, key):
        char = None
        try:
            char = key.char
            self.buffer += char
            
            # Exit out the program by typing: ///
            if self.buffer.endswith("///"):
                logger.info("Ending recording. Saving data...")
                self.stop()
                return False  # Stop listener
            
            # Reset buffer if it gets too long
            if len(self.buffer) > 10:
                self.buffer = self.buffer[-10:]
            
            logger.debug(f"Key press: '{char}'")
                
        except AttributeError:
            char = str(key)
            logger.debug(f"Special key press: {char}")
        
        with self.lock:
            time_interval = self.get_time_interval()
            self.data[time_interval] = {
                "x": False, # current X mous pos / set to False because this is a keyboard event
                "y": False, # current Y mouse pos / set to False because this is a keyboard event
                "k": char, # the key pressed
                "c": False, # click
                "down": False, #click down
                "up": False, # click release
                "mults_keys": list(self.mult_keys)  # Convert set to list for JSON serialization
            }

            self.mult_keys.add(char)

            self.event_counters["key_presses"] += 1
            
        return True
    
    def on_key_release(self, key):
        char = None
        try:
            char = key.char
        except AttributeError:
            char = str(key)
            logger.debug(f"Special key release: {char}")
        
        with self.lock:
            # Check if the character is in the set before trying to remove it
            if char in self.mult_keys:
                self.mult_keys.remove(char)
            else:
                logger.debug(f"Attempted to remove key {char} that was not in mult_keys set")
        return True
        
    def on_mouse_move(self, x, y):
        self.new_mouse_pos = {"x": x, "y": y}
        
        # Check if we're currently dragging
        if self.is_dragging:
            # Update current drag data
            self.current_drag_data["current_x"] = x
            self.current_drag_data["current_y"] = y
            
            # Calculate current drag distance
            dx = x - self.drag_start_pos["x"]
            dy = y - self.drag_start_pos["y"]
            current_distance = (dx**2 + dy**2)**0.5
            
            # Update distance
            self.current_drag_data["distance"] = current_distance
            self.current_drag_data["duration"] = time.time() - self.drag_start_time
            
            # Log drag movement (but not too often)
            if self.event_counters["mouse_moves"] % 20 == 0:
                logger.debug(f"Dragging: distance={current_distance:.2f}px, duration={self.current_drag_data['duration']:.2f}s")
                
                # Also record selected drag movements
                with self.lock:
                    time_interval = self.get_time_interval()
                    self.data[time_interval] = {
                        "x": x,
                        "y": y,
                        "k": False,
                        "c": False, 
                        "up": False,
                        "down": False,
                        "during_drag": True,
                        "drag_distance_so_far": current_distance,
                        "drag_duration_so_far": self.current_drag_data["duration"],
                        "mults_keys": list(self.mult_keys)  # Add the active keys
                    }
        
        # Only log regular movements occasionally to avoid flooding the terminal
        if self.event_counters["mouse_moves"] % 10 == 0:
            logger.debug(f"Mouse moved to ({x}, {y})")
    
    def on_click(self, x, y, button, pressed):
        with self.lock:
            time_interval = self.get_time_interval()
            
            if pressed:  # Mouse button down
                logger.info(f"Mouse press with {button} at ({x}, {y})")
                if self.mult_keys:
                    logger.info(f"  with active keys: {self.mult_keys}")
                
                self.event_counters["mouse_clicks"] += 1
                
                # Start potential drag operation
                self.is_dragging = True
                self.drag_start_pos = {"x": x, "y": y}
                self.drag_start_time = time.time()
                self.drag_button = button
                
                # Reset current drag data
                self.current_drag_data = {
                    "start_x": x,
                    "start_y": y,
                    "current_x": x,
                    "current_y": y,
                    "distance": 0,
                    "duration": 0
                }
                
                logger.info(f"Potential drag started at ({x}, {y})")
                
                self.data[time_interval] = {
                    "x": x,
                    "y": y,
                    "k": False,
                    "c": True,
                    "down": True,  # Mouse button pressed down
                    "up": False,
                    "drag_start": True,
                    "mults_keys": list(self.mult_keys),  # Add active keys
                    "button": str(button)  # Add which button was pressed
                }
            else:  # Mouse button up
                logger.info(f"Mouse release with {button} at ({x}, {y})")
                if self.mult_keys:
                    logger.info(f"  with active keys: {self.mult_keys}")
                    
                self.event_counters["mouse_releases"] += 1
                
                # Check if we were dragging
                if self.is_dragging and button == self.drag_button:
                    # Calculate final drag metrics
                    drag_end_time = time.time()
                    drag_duration = drag_end_time - self.drag_start_time
                    
                    # Calculate distance (simple straight line)
                    dx = x - self.drag_start_pos["x"]
                    dy = y - self.drag_start_pos["y"]
                    drag_distance = (dx**2 + dy**2)**0.5
                    
                    logger.info(f"Drag ended at ({x}, {y})")
                    logger.info(f"Drag distance: {drag_distance:.2f} pixels")
                    logger.info(f"Drag duration: {drag_duration:.2f} seconds")
                    
                    # Update counters
                    self.event_counters["drags"] += 1
                    self.event_counters["drag_distance_total"] += drag_distance
                    
                    # Save drag data
                    self.data[time_interval] = {
                        "x": x,
                        "y": y,
                        "k": False,
                        "c": True,
                        "down": False,
                        "up": True,
                        "drag_end": True,
                        "drag_distance": drag_distance,
                        "drag_duration": drag_duration,
                        "drag_start_x": self.drag_start_pos["x"],
                        "drag_start_y": self.drag_start_pos["y"],
                        "mults_keys": list(self.mult_keys),  # Add active keys
                        "button": str(button)  # Add which button was released
                    }
                    
                    # Reset drag state
                    self.is_dragging = False
                else:
                    # Regular mouse release (not part of drag)
                    self.data[time_interval] = {
                        "x": x,
                        "y": y,
                        "k": False,
                        "c": True,
                        "down": False,
                        "up": True,
                        "mults_keys": list(self.mult_keys),  # Add active keys
                        "button": str(button)  # Add which button was released
                    }
                
        return True
    
    def on_scroll(self, x, y, dx, dy):
        """Handle mouse scroll events"""
        logger.debug(f"Mouse scroll at ({x}, {y}), direction: {'up' if dy > 0 else 'down'}")
        if self.mult_keys:
            logger.debug(f"  with active keys: {self.mult_keys}")
            
        self.event_counters["scrolls"] += 1
        
        with self.lock:
            time_interval = self.get_time_interval()
            self.data[time_interval] = {
                "x": x,
                "y": y,
                "k": False,
                "c": False,
                "up": False,
                "down": False,
                "scroll": dy,  # Positive for up, negative for down
                "mults_keys": list(self.mult_keys)  # Add active keys
            }
    
    def check_mouse_position(self):
        """Periodically check if mouse position has changed"""
        logger.info("Mouse position tracking thread started")
        position_updates = 0
        
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
                        "down": False,
                        "mults_keys": list(self.mult_keys)  # Add active keys
                    }
                    position_updates += 1
                    self.event_counters["mouse_moves"] += 1
                    
                    # Log every 10th position update to avoid flooding
                    if position_updates % 10 == 0:
                        logger.debug(f"Position update #{position_updates}: ({self.new_mouse_pos['x']}, {self.new_mouse_pos['y']})")
                        
                self.old_mouse_pos = self.new_mouse_pos.copy()
            time.sleep(0.1)
        
        logger.info("Mouse position tracking thread stopped")
    
    def start(self):
        """Start tracking inputs"""
        time.sleep(.6)
        logger.info("=== Input tracking started ===")
        logger.info("Type /// to stop and save data")
        
        # Start listeners
        self.keyboard_listener.start()
        logger.info("Keyboard listener started")
        
        self.mouse_listener.start()
        logger.info("Mouse listener started")
        
        self.mouse_thread.start()
        
        # Print status updates periodically
        status_thread = threading.Thread(target=self.print_status)
        status_thread.daemon = True
        status_thread.start()
        
        # Wait for keyboard listener to end
        self.keyboard_listener.join()
        
        # Save data when done
        self.save_data()
    
    def print_status(self):
        """Print periodic status updates"""
        while self.running:
            time.sleep(5)  # Update every 5 seconds
            with self.lock:
                elapsed = time.time() - self.start_time
                logger.info(f"Status: Running for {elapsed:.1f}s, {len(self.data)} events recorded")
                
                # Show standard event counts
                logger.info(f"Events: {self.event_counters}")
                
                # Show active keys
                if self.mult_keys:
                    logger.info(f"Currently active keys: {self.mult_keys}")
                
                # Show drag status if currently dragging
                if self.is_dragging:
                    drag_duration = time.time() - self.drag_start_time
                    logger.info(f"Currently dragging: {self.drag_button} button")
                    logger.info(f"  Started at: ({self.drag_start_pos['x']}, {self.drag_start_pos['y']})")
                    logger.info(f"  Current position: ({self.new_mouse_pos['x']}, {self.new_mouse_pos['y']})")
                    logger.info(f"  Current distance: {self.current_drag_data['distance']:.2f} pixels")
                    logger.info(f"  Current duration: {drag_duration:.2f} seconds")
    
    def stop(self):
        """Stop tracking inputs"""
        logger.info("Stopping input tracking...")
        self.running = False
        if self.mouse_listener.is_alive():
            self.mouse_listener.stop()
        
        # Wait for mouse thread to complete
        self.mouse_thread.join(timeout=1.0)
        logger.info("All listeners stopped")
    
    def save_data(self):
        """Save data to JSON file"""
        with self.lock:
            # Check for various events before saving
            down_events = sum(1 for v in self.data.values() if v.get('down') is True)
            up_events = sum(1 for v in self.data.values() if v.get('up') is True)
            drag_starts = sum(1 for v in self.data.values() if v.get('drag_start') is True)
            drag_ends = sum(1 for v in self.data.values() if v.get('drag_end') is True)
            drag_movements = sum(1 for v in self.data.values() if v.get('during_drag') is True)
            
            # Calculate average drag distance and duration
            drag_distances = [v.get('drag_distance', 0) for v in self.data.values() if v.get('drag_end') is True]
            drag_durations = [v.get('drag_duration', 0) for v in self.data.values() if v.get('drag_end') is True]
            
            avg_drag_distance = sum(drag_distances) / len(drag_distances) if drag_distances else 0
            avg_drag_duration = sum(drag_durations) / len(drag_durations) if drag_durations else 0
            
            logger.info("=== Saving Data ===")
            logger.info(f"Statistics:")
            logger.info(f"- Total events: {len(self.data)}")
            logger.info(f"- Mouse down events: {down_events}")
            logger.info(f"- Mouse up events: {up_events}")
            logger.info(f"- Key presses: {self.event_counters['key_presses']}")
            logger.info(f"- Mouse moves: {self.event_counters['mouse_moves']}")
            logger.info(f"- Scrolls: {self.event_counters['scrolls']}")
            logger.info(f"- Drag operations: {self.event_counters['drags']}")
            logger.info(f"- Drag starts logged: {drag_starts}")
            logger.info(f"- Drag ends logged: {drag_ends}")
            logger.info(f"- Drag movements tracked: {drag_movements}")
            logger.info(f"- Total drag distance: {self.event_counters['drag_distance_total']:.2f} pixels")
            
            if self.event_counters['drags'] > 0:
                logger.info(f"- Average drag distance: {avg_drag_distance:.2f} pixels")
                logger.info(f"- Average drag duration: {avg_drag_duration:.2f} seconds")
            
            try:
                # Also save to the default filename
                with open(self.output_file, 'w') as f:
                    json.dump(self.data, f, indent=2)
                logger.info(f"Data also saved to {os.path.abspath(self.output_file)}")
            except Exception as e:
                logger.error(f"Error saving data: {e}")


if __name__ == "__main__":
    try:
        # You can adjust log level here for more or less verbose output
        # Options: logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR
        # For extremely detailed logging, use DEBUG
        # For normal operation, use INFO
        logger.setLevel(logging.INFO)
        
        logger.info("Starting InputTracker...")
        tracker = InputTracker()
        tracker.start()
    except KeyboardInterrupt:
        logger.warning("Program interrupted by user (Ctrl+C). Stopping...")
        if 'tracker' in locals():
            tracker.stop()
            tracker.save_data()
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)