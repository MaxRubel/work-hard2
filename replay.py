import pyautogui
import time
import json
import random
import string

# Fail-safe feature - move mouse to upper left corner to abort
pyautogui.FAILSAFE = True

# Set the time interval between events (in seconds)
TIME_INTERVAL = 0.01
        
def main():
    print("Get ready to replay input actions! Starting in 3 seconds...")
    time.sleep(3)
    
    # load user input data:
    with open('input_data.json', 'r') as file:
        data = json.load(file)    

    # load sample file to type (if needed):
    try:
        with open('sampleDocument.txt', 'r') as file:
            document = file.read()
    except FileNotFoundError:
        print("Sample document not found, continuing without it.")
        document = ""
        
    keyCount = 0
    scrollCount = 0
    mouse_down = False  # Track if mouse button is currently pressed down
    
    print(f"Found {len(data)} events to process")
    
    # Sort timestamps to ensure chronological order
    timestamps = sorted([int(t) for t in data.keys()])
    
    # main loop
    for i in timestamps:
        t = str(i)
        if t not in data:
            continue

        task = data[t]
        
        # Log significant events
        if task.get("down") == True or task.get("up") == True or task.get("c") == True:
            print(f"Time {t}: Mouse event - down:{task.get('down')}, up:{task.get('up')}, c:{task.get('c')}")
         
        # Handle mouse movement
        if task.get("x") != False:
            if task.get("x") == 0 and task.get("y") == 0:
                continue
            # Move mouse to position with slight duration to make it more natural
            pyautogui.moveTo(task.get("x"), task.get("y"), duration=0.01)
        
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
                # Check if it's a special key representation
                if isinstance(task.get("k"), str) and task.get("k").startswith("Key."):
                    # Extract the key name after "Key."
                    key_name = task.get("k").split("Key.")[1]
                    
                    # Map key names to pyautogui format
                    key_mapping = {
                        'shift': 'shift',
                        'ctrl': 'ctrl',
                        'alt': 'alt',
                        'cmd': 'command',
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
                        pyautogui.press(key_mapping[key_name])
                    else:
                        pyautogui.press(key_name)
                else:
                    # Regular character - type directly
                    pyautogui.write(task.get("k"))
                
                keyCount += 1
            except Exception as e:
                print(f"Error typing key {task.get('k')}: {e}")

        # Use a fixed time interval between actions
        time.sleep(TIME_INTERVAL)
    
    print(f"Simulation complete! Processed {keyCount} keystrokes and {len(timestamps)} events.")
    
    # Ensure mouse is released at the end
    if mouse_down:
        pyautogui.mouseUp()
        print("Released mouse button at end of simulation")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram interrupted by user.")
        # Safety measure: ensure mouse is released
        pyautogui.mouseUp()
    except Exception as e:
        print(f"Error occurred: {e}")
        # Safety measure: ensure mouse is released
        pyautogui.mouseUp()