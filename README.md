# Bodysteer - Steer A Game Using Your Webcam and Tilting Your Body

This project allows you to steer your character by tilting your body, using input from a standard webcam. It detects body landmarks (shoulders) via MediaPipe, calculates the tilt angle, and translates it into virtual gamepad input using vJoy and XOutput.

This provides a hands-free steering solution, ideal for use with spin bikes and other fitness equipment connected via ANT+/Bluetooth sensors for speed/cadence.

![alt text](http://github.com/cheneryal/images/ui.png)

## Features

*   Hands-free steering using body tilt.
*   Uses standard webcam, no special hardware required.
*   Real-time pose estimation via Google MediaPipe.
*   Outputs to a virtual DirectInput device (vJoy).
*   Uses XOutput to translate DirectInput to XInput for game compatibility.
*   Configurable sensitivity and deadzone via script parameters.

## Prerequisites

Before you begin, ensure you have the following hardware and software:

**Hardware:**

*   A PC capable of running the game and Python script simultaneously.
*   A standard webcam positioned to see your upper body/shoulders clearly.
*   Your bike setup with Bluetooth/ANT+ sensors (e.g. for Zwift or GTBikeV).

**Software:**

1.  **Python:** Version 3.7+ recommended. [Download Python](https://www.python.org/downloads/) (Make sure to check "Add Python to PATH" during installation).
2.  **vJoy Driver:** Creates the virtual DirectInput joystick. [Download vJoy](https://github.com/jshafer817/vJoy/releases) (Install this driver *first*).
3.  **ViGEmBus Driver:** Required by XOutput to create virtual Xbox controllers. [Download ViGEmBus](https://github.com/ViGEm/ViGEmBus/releases) (Install this driver *before* using XOutput).
4.  **XOutput:** Translates vJoy's DirectInput to XInput. [Download XOutput](https://github.com/csutorasa/XOutput/releases) (Download the application).
5.  **Git:** (Optional, for cloning the repository). [Download Git](https://git-scm.com/downloads/).

## Installation

1.  **Clone Repository:**
    Open a terminal or command prompt and clone this repository:
    ```bash
    git clone https://github.com/cheneryal/bodysteer.git
    cd Bodysteer
    ```
    *(Alternatively, download the ZIP file from GitHub and extract it.)*

2.  **Install Drivers:**
    *   Install the **vJoy driver**.
    *   Install the **ViGEmBus driver**.

3.  **Set up Python Environment (Recommended):**
   
    ```bash
    python -m venv venv
    # Activate the environment:
    # Windows:
    venv\Scripts\activate
    # macOS/Linux:
    # source venv/bin/activate
    ```

4.  **Install Python Dependencies:**
    Install the required Python libraries using the `requirements.txt` file:
    ```bash
    python -m pip install -r requirements.txt
    ```

5.  **Place XOutput:**
    Place the downloaded `XOutput.exe` file somewhere convenient (it doesn't need to be in the project folder, but you need to know where it is).

## Configuration

1.  **Configure vJoy:**
    *   Run "Configure vJoy" from your Start Menu.
    *   Ensure **Device 1** is enabled.
    *   Check the **"X" axis** under "Axes". You can leave other axes/buttons unchecked.
    *   Click "Apply".
    *   *`![vJoy Config](./images/vjoy.png)`)*

2.  **Camera Setup:**
    *   Position your webcam so it has a clear, stable view of your shoulders while you are on the bike in your normal riding position.
    *   Ensure good, consistent lighting. Avoid strong backlighting.

3.  **Configure XOutput:**
    *   Run `XOutput.exe`. You may need to grant firewall access.
    *   Click **"Add controller"**.
    *   Click **"Edit"** on the new controller entry.
    *   In the "Input device" dropdown, select **"vJoy Device"**.
    *   Under **"Left Stick" -> "X Axis"**:
        *   Click the configuration button (often looks like `...` or a dropdown).
        *   Select **"Axis X"** (or the corresponding axis number from vJoy, usually the first one listed).
        *   **(Verification):** Run the `tilt_steering.py` script (see Usage below) and tilt your body. You should see the input bar for this axis move in XOutput.
    *   Click **"Save configuration"**.
    *   Go back to the main XOutput window.
    *  * `![XOutput Mapping](./images/xoutput.png)`)*

4.  **Configure Steam:**
    *   **Disable Steam Input:** In your Steam Library, right-click Your Game -> Properties -> Controller -> Set "Override for ..." to **"Disable Steam Input"**. This prevents conflicts.
    *   **In-Game:** Launch Game. Go to Settings -> Controller. Ensure the input method is set to "Gamepad" or "Controller". The game should now recognize the virtual "Xbox 360 Controller" created by XOutput.

## Usage

1.  **Connect Webcam:** Ensure your webcam is connected and positioned correctly.
2.  **Run Python Script:**
    *   Open a terminal/command prompt.
    *   Navigate to the project directory (`cd Bodysteer`).
    *   Activate the virtual environment (e.g., `venv\Scripts\activate`).
    *   Run the script: `python main_gui.py`
    *   A window should pop up showing your webcam feed (potentially with pose landmarks). Keep this window open.
3.  **Run XOutput:**
    *   Start `XOutput.exe`.
    *   Click **"Start"** next to your configured vJoy controller. You should hear the Windows device connect sound. Keep XOutput running.
4.  **Launch Game:** Start the game (e.g., via Steam).
5.  **Ride!** Your body tilts should now control steering in the game.
6.  **Stopping:**
    *   Close Game.
    *   Click **"Stop"** in XOutput and close it.
    *   Go to the Python script's webcam window and press **'Q'** to quit the script.
    *   Deactivate the virtual environment (`deactivate`).

## Troubleshooting

*   **Game Doesn't Detect Controller:**
    *   Ensure XOutput is **Started** *before* launching the game.
    *   Verify **ViGEmBus driver** is installed correctly.
    *   Confirm **Steam Input is Disabled** for GTA V.
    *   Check `joy.cpl` (Windows USB Game Controllers): You should see both "vJoy Device" and "Xbox 360 Controller". Test the Xbox controller properties page - does the X axis move when you tilt (with the script and XOutput running)?
    *   Disconnect all other physical gamepads.
*   **Steering is Jittery/Unstable:**
    *   Improve lighting conditions.
    *   Increase the `deadzone` value in `main_gui.py`.
*   **Steering is Too Sensitive / Not Sensitive Enough:**
    *   Adjust the `max_tilt_angle` value in `main_gui.py`.
*   **XOutput Error / ViGEmBus Not Found:**
    *   Reinstall the ViGEmBus driver. Ensure you installed the correct version.
*   **Python Script Error:**
    *   Make sure all dependencies in `requirements.txt` are installed in your active environment (`python -m pip install -r requirements.txt`).
    *   Check webcam connection and permissions.

## Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request for improvements, bug fixes, or new features.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

*   [Google MediaPipe](https://developers.google.com/mediapipe) for the pose estimation library.
*   [vJoy](http://vjoystick.sourceforge.net/) for the virtual joystick driver.
*   [XOutput](https://github.com/csutorasa/XOutput) and [ViGEmBus](https://github.com/ViGEm/ViGEmBus) for the XInput emulation.
