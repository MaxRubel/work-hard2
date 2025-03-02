import pyautogui
import time
import json
import random
import string

# Fail-safe feature - move mouse to upper left corner to abort
pyautogui.FAILSAFE = True

# Function to process hotkeys and keyboard input
def process_keyboard_input(task):
    """Handle keyboard input including hotkey combinations"""
    # Check if there are multiple keys pressed (hotkey combination)
    if task.get("mults_keys") and len(task.get("mults_keys")) > 0:
        # Get the current key being pressed
        current_key = task.get("k")
        
        # Get all active modifier keys
        modifiers = []
        normal_keys = []
        
        for key in task.get("mults_keys"):
            # Clean up the key representation
            clean_key = key
            if isinstance(key, str) and key.startswith("Key."):
                clean_key = key.split("Key.")[1]
            
            # Categorize as modifier or normal key
            if clean_key in ['ctrl', 'alt', 'shift', 'cmd', 'command', 'win']:
                modifiers.append(clean_key)
            else:
                normal_keys.append(clean_key)
        
        # Add the current key if it's not already in the lists
        if current_key and current_key not in modifiers and current_key not in normal_keys:
            # Check if it's a special key
            if isinstance(current_key, str) and current_key.startswith("Key."):
                clean_current = current_key.split("Key.")[1]
                if clean_current in ['ctrl', 'alt', 'shift', 'cmd', 'command', 'win']:
                    modifiers.append(clean_current)
                else:
                    normal_keys.append(clean_current)
            else:
                normal_keys.append(current_key)
        
        # If we have at least one modifier and one normal key, it's a hotkey combination
        if modifiers and (normal_keys or current_key):
            print(f"Executing hotkey: {'+'.join(modifiers)}+{'+'.join(normal_keys if normal_keys else [current_key])}")
            
            # Hold down all modifiers
            for mod in modifiers:
                pyautogui.keyDown(mod)
            
            # Press all normal keys
            for key in normal_keys:
                if key not in modifiers:  # Skip if it's also a modifier
                    pyautogui.press(key)
            
            # If the current key isn't in normal_keys and isn't a modifier, press it
            if current_key and current_key not in normal_keys and current_key not in modifiers:
                # Check if it's a special key
                if isinstance(current_key, str) and current_key.startswith("Key."):
                    clean_current = current_key.split("Key.")[1]
                    pyautogui.press(clean_current)
                else:
                    pyautogui.press(current_key)
            
            # Release all modifiers in reverse order
            for mod in reversed(modifiers):
                pyautogui.keyUp(mod)
                
            return True
    
    # Regular key press (not part of a hotkey)
    if task.get("k") is not None and task.get("k") != False:
        try:
            # Check if it's a special key representation
            if isinstance(task["k"], str) and task["k"].startswith("Key."):
                # Extract the key name after "Key."
                key_name = task["k"].split("Key.")[1]
                print(f"Pressing special key: {key_name}")
                pyautogui.press(key_name)
            else:
                # Regular character
                print(f"Typing key: {task['k']}")
                pyautogui.write(task["k"])
            return True
        except Exception as e:
            print(f"Error typing key {task['k']}: {e}")
    
    return False

def main():
    print("Get ready to work super hard!")
    time.sleep(3)
    
    # load user input data:
    with open('input_data.json', 'r') as file:
        data = json.load(file)
    
        
    keyCount = 0
    hotkeyCount = 0
    scrollCount = 0
    mouse_down = False  # Track if mouse button is currently pressed down
        
    # Sort timestamps to ensure chronological order
    timestamps = sorted([int(t) for t in data.keys()])
    
    # main loop
    for i in timestamps:
        t = str(i)
        if t not in data:
            continue
        
        task = data[t]
        
        # Handle mouse movement
        if task.get("x") != False:
            if task.get("x", 0) == 0 and task.get("y", 0) == 0:
                continue
            # Move mouse to position with slight duration to make it more natural
            pyautogui.moveTo(task["x"], task["y"], duration=0.05)
        
        # Handle mouse button down (start highlighting)
        if task.get("down") == True:
            mouse_down = True
            
            # Check if we need to use a specific mouse button
            button = 'left'  # Default to left button
            if task.get("button"):
                button_str = task.get("button").lower()
                if 'right' in button_str:
                    button = 'right'
                elif 'middle' in button_str:
                    button = 'middle'
            
            # Check for modifiers during mouse down
            if task.get("mults_keys") and len(task.get("mults_keys")) > 0:
                modifiers = []
                for key in task.get("mults_keys"):
                    if isinstance(key, str) and key.startswith("Key."):
                        clean_key = key.split("Key.")[1]
                        if clean_key in ['ctrl', 'alt', 'shift']:
                            modifiers.append(clean_key)
                    elif key in ['ctrl', 'alt', 'shift']:
                        modifiers.append(key)
                
                # Hold modifiers before mouse click
                for mod in modifiers:
                    pyautogui.keyDown(mod)
                
                pyautogui.mouseDown(button=button)
                
                # Don't release modifiers yet - they might be needed for the drag
            else:
                pyautogui.mouseDown(button=button)
        
        # Handle mouse button up (finish highlighting)
        elif task.get("up") == True or (task.get("c") == True and mouse_down):
            if mouse_down:
                # Check for modifiers during mouse up
                has_modifiers = False
                if task.get("mults_keys") and len(task.get("mults_keys")) > 0:
                    modifiers = []
                    for key in task.get("mults_keys"):
                        if isinstance(key, str) and key.startswith("Key."):
                            clean_key = key.split("Key.")[1]
                            if clean_key in ['ctrl', 'alt', 'shift']:
                                modifiers.append(clean_key)
                        elif key in ['ctrl', 'alt', 'shift']:
                            modifiers.append(key)
                    
                    has_modifiers = bool(modifiers)

                pyautogui.mouseUp()
                mouse_down = False
                
                # Release any modifiers after mouse up
                if has_modifiers:
                    for mod in reversed(modifiers):
                        pyautogui.keyUp(mod)
            else:
                # This is a regular click, not ending a drag
                button = 'left'  # Default to left button
                if task.get("button"):
                    button_str = task.get("button").lower()
                    if 'right' in button_str:
                        button = 'right'
                    elif 'middle' in button_str:
                        button = 'middle'
                
                # Check for modifiers during click
                if task.get("mults_keys") and len(task.get("mults_keys")) > 0:
                    modifiers = []
                    for key in task.get("mults_keys"):
                        if isinstance(key, str) and key.startswith("Key."):
                            clean_key = key.split("Key.")[1]
                            if clean_key in ['ctrl', 'alt', 'shift']:
                                modifiers.append(clean_key)
                        elif key in ['ctrl', 'alt', 'shift']:
                            modifiers.append(key)
                    
                    # Hold modifiers, click, then release
                    for mod in modifiers:
                        pyautogui.keyDown(mod)
                    
                    pyautogui.click(button=button)                    
                    for mod in reversed(modifiers):
                        pyautogui.keyUp(mod)
                else:
                    pyautogui.click(button=button)
        
        # Handle keyboard input
        elif task.get("k") is not None and task.get("k") != False:
            # Process the keyboard input with hotkey support
            keyboard_result = process_keyboard_input(task)
            if keyboard_result:
                keyCount += 1
                if task.get("mults_keys") and len(task.get("mults_keys")) > 0:
                    hotkeyCount += 1
        
        # Handle scroll
        elif task.get("scroll") is not None:
            scroll_amount = task.get("scroll")
            # PyAutoGUI scroll takes positive values for scrolling up (unlike some systems)
            # Adjust the multiplier to control scroll speed/sensitivity
            scroll_multiplier = 5
            clicks = int(scroll_amount * scroll_multiplier)
            
            # Check for modifiers during scroll
            if task.get("mults_keys") and len(task.get("mults_keys")) > 0:
                modifiers = []
                for key in task.get("mults_keys"):
                    if isinstance(key, str) and key.startswith("Key."):
                        clean_key = key.split("Key.")[1]
                        if clean_key in ['ctrl', 'alt', 'shift']:
                            modifiers.append(clean_key)
                    elif key in ['ctrl', 'alt', 'shift']:
                        modifiers.append(key)
                
                if modifiers:
                    # Hold modifiers, scroll, then release
                    for mod in modifiers:
                        pyautogui.keyDown(mod)
                    
                    pyautogui.scroll(clicks)
                    
                    for mod in reversed(modifiers):
                        pyautogui.keyUp(mod)
                    
                    scrollCount += 1
                    continue
            
            pyautogui.scroll(clicks)
            scrollCount += 1
        
        # Add a small sleep between actions to avoid overwhelming the system
        time.sleep(0.01)
        
    # Ensure mouse is released at the end
    if mouse_down:
        pyautogui.mouseUp()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram interrupted by user.")
        # Safety measure: ensure mouse is released
        pyautogui.mouseUp()
        # Safety measure: ensure all modifier keys are released
        for mod in ['ctrl', 'alt', 'shift', 'command', 'win']:
            pyautogui.keyUp(mod)
    except Exception as e:
        print(f"Error occurred: {e}")
        # Safety measure: ensure mouse is released
        pyautogui.mouseUp()
        # Safety measure: ensure all modifier keys are released
        for mod in ['ctrl', 'alt', 'shift', 'command', 'win']:
            pyautogui.keyUp(mod)