import pyautogui
import time
import json
import logging

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger('InputReplay')

# Fail-safe feature - move mouse to upper left corner to abort
pyautogui.FAILSAFE = True

class InputReplay:
    def __init__(self, input_file="input_data.json"):
        self.input_file = input_file
        self.data = {}
        self.modifiers = set()  # Track currently held modifier keys
        self.mouse_down = False  # Track if mouse button is currently pressed
        
        # Statistics counters
        self.stats = {
            "keyCount": 0,
            "hotkeyCount": 0,
            "mouseClickCount": 0,
            "mouseMoveCount": 0,
            "scrollCount": 0,
            "dragCount": 0
        }
    
    def load_data(self):
        """Load recorded input data from JSON file"""
        try:
            with open(self.input_file, 'r') as file:
                self.data = json.load(file)
            logger.info(f"Loaded {len(self.data)} events from {self.input_file}")
            return True
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return False
    
    def process_keyboard_input(self, task):
        """Process keyboard input events"""
        current_key = task.get("k")
        if not current_key:
            return False
            
        logger.info(f"Processing key: {current_key}")
        
        # Handle modifier keys in mults_keys list
        mults_keys = task.get("mults_keys", [])
        
        # Add new modifiers
        for key in mults_keys:
            if key not in self.modifiers and key in ['shift', 'ctrl', 'alt', 'cmd']:
                self.modifiers.add(key)
                logger.info(f"Pressing modifier: {key}")
                pyautogui.keyDown(key)
        
        # Release old modifiers that are no longer held
        for key in list(self.modifiers):
            if key not in mults_keys:
                logger.info(f"Releasing modifier: {key}")
                pyautogui.keyUp(key)
                self.modifiers.remove(key)
        
        # Handle the current key press if it's not a modifier that's already tracked
        if current_key not in self.modifiers:
            # Handle special keys
            if current_key in ['shift', 'ctrl', 'alt', 'cmd']:
                # This is a modifier key press event
                if current_key not in self.modifiers:
                    logger.info(f"Pressing modifier: {current_key}")
                    pyautogui.keyDown(current_key)
                    self.modifiers.add(current_key)
            elif len(current_key) == 1:  # Regular character key
                logger.info(f"Typing: {current_key}")
                pyautogui.write(current_key)
            else:  # Special key like enter, space, etc.
                try:
                    logger.info(f"Pressing special key: {current_key}")
                    pyautogui.press(current_key)
                except Exception as e:
                    logger.error(f"Failed to press key '{current_key}': {e}")
        
        self.stats["keyCount"] += 1
        if mults_keys:
            self.stats["hotkeyCount"] += 1
            
        return True
    
    def process_keyboard_release(self, task):
        """Process keyboard release events"""
        current_key = task.get("k")
        if not current_key:
            return False
            
        logger.info(f"Releasing key: {current_key}")
        
        # Check if it's a modifier key that needs to be released
        if current_key in ['shift', 'ctrl', 'alt', 'cmd'] and current_key in self.modifiers:
            pyautogui.keyUp(current_key)
            self.modifiers.remove(current_key)
            
        return True
    
    def process_mouse_event(self, task):
        """Process mouse events (movement, clicks, drags, scrolls)"""
        event_type = task.get("type", "")
        
        # Handle mouse movement
        if "x" in task and "y" in task and task.get("x") != False and task.get("y") != False:
            x, y = task.get("x"), task.get("y")
            
            # Skip 0,0 coordinates which are often invalid
            if x == 0 and y == 0:
                return True
                
            # Move mouse with a slight duration for more natural movement
            logger.info(f"Moving mouse to ({x}, {y})")
            pyautogui.moveTo(x, y, duration=0.05)
            self.stats["mouseMoveCount"] += 1
        
        # Handle mouse button press (down)
        if task.get("down") == True:
            # Determine which mouse button to use
            button = 'left'  # Default
            if task.get("button"):
                button_str = task.get("button").lower()
                if 'right' in button_str:
                    button = 'right'
                elif 'middle' in button_str:
                    button = 'middle'
            
            logger.info(f"Mouse down with {button} button")
            
            # Apply any active modifiers first
            mults_keys = task.get("mults_keys", [])
            for key in mults_keys:
                if key in ['shift', 'ctrl', 'alt', 'cmd'] and key not in self.modifiers:
                    logger.info(f"Pressing modifier for mouse action: {key}")
                    pyautogui.keyDown(key)
                    self.modifiers.add(key)
            
            # Press mouse button down
            pyautogui.mouseDown(button=button)
            self.mouse_down = True
            self.stats["mouseClickCount"] += 1
            
            # Note: We don't release modifiers yet as they might be needed for the drag
        
        # Handle mouse button release (up)
        elif task.get("up") == True and self.mouse_down:
            # Determine which mouse button was used
            button = 'left'  # Default
            if task.get("button"):
                button_str = task.get("button").lower()
                if 'right' in button_str:
                    button = 'right'
                elif 'middle' in button_str:
                    button = 'middle'
            
            logger.info(f"Mouse up with {button} button")
            
            # Release the mouse button
            pyautogui.mouseUp(button=button)
            self.mouse_down = False
            
            # Release any modifiers that are no longer needed
            mults_keys = task.get("mults_keys", [])
            for key in list(self.modifiers):
                if key not in mults_keys:
                    logger.info(f"Releasing modifier after mouse action: {key}")
                    pyautogui.keyUp(key)
                    self.modifiers.remove(key)
            
            # Count as drag if drag_end is True
            if task.get("drag_end") == True:
                self.stats["dragCount"] += 1
        
        # Handle scroll events
        elif task.get("scroll") is not None:
            scroll_amount = task.get("scroll")
            # Adjust the multiplier to control scroll speed/sensitivity
            scroll_multiplier = 5
            clicks = int(scroll_amount * scroll_multiplier)
            
            logger.info(f"Scrolling: {clicks} clicks")
            
            # Apply any active modifiers for scrolling
            mults_keys = task.get("mults_keys", [])
            active_modifiers = []
            
            for key in mults_keys:
                if key in ['shift', 'ctrl', 'alt', 'cmd'] and key not in self.modifiers:
                    logger.info(f"Pressing modifier for scroll: {key}")
                    pyautogui.keyDown(key)
                    active_modifiers.append(key)
            
            # Perform the scroll
            pyautogui.scroll(clicks)
            self.stats["scrollCount"] += 1
            
            # Release any modifiers that were just for this scroll
            for key in active_modifiers:
                if key not in self.modifiers:  # Only release if it wasn't already held
                    logger.info(f"Releasing modifier after scroll: {key}")
                    pyautogui.keyUp(key)
        
        return True
    
    def replay(self):
        """Replay the recorded input events"""
        if not self.load_data():
            return False
        
        logger.info("Starting replay in 3 seconds...")
        for i in range(3, 0, -1):
            logger.info(f"{i}...")
            time.sleep(1)
        
        logger.info("Replay started!")
        
        # Sort timestamps to ensure chronological order
        timestamps = sorted([int(t) for t in self.data.keys()])
        
        try:
            # Main replay loop
            for i in timestamps:
                t = str(i)
                if t not in self.data:
                    continue
                
                task = self.data[t]
                event_type = task.get("type", "")
                
                # Process keyboard input
                if event_type == "keypress":
                    self.process_keyboard_input(task)
                
                # Process keyboard release
                elif event_type == "keyrelease":
                    self.process_keyboard_release(task)
                
                # Process mouse events
                else:
                    self.process_mouse_event(task)
                
                # Add a small sleep between actions to avoid overwhelming the system
                time.sleep(0.01)
            
            logger.info("Replay completed successfully!")
            
        except KeyboardInterrupt:
            logger.warning("Replay interrupted by user.")
        except Exception as e:
            logger.error(f"Error during replay: {e}")
        finally:
            # Cleanup: ensure all modifiers are released
            self.cleanup()
            
        # Print final stats
        self.print_stats()
        
        return True
    
    def cleanup(self):
        """Release all held keys and buttons"""
        # Release any held mouse buttons
        if self.mouse_down:
            logger.info("Releasing mouse button")
            pyautogui.mouseUp()
            self.mouse_down = False
        
        # Release all modifier keys
        for mod in self.modifiers:
            logger.info(f"Releasing modifier key: {mod}")
            pyautogui.keyUp(mod)
        self.modifiers.clear()
        
        # Additional safety measure
        for mod in ['ctrl', 'alt', 'shift', 'command', 'win']:
            pyautogui.keyUp(mod)
    
    def print_stats(self):
        """Print replay statistics"""
        logger.info("=== Replay Statistics ===")
        logger.info(f"Key presses: {self.stats['keyCount']}")
        logger.info(f"Hotkey combinations: {self.stats['hotkeyCount']}")
        logger.info(f"Mouse clicks: {self.stats['mouseClickCount']}")
        logger.info(f"Mouse movements: {self.stats['mouseMoveCount']}")
        logger.info(f"Scrolls: {self.stats['scrollCount']}")
        logger.info(f"Drags: {self.stats['dragCount']}")

def main():
    try:
        replayer = InputReplay()
        replayer.replay()
    except KeyboardInterrupt:
        print("\nProgram interrupted by user.")
    except Exception as e:
        print(f"Error occurred: {e}")

if __name__ == "__main__":
    main()