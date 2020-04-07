import ctypes
import time
import os
import pynput
import tkinter
from tkinter import ttk

import key_translation

PROCESS_PER_MONITOR_DPI_AWARE = 2
movementFraction = 100.0
fileExtension = ".mr"

class Recording:
    
    def __init__(self):
        self.events = []
        self.lastEventTime = time.time()
        
    def ClearRecording(self):
        self.events = []
        self.lastEventTime = time.time()
        
    def AddEventFromText(self, text):
        parameters = (text.strip()).split(" ")
        if len(parameters) == 5:
            self.AddMouseEventFromText(parameters)
        else:
            self.AddKeyboardEventFromText(parameters)    
    
    def AddKeyboardEvent(self, key, pressed, delayTime = None):
        eventTime = time.time()
        if delayTime == None:
            delayTime = eventTime - self.lastEventTime
        self.lastEventTime = eventTime
        event = KeyboardEvent(delayTime, key, pressed)
        self.events.append(event)
    
    def AddKeyboardEventFromText(self, params):
        [delay, key, pressed] = params
        delay = float(delay)
        key = key_translation.textToKey[key] if key in key_translation.textToKey else pynput.keyboard.KeyCode.from_char(key)
        pressed = True if pressed == "True" else False
        self.AddKeyboardEvent(key, pressed, delay)
        
    def AddMouseEvent(self, button, pressed, x, y, delayTime = None):
        eventTime = time.time()
        if delayTime == None:
            delayTime = eventTime - self.lastEventTime
        self.lastEventTime = eventTime
        event = MouseEvent(delayTime, button, pressed, x, y)
        self.events.append(event)
        
    def AddMouseEventFromText(self, params):
        [delay, button, pressed, x, y] = params
        delay = float(delay)
        button = key_translation.textToButton[button]
        pressed = True if pressed == "True" else False
        x = int(x)
        y = int(y)
        self.AddMouseEvent(button, pressed, x, y, delay)
        
    def GetEvents(self):
        return self.events
    
    def Playback(self):
        pressedKeys = []
        pressedMouse = []
        keyboard = pynput.keyboard.Controller()
        mouse = pynput.mouse.Controller()
        for event in self.GetEvents():
            if type(event) == KeyboardEvent:
                event.Playback(keyboard)
                key = event.GetKey()
                if event.GetKeyPressed() and key not in pressedKeys:
                    pressedKeys.append(key)
                elif not event.GetKeyPressed() and key in pressedKeys:
                    pressedKeys.remove(key)
            else:
                event.Playback(mouse)
                button = event.GetButton()
                if event.GetButtonPressed() and button not in pressedMouse:
                    pressedMouse.append(button)
                elif not event.GetButtonPressed() and button in pressedMouse:
                    pressedMouse.remove(button)
        for key in pressedKeys:
            keyboard.release(key)
        for button in pressedMouse:
            mouse.release(button)
        
    def PrintRecording(self):
        counter = 0
        for event in self.GetEvents():
            print("Event", counter)
            event.PrintEvent()
            counter += 1
    
class KeyboardEvent:
    
    delayTime = 0
    key = None
    pressed = False
    
    def __init__(self, delayTime, key, pressed):
        self.delayTime = delayTime
        self.key = key
        self.pressed = pressed
        
    def GetDelayTime(self):
        return self.delayTime
    
    def GetKey(self):
        return self.key
    
    def GetKeyPressed(self):
        return self.pressed
    
    def GetKeyType(self):
        return type(self.key)
    
    def GetKeyLabel(self):
        if self.GetKeyType() == pynput.keyboard.KeyCode:
            return self.GetKey().char
        return key_translation.keyToText[self.key]
    
    def Playback(self, keyboard):
        time.sleep(self.GetDelayTime())
        if self.GetKeyPressed():
            keyboard.press(self.GetKey())
        else:
            keyboard.release(self.GetKey())
            
    def GetFileText(self):
        return " ".join([str(self.GetDelayTime()), self.GetKeyLabel(), str(self.GetKeyPressed())]) + "\n" 
    
    def PrintEvent(self):
        print("Delay Time:", self.GetDelayTime())
        print("Key:", self.GetKeyLabel())
        print("Pressed:", self.GetKeyPressed())
    
class MouseEvent:
    
    delayTime = 0
    button = None
    pressed = False
    position = (0, 0)
    
    def __init__(self, delayTime, button, pressed, x, y):
        self.delayTime = delayTime
        self.button = button
        self.pressed = pressed
        self.position = (x, y)
        
    def GetDelayTime(self):
        return self.delayTime
    
    def GetButton(self):
        return self.button
    
    def GetButtonPressed(self):
        return self.pressed
    
    def GetPosition(self):
        return self.position
    
    def GetButtonLabel(self):
        return key_translation.buttonToText[self.button]
    
    def Playback(self, mouse):
        (startingX, startingY) = mouse.position
        dx = (self.GetPosition()[0] - startingX) / movementFraction
        dy = (self.GetPosition()[1] - startingY) / movementFraction
        intDelay = self.GetDelayTime() / movementFraction

        for interval in range(int(movementFraction)):
            time.sleep(intDelay)
            mouse.position = (startingX + (dx * interval), startingY + (dy * interval))
        mouse.position = self.GetPosition()
        if self.GetButtonPressed():
            mouse.press(self.GetButton())
        else:
            mouse.release(self.GetButton())
            
    def GetFileText(self):
        return " ".join([str(self.GetDelayTime()), self.GetButtonLabel(), str(self.GetButtonPressed()), str(self.GetPosition()[0]), str(self.GetPosition()[1])]) + "\n"
    
    def PrintEvent(self):
        print("Delay Time:", self.GetDelayTime())
        print("Button:", self.GetButtonLabel())
        print("Pressed:", self.GetButtonPressed())
        print("Position:", self.GetPosition())

class Dialog:
    
    # self.loadedRecording
    # self.window
    # self.gridContainer
    # self.gridCanvas
    # self.gridScrollbar
    # self.gridScrollableFrame
    # self.recordingGrid
    # self.buttonFrame
    # self.recordButton
    # self.playButton
    # self.saveButton
    # self.loadButton
    
    def __init__(self):
        
        self.loadedRecording = Recording()
        
        self.window = tkinter.Tk()
        self.window.title("Do not believe everything you see when you're talking to me, Scam Likely~~") 
        self.gridContainer = tkinter.Frame(self.window)
        self.gridCanvas = tkinter.Canvas(self.gridContainer)
        self.gridScrollbar = tkinter.Scrollbar(self.gridContainer, orient = "vertical", command = self.gridCanvas.yview)
        self.gridScrollableFrame = tkinter.Frame(self.gridCanvas)
        self.gridScrollableFrame.bind("<Configure>", lambda e: self.gridCanvas.configure(scrollregion = self.gridCanvas.bbox("all")))
        self.gridCanvas.create_window((0, 0), window = self.gridScrollableFrame, anchor = "nw")
        self.gridCanvas.configure(yscrollcommand = self.gridScrollbar.set)
        self.recordingGrid = []
        
        width = 4
        height = 100
        for row in range(height):
            recordingRow = []
            for column in range(width):
                text = tkinter.Entry(scrollableFrame, width = 15, state = "normal")
                text.grid(column = column, row = row)
                recordingRow.append(text)
            self.recordingGrid.append(recordingRow)
        
        self.gridContainer.grid(column = 0, row = 0)
        self.gridCanvas.pack(side = "left", fill = "both", expand = True)
        self.gridScrollbar.pack(side = "right", fill = "y")
        
        window.update()
        
        self.buttonFrame = tkinter.Frame(self.window, width = self.gridContainer.winfo_width(), height = self.gridContainer.winfo_height())
        self.buttonFrame.grid(column = 1, row = 0)      
        
        self.recordButton = tkinter.Button(self.buttonFrame, text = "Record", command = lambda: BeginRecording(self.loadedRecording))
        self.recordButton.grid(column = 0, row = 0)
        
        self.playButton = tkinter.Button(self.buttonFrame, text = "Playback", command = lambda: self.loadedRecording.Playback())
        self.playButton.grid(column = 1, row = 0)
        
        self.saveButton = tkinter.Button(self.buttonFrame, text = "Save", command = lambda: SaveRecording(self.loadedRecording))
        self.saveButton.grid(column = 0, row = 1)
        
        self.loadButton = tkinter.Button(self.buttonFrame, text = "Load", command = lambda: LoadRecording(self.loadedRecording))
        self.loadButton.grid(column = 1, row = 1)        

        # Records mouse and keyboard clicks into an events array and returns it
        def BeginRecording(self):
            print("Beginning recording, press 'q' to stop")
            self.loadedRecording.ClearRecording()
            
            pressedMouse = []
            pressedKeys = []
            
            # Function for tracking a keyboard button press
            def on_press(key):
                nonlocal pressedKeys
                if key in pressedKeys:
                    return True
                pressedKeys.append(key)
                return RegisterKeystroke(key, True)
                
            # Function for tracking a keyboard button release
            def on_release(key):
                nonlocal pressedKeys
                if key not in pressedKeys:
                    return True
                pressedKeys.remove(key)
                return RegisterKeystroke(key, False)
                
            # Function for recording a keyboard event
            def RegisterKeystroke(key, pressed):
                if type(key) == pynput.keyboard.KeyCode and key.char == 'q':
                    return False
                nonlocal recording
                self.loadedRecording.AddKeyboardEvent(key, pressed)
                return True
            
            # Function for recording a mouse button click
            def on_click(x, y, button, pressed):
                nonlocal pressedMouse, recording
                if pressed:
                    if button not in pressedMouse:
                        pressedMouse.append(button)
                    else:
                        return True
                else:
                    if button in pressedMouse:
                        pressedMouse.remove(button)
                    else:
                        return True
                self.loadedRecording.AddMouseEvent(button, pressed, x, y)
                  
            
            # Begins the recording here, stops when on_click or on_press returns False
            with pynput.mouse.Listener(on_click = on_click) as listener:
                with pynput.keyboard.Listener(on_press = on_press, on_release = on_release) as listener:
                    listener.join()
                    
            print("Recording has been completed")
 
        def SaveRecording(self):    
            if len(self.loadedRecording.GetEvents()) == 0:
                print("There is no recorded program")
                return
            name = input("Please name the recording: ")
            if os.path.exists(name + fileExtension):
                fileID = 1
                while os.path.exists(name + "_" + str(fileID) + fileExtension):
                    fileID += 1
                name = name + "_" + str(fileID)
            file = open(name + fileExtension, "x")
            for event in self.loadedRecording.GetEvents():
                file.write(event.GetFileText())
            file.close()

        def LoadRecording(self):  
            name = input("Load which recording?: ")
            if not os.path.exists(name + fileExtension):
                print("Could not find recorded program named", name)
                return
            self.loadedRecording.ClearRecording()
            file = open(name + fileExtension, "r")
            readEvents = file.readlines()
            for event in readEvents:
                self.loadedRecording.AddEventFromText(event)
            file.close()
    
def ReplaceText(field, text):
    field.delete(0, END)
    field.insert(0, text)
    
def PopulateTextGrid(grid, events):
    for event in events:
        for row in grid:
            if type(event) == KeyboardEvent:
                ReplaceText(row[0], "Keyboard")
                ReplaceText(row[1], event.GetKeyLabel())
                ReplaceText(row[2], event.GetKeyPressed())
                ReplaceText(row[3], event.GetDelayTime())
            else:
                ReplaceText(row[0], "Mouse")
                ReplaceText(row[1], event.GetButtonLabel())
                ReplaceText(row[2], str(event.GetButtonPressed()) + str(event.GetPosition()))
                ReplaceText(row[3], event.GetDelayTime()) 

if __name__ == "__main__":
    
    ctypes.windll.shcore.SetProcessDpiAwareness(PROCESS_PER_MONITOR_DPI_AWARE)    
    loadedRecording = Recording()
    
    
    """
    
    window.geometry("500x300")
    label = tkinter.Label(window, text = "Hi hungry, I'm dad", font = ("Impact", 50))
    label.grid(column = 0, row = 0)
    
    text = tkinter.Entry(window, width = 30, state = "normal")
    text.bind("<Return>", lambda _: SenpaiTouchedMe(label, text))
    text.grid(column = 0, row = 2)
    text.focus()
    
    button = tkinter.Button(window, text = "Touch me, senpai", font = ("Comic Sans MS", 30), bg = "black", fg="blue", command = lambda: SenpaiTouchedMe(label, text))
    button.grid(column = 0, row = 1)
    
    combo = ttk.Combobox(window)
    combo["values"] = ("doo", "doo doo", "do do", "do do do do")
    combo.current(1)
    combo.grid(column = 1, row = 0)
    
    checkState = tkinter.BooleanVar()
    checkState.set(True)
    check = ttk.Checkbutton(window, text = "Pick me mommy", var = checkState)
    check.grid(column = 1, row = 1)
    
    radio = ttk.Radiobutton(window, text = "No, pick me", value = 1)
    radio2 = ttk.Radiobutton(window, text = "But I'm the best one", value = 2)
    radio3 = ttk.Radiobutton(window, text = "I am the best tho", value = 3)
    radio.grid(column = 2, row = 0)
    radio2.grid(column = 2, row = 1)
    radio3.grid(column = 2, row = 2)
    """
    
    window.mainloop()
    
    exit(0)

