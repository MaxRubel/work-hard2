import pyautogui
import time
import json
import random
import string

# Fail-safe feature - move mouse to upper left corner to abort
pyautogui.FAILSAFE = True
        
def main():
    print("Get ready to highlight text! Starting in 3 seconds...")
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
                 
        # Handle mouse movement
        if task["x"] != False:
            if task["x"] == 0 and task["y"] == 0:
                continue
            # Move mouse to position with slight duration to make it more natural
            pyautogui.moveTo(task["x"], task["y"], duration=0.05)
        
        # Handle mouse button down (start highlighting)
        if task.get("down") == True:
            mouse_down = True
            pyautogui.mouseDown()
            print(f"Mouse DOWN at position ({task['x']}, {task['y']})")
            
        # Handle mouse button up (finish highlighting)
        elif task.get("up") == True or (task.get("c") == True and mouse_down):
            if mouse_down:
                pyautogui.mouseUp()
                mouse_down = False
                print(f"Mouse UP at position ({task['x']}, {task['y']})")
            else:
                pyautogui.click()
                print(f"Clicked at position ({task['x']}, {task['y']})")
            
        # Handle keyboard input
        elif task.get("k") != False and task.get("k") is not None:
            try:
                # Check if it's a special key representation
                if isinstance(task["k"], str) and task["k"].startswith("Key."):
                    # Extract the key name after "Key."
                    key_name = task["k"].split("Key.")[1]
                    pyautogui.press(key_name)
                else:
                    # Regular character
                    pyautogui.write(task["k"])
                
                keyCount += 1
            except Exception as e:
                print(f"Error typing key {task['k']}: {e}")

        elif task.get("scroll") is not None:
            scroll_amount = task.get("scroll")
            # PyAutoGUI scroll takes positive values for scrolling up (unlike some systems)
            # Adjust the multiplier to control scroll speed/sensitivity
            scroll_multiplier = 5
            clicks = int(scroll_amount * scroll_multiplier)
            
            print(f"Scrolling {'up' if clicks > 0 else 'down'} by {abs(clicks)} clicks")
            pyautogui.scroll(clicks)
            scrollCount += 1

        # Add a small sleep between actions to avoid overwhelming the system
        time.sleep(0.01)
    
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