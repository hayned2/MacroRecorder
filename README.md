# MacroRecorder

A recorder that will record the user's mouse and keyboard strokes for a time, then be able to play that same recording back.

### Prerequesites

To run the actual code, Python 3.0 is required, along with the packages [ctypes, pynput, tkinter, ast]

A windows executable has been included in the *dist* directory, which does not require Python to run.

### How to Use

Run the program to get to the interface.

**Record** will begin your recording. This will minimize the window. To stop the recording, you click the Stop hotkey, which by default is the right_alt button.

**Playback** will playback the currently loaded recording according to the number of loops. You can click the Stop hotkey to force the playback to stop before its next input.

**Loops** is the number of times the recording will playback in succession. The default is 1.

**Save** will save the current recording to a file, where the default file extenstion is ".mr" (macro recording).

**Load** will load in a .mr file that can be edited and played back.

**Clear** will clear the currently loaded recording. Be careful, there is no undo on this.

**Stop and Change** is the hotkey that is used to stop recordings and playbacks. By default, this is the right alt key. To change it, click the Change button, and it will listen for the next key press.

**Event Info** contains information about the currently selected event in the Recording Grid on the right.

**Type** is whether it is a mouse event or a keyboard event

**Label** is which mouse button or which keyboard key is the one involved in this event.

**Position** will only show up if the Type is set to Mouse. 

**X1 and Y1** is the top-left corner of the screen coordinates where the mouse event occurs.

**X2 and Y2** is the bottom-right corner of the screen coordinates. By default, this is the same as X1 and Y1. However, if you wish to allow the mouse click to occur anywhere within a specified box region, you can change these values to do so.

**Change** will, depending on whether the Type is set to Mouse or Keyboard, record the next mouse button press or keyboard stroke. This will change the Label for both, as well as the X and Y values for the Mouse position.

**Change X2/Y2** will only change the X2 and Y2 values to the next clicked location on the screen.

**Pressed** determines whether the button is being pressed down (checked) or released (unchecked)

**Delay** determines how long, in seconds, will the event wait to occur. This can occur in a range, thus the two boxes. By default, the delay has no range, and will use the value in the first box for the second box unless specified. Both values must be positive numbers.

**Add Row** will add the current event described in Event Info to the Recording Grid on the right, at the end.

**Update Row** will change the currently selected event in the Recording Grid to the info described in the Event Info.

**Delete** will delete the currently selected event in the Recording Grid. Be careful, as this cannot be undone.

**Up / Down Arrows** will move the currently selected event up and down the Recording Grid.

**Recording Grid** depicts the contents of the current recording. Selecting a row in this grid will automatically update the Event Info panel with its information.

### Creating a New Executable

If you wish to create a new executable for this project, install the pyinstaller package through pip, navigate to the repo directory in cmd, and run the command 
```
pyinstaller --onefile macro.py
```

### Authors

Dan H. (hayned2)
Abi M. (for some bug testing)

### Licensing and Use

This was a personal project, and is intended for personal use. Feel free to use and modify to your heart's content. For any questions or feedback, send an email to hayned2@gmail.com

### Thanks for reading and using! :)
