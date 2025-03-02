import pyautogui
import time
import json
import random
import string

# Fail-safe feature - move mouse to upper left corner to abort
pyautogui.FAILSAFE = True

# Configure PyAutoGUI settings
pyautogui.PAUSE = 0.01  # Add small delay between PyAutoGUI commands for stability

def main():
    print("Get ready to replay input actions! Starting in 3 seconds...")
    time.sleep(2)
    
    # load user input data:
    try:
        with open('input_data.json', 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        print("Error: input_data.json not found!")
        return
    except json.JSONDecodeError:
        print("Error: input_data.json is not valid JSON!")
        return
        
    keyCount = 0
    scrollCount = 0
    mouse_down = False  # Track if mouse button is currently pressed down
    
    # Track currently held keys
    held_keys = set()
    
    print(f"Found {len(data)} events to process")
    
    # Sort timestamps to ensure chronological order
    timestamps = sorted([int(t) for t in data.keys()])
    
    # Group consecutive key presses for text input
    # This helps improve reliability for typing sequences
    text_buffer = ""
    last_was_text = False
    
    # main loop
    for i in range(120000):
        t = str(i)
        if t not in data:
            continue

        task = data[t]
        
        # Check if we need to flush the text buffer
        current_is_text = (task.get("k") is not None and 
                          task.get("k") != False and 
                          not isinstance(task.get("k"), str) or
                          (isinstance(task.get("k"), str) and 
                           not task.get("k").startswith("Key.") and
                           not task.get("key_up") and 
                           not task.get("key_held")))
        
        # If we're switching away from text input or this is the last event,
        # flush the text buffer
        if (text_buffer and not current_is_text) or (text_buffer and i == len(timestamps) - 1):
            if text_buffer:
                print(f"Typing buffered text: '{text_buffer}'")
                # Use interval parameter for more reliable typing
                pyautogui.write(text_buffer, interval=0.03)
                keyCount += len(text_buffer)
                text_buffer = ""
        
        # Log significant mouse events
        if task.get("down") == True or task.get("up") == True or task.get("c") == True:
            print(f"Time {t}: Mouse event - down:{task.get('down')}, up:{task.get('up')}, c:{task.get('c')}")
         
        # Handle mouse movement
        if task.get("x") != False:
            if task.get("x") == 0 and task.get("y") == 0:
                continue
            # Move mouse to position with slight duration to make it more natural
            pyautogui.moveTo(task.get("x"), task.get("y"), duration=0.05)
        
        # Handle mouse button down (start highlighting)
        if task.get("down") == True:
            mouse_down = True
            pyautogui.mouseDown()
            print(f"Mouse DOWN at position ({task.get('x')}, {task.get('y')})")
            
        # Handle mouse button up (finish highlighting)
        elif task.get("up") == True or (task.get("c") == True and mouse_down):
            if mouse_down:
                pyautogui.mouseUp()
                mouse_down = False
                print(f"Mouse UP at position ({task.get('x')}, {task.get('y')})")
            else:
                pyautogui.click()
                print(f"Clicked at position ({task.get('x')}, {task.get('y')})")
        
        # Handle scroll events
        elif task.get("scroll") is not None:
            scroll_amount = task.get("scroll")
            # PyAutoGUI scroll takes positive values for scrolling up (unlike some systems)
            # Adjust the multiplier to control scroll speed/sensitivity
            scroll_multiplier = 5
            clicks = int(scroll_amount * scroll_multiplier)
            
            print(f"Scrolling {'up' if clicks > 0 else 'down'} by {abs(clicks)} clicks")
            pyautogui.scroll(clicks)
            scrollCount += 1
            
        # Handle keyboard input
        elif task.get("k") != False and task.get("k") is not None:
            try:
                key = task.get("k")

                # Handle key release events
                if task.get("key_up") == True:
                    if key.startswith("Key."):
                        key_name = key.split("Key.")[1]
                        
                        # Map key names to pyautogui format
                        key_mapping = {
                            'shift': 'shift',
                            'ctrl': 'ctrl', 
                            'ctrl_l': 'ctrl',
                            'ctrl_r': 'ctrl',
                            'alt': 'alt',
                            'alt_l': 'alt',
                            'alt_r': 'alt',
                            'cmd': 'command',
                            'cmd_r': 'command',
                            'cmd_l': 'command'
                        }
                        
                        if key_name in key_mapping:
                            release_key = key_mapping[key_name]
                        else:
                            release_key = key_name
                        
                        # Release the key
                        if release_key in held_keys:
                            print(f"Releasing key: {release_key}")
                            pyautogui.keyUp(release_key)
                            held_keys.remove(release_key)
                    elif key in held_keys:
                        print(f"Releasing key: {key}")
                        pyautogui.keyUp(key)
                        held_keys.remove(key)
                
                # Handle key press events
                else:
                    # Handle special keys
                    if isinstance(key, str) and key.startswith("Key."):
                        # Extract the key name after "Key."
                        key_name = key.split("Key.")[1]
                        
                        # Map key names to pyautogui format
                        key_mapping = {
                            'shift': 'shift',
                            'ctrl': 'ctrl',
                            'ctrl_l': 'ctrl',
                            'ctrl_r': 'ctrl',
                            'alt': 'alt',
                            'alt_l': 'alt',
                            'alt_r': 'alt',
                            'cmd': 'command',
                            'cmd_r': 'command',
                            'cmd_l': 'command',
                            'enter': 'enter',
                            'space': 'space',
                            'tab': 'tab',
                            'backspace': 'backspace',
                            'esc': 'escape',
                            'up': 'up',
                            'down': 'down',
                            'left': 'left',
                            'right': 'right',
                            'delete': 'delete',
                            'home': 'home',
                            'end': 'end',
                            'page_up': 'pageup',
                            'page_down': 'pagedown'
                        }
                        
                        if key_name in key_mapping:
                            mapped_key = key_mapping[key_name]
                        else:
                            mapped_key = key_name
                        
                        # Check if this is a modifier key or should be held
                        is_modifier = key_name in ['shift', 'ctrl', 'ctrl_l', 'ctrl_r', 'alt', 'alt_l', 'alt_r', 'cmd', 'cmd_l', 'cmd_r']
                        
                        if is_modifier or task.get("key_held") == True:
                            if mapped_key not in held_keys:
                                print(f"Holding down key: {mapped_key}")
                                pyautogui.keyDown(mapped_key)
                                held_keys.add(mapped_key)
                        else:
                            # For non-modifier special keys, press directly with a slight delay
                            print(f"Pressing special key: {mapped_key}")
                            pyautogui.press(mapped_key)
                            time.sleep(0.03)  # Add extra delay after special keys
                    else:
                        # Regular character
                        if task.get("key_held") == True:
                            # Hold the key down
                            if key not in held_keys:
                                print(f"Holding down character: {key}")
                                pyautogui.keyDown(key)
                                held_keys.add(key)
                        else:
                            # Buffer the character for more reliable typing
                            text_buffer += key
                            last_was_text = True
                
                if not current_is_text:
                    keyCount += 1
                    
            except Exception as e:
                print(f"Error handling key {task.get('k')}: {e}")
                # Try to recover by flushing the buffer
                if text_buffer:
                    pyautogui.write(text_buffer, interval=0.05)
                    text_buffer = ""

        # Add a small sleep between actions to avoid overwhelming the system
        # This value can be adjusted based on the reliability of replay
        time.sleep(.1)
    
    # Flush any remaining text in the buffer
    if text_buffer:
        print(f"Typing final buffered text: '{text_buffer}'")
        pyautogui.write(text_buffer, interval=0.03)
        keyCount += len(text_buffer)
    
    # Release any keys still being held at the end
    for key in held_keys:
        print(f"Releasing held key at end: {key}")
        pyautogui.keyUp(key)
    
    print(f"Simulation complete! Processed {keyCount} keystrokes, {scrollCount} scroll events, and {len(timestamps)} total events.")
    
    # Ensure mouse is released at the end
    if mouse_down:
        pyautogui.mouseUp()
        print("Released mouse button at end of simulation")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram interrupted by user.")
        # Safety measures
        pyautogui.mouseUp()
        
        # Also release any commonly held keys as a precaution
        for key in ['shift', 'ctrl', 'alt', 'command']:
            try:
                pyautogui.keyUp(key)
            except:
                pass
    except Exception as e:
        print(f"Error occurred: {e}")
        # Safety measures
        pyautogui.mouseUp()
        for key in ['shift', 'ctrl', 'alt', 'command']:
            try:
                pyautogui.keyUp(key)
            except:
                pass