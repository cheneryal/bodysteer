# Bodysteer - Steer A Game Using Your Webcam and Tilting Your Body
![Bodysteer GUI Screenshot](https://github.com/cheneryal/bodysteer/raw/main/icon.ico)
![Bodysteer GUI Screenshot](https://github.com/cheneryal/bodysteer/raw/main/images/ui.png)

This project allows you to steer your character by tilting your body, using input from a standard webcam. It detects body landmarks (shoulders) via MediaPipe, calculates the tilt angle, and translates it into virtual gamepad input using vJoy and XOutput.

This provides a hands-free steering solution, ideal for use with spin bikes and other fitness equipment connected via ANT+/Bluetooth sensors for speed/cadence.

## Features

*   Hands-free steering using body tilt.
*   Uses standard webcam, no special hardware required.
*   Real-time pose estimation via Google MediaPipe.
*   Outputs to a virtual DirectInput device (vJoy).
*   Uses XOutput to translate DirectInput to XInput for game compatibility.
*   Configurable sensitivity, deadzone, and calibration via the GUI.

## Installation Options

You have three main ways to install and use Bodysteer:

1.  **Easy Installation (Recommended for Most Users):** Download a pre-built executable. This is the simplest way to get started.
2.  **Manual Installation (For Developers or Customization):** Clone the repository and set up a Python environment. This is for users who want to modify the code or contribute.
3.  **Easy Installation without joystick drivers (GTA V only):** Download a pre-built executable and a Script Hook V .NET script.

---

### Option 1: Easy Installation (Recommended)

**Prerequisites:**

Before you begin, ensure you have the following software:

*   **vJoy Driver:** Creates the virtual DirectInput joystick.
    *   [Download vJoy](http://vjoystick.sourceforge.net/site/index.php/download-a-install/download) (Install this driver).
*   **ViGEmBus Driver:** Required by XOutput to create virtual Xbox controllers.
    *   [Download ViGEmBus](https://github.com/ViGEm/ViGEmBus/releases/latest) (Download and run the `ViGEmBus_Setup_x64.msi` or similar installer).
*   **XOutput:** Translates vJoy's DirectInput to XInput.
    *   [Download XOutput](https://github.com/csutorasa/XOutput/releases/latest) (Download `XOutput.zip`, extract `XOutput.exe` somewhere convenient).

**Hardware:**

*   A PC capable of running your game.
*   A standard webcam positioned to see your upper body/shoulders clearly.
*   (Optional) Your bike setup with Bluetooth/ANT+ sensors.

**Installation Steps:**

1.  **Download Bodysteer Executable:**
    *   Go to the [Bodysteer GitHub Releases page](https://github.com/cheneryal/bodysteer/releases).
    *   Download the latest `bodysteer` file.
    *   Place the downloaded `bodysteer.exe` file somewhere convenient on your computer.

2.  **Install Drivers:**
    *   Install the **vJoy driver** (downloaded from prerequisites).
    *   Install the **ViGEmBus driver** (downloaded from prerequisites).

3.  **Place XOutput:**
    *   Ensure you have downloaded and extracted `XOutput.exe` (from prerequisites) to a known location.

4.  **Proceed to the [Configuration](#configuration) section below.**

---

### Option 2: Manual Installation (For Developers or Customization)

**Prerequisites:**

Before you begin, ensure you have the following hardware and software:

**Hardware:**

*   A PC capable of running the game and Python script simultaneously.
*   A standard webcam positioned to see your upper body/shoulders clearly.
*   (Optional) Your bike setup with Bluetooth/ANT+ sensors.

**Software:**

*   **Python:** Version 3.9+ recommended (3.12 was used for recent builds). [Download Python](https://www.python.org/downloads/) (Make sure to check "Add Python to PATH" during installation).
*   **vJoy Driver:** Creates the virtual DirectInput joystick. [Download vJoy](http://vjoystick.sourceforge.net/site/index.php/download-a-install/download) (Install this driver).
*   **ViGEmBus Driver:** Required by XOutput to create virtual Xbox controllers. [Download ViGEmBus](https://github.com/ViGEm/ViGEmBus/releases/latest) (Install this driver before using XOutput).
*   **XOutput:** Translates vJoy's DirectInput to XInput. [Download XOutput](https://github.com/csutorasa/XOutput/releases/latest) (Download the application).
*   **Git:** (Optional, for cloning the repository). [Download Git](https://git-scm.com/downloads/).

**Installation Steps:**

1.  **Clone Repository:**
    *   Open a terminal or command prompt.
    *   `git clone https://github.com/cheneryal/bodysteer.git`
    *   `cd bodysteer`
    *   (Alternatively, download the ZIP file from GitHub and extract it.)

2.  **Install Drivers:**
    *   Install the **vJoy driver**.
    *   Install the **ViGEmBus driver**.

3.  **Set up Python Environment (Recommended):**
    *   `python -m venv venv`
    *   Activate the environment:
        *   Windows: `venv\Scripts\activate`
        *   macOS/Linux: `source venv/bin/activate`

4.  **Install Python Dependencies:**
    *   Install the required Python libraries:
        `python -m pip install -r requirements.txt`

5.  **Place XOutput:**
    *   Place the downloaded `XOutput.exe` file somewhere convenient (it doesn't need to be in the project folder, but you need to know where it is).

6.  **Proceed to the [Configuration](#configuration) section below.**

---

### Option 3: Easy Installation without joystick drivers

**Hardware:**

*   A PC capable of running GTA V (and optionally [GTBikeV](https://www.gtbikev.com/)).
*   A standard webcam positioned to see your upper body/shoulders clearly.
*   (Optional) Your bike setup with Bluetooth/ANT+ sensors.

**Installation Steps:**

*   Go to the [Bodysteer GitHub Releases page](https://github.com/cheneryal/bodysteer/releases).
*   Download the latest `bodysteer` file.
*   Place the downloaded `bodysteer.exe` file somewhere convenient on your computer.
*   Download the script [Steer.3.cs](Steer.3.cs) and place it in the `Grand Theft Auto V\Scripts` folder.
*   The script requires [Script Hook V](http://www.dev-c.com/gtav/scripthookv/) and [Script Hook V .NET](https://github.com/scripthookvdotnet/scripthookvdotnet) which should be already installed if you use GTBikeV.
*   Proceed to step 2 of [Configuration](#configuration) section below (the other steps are not necessary).

---

## Configuration

*(These steps are common for both Easy and Manual installations)*

1.  **Configure vJoy:**
    *   Run "Configure vJoy" from your Start Menu.
    *   Ensure **Device 1** is enabled.
    *   Check the **"X" axis** under "Axes". You can leave other axes/buttons unchecked.
    *   Click "Apply".

![Bodysteer vJoy Configuration](https://github.com/cheneryal/bodysteer/raw/main/images/vjoy.png)

2.  **Run Bodysteer Application:**
    *   Position your webcam so it has a clear, stable view of your shoulders while you are on the bike in your normal riding position.
    *   Ensure good, consistent lighting. Avoid strong backlighting.
    *   **For Easy Installation:** Double-click the `bodysteer.exe` file you downloaded.
    *   **For Manual Installation:**
        *   Ensure your Python virtual environment is activated (e.g., `venv\Scripts\activate`).
        *   Navigate to the `bodysteer` project directory in your terminal.
        *   Run `python main_gui.pyw` or simply double-click the `main_gui.pyw` file.
    *   The Bodysteer GUI window will appear.
        *   From the dropdown menu, select your camera device.
        *   Click **Start Camera**.
        *   Click **'Start Calibration'**:
            *   On your bike, look straight at the camera (neutral position) and press **'Calibrate: Look Straight'**.
            *   Tilt your body all the way to the left and click **'Calibrate: Tilt LEFT'**.
            *   Finally, tilt your body all the way to the right and click **'Calibrate: Tilt RIGHT'**.
        *   Set the **Deadzone** and **Sensitivity** using the sliders.
        *   Click **'Save Config'** to save these settings for future sessions.

3.  **Configure XOutput:**
    *   Run `XOutput.exe`. You may need to grant firewall access.
    *   Click "**Add controller**".
    *   Click "**Edit**" on the new controller entry.
    *   In the "**Input device**" dropdown, select "**vJoy Device**".
    *   Under "**Left Stick**" -> "**X Axis**":
        *   Click the configuration button (often looks like `...` or a dropdown).
        *   Select "**Axis X**" (or the corresponding axis number from vJoy, usually the first one listed).
    *   **(Verification - Optional):** While Bodysteer is running and calibrated, tilt your body. You should see the input bar for this axis move in XOutput.
    *   Click "**Save configuration**".
    *   Go back to the main XOutput window.

![Bodysteer xoutput Configuration](https://github.com/cheneryal/bodysteer/raw/main/images/xoutput.png)

4.  **Configure Steam (or Game Launcher):**
    *   **Disable Steam Input (Recommended for many games):** In your Steam Library, right-click your game -> Properties -> Controller -> Set "Override for ..." to "**Disable Steam Input**". This prevents conflicts.
    *   **In-Game:** Launch your game. Go to Settings -> Controller. Ensure the input method is set to "Gamepad" or "Controller". The game should now recognize the virtual "Xbox 360 Controller" created by XOutput.

## Usage

1.  **Connect Webcam:** Ensure your webcam is connected and positioned correctly.
2.  **Run Bodysteer Application:**
    *   **Easy Installation:** Double-click `bodysteer.exe`. Select camera, click Start Camera. Load config if saved, or calibrate.
    *   **Manual Installation:** Activate virtual environment, run `python main_gui.pyw` (or double-click `main_gui.pyw`). Select camera, click Start Camera. Load config if saved, or calibrate.
    *   Keep the Bodysteer window open.
3.  **Run XOutput:**
    *   Start `XOutput.exe`.
    *   Click "**Start**" next to your configured vJoy controller. You should hear the Windows device connect sound. Keep XOutput running.
4.  **Launch Game:** Start your game (e.g., via Steam).
5.  **Ride!** Your body tilts should now control steering in the game.

**Stopping:**

1.  Close the Game.
2.  In XOutput, click "**Stop**" next to the controller and then close XOutput.
3.  Close the Bodysteer application window.
4.  (For Manual Installation) If you used a terminal, you can deactivate the virtual environment (`deactivate`).

## Troubleshooting

*   **Game Doesn't Detect Controller:**
    *   Ensure XOutput is **Started** (controller shows green) *before* launching the game.
    *   Verify ViGEmBus driver is installed correctly.
    *   Confirm Steam Input is Disabled for the game if applicable.
    *   Check `joy.cpl` (Windows "Set up USB game controllers"): You should see both "vJoy Device" and "Xbox 360 Controller for Windows". Test the Xbox controller properties page - does the X axis move when you tilt (with Bodysteer and XOutput running)?
    *   Disconnect all other physical gamepads.
*   **Steering is Jittery/Unstable:**
    *   Improve lighting conditions (ensure good, even lighting, avoid backlighting).
    *   Ensure a stable background behind you.
    *   Increase the **Deadzone** value in the Bodysteer GUI.
    *   Recalibrate in Bodysteer GUI.
*   **Steering is Too Sensitive / Not Sensitive Enough:**
    *   Adjust the **Sensitivity** value in the Bodysteer GUI.
    *   Recalibrate in Bodysteer GUI, ensuring you capture your full tilt range.
*   **XOutput Error / ViGEmBus Not Found:**
    *   Reinstall the ViGEmBus driver. Ensure you installed the correct version and restarted if prompted.
*   **Bodysteer Application Error / Doesn't Start (Easy Install):**
    *   Ensure vJoy and ViGEmBus drivers are installed.
    *   Try running `bodysteer.exe` as an administrator (right-click -> Run as administrator).
    *   Check if your antivirus is blocking the application.
*   **Python Script Error (Manual Install):**
    *   Make sure all dependencies in `requirements.txt` are installed in your active virtual environment (`python -m pip install -r requirements.txt`).
    *   Check webcam connection and permissions. Ensure the correct camera is selected in the GUI.
*   **No Camera Feed / "Error opening video source":**
    *   Ensure the correct camera is selected from the dropdown in the Bodysteer GUI.
    *   Verify the webcam is not being used by another application.
    *   Check webcam drivers and connection.
*   **Bodysteer takes too long to detect camera:**
    *   Access **Control Panel > System > Advanced system settings > Advanced > Environment variables**.
    *   Add a new environment variable `OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS` with value `0`.

## Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request for improvements, bug fixes, or new features.

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.

## Acknowledgements

*   Google [MediaPipe](https://mediapipe.dev/) for the pose estimation library.
*   [vJoy](http://vjoystick.sourceforge.net/) for the virtual joystick driver.
*   [XOutput](https://github.com/csutorasa/XOutput) and [ViGEmBus](https://github.com/ViGEm/ViGEmBus) for the XInput emulation.
