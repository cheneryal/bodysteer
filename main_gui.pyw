import os
os.environ["OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS"] = "0"
import cv2
import mediapipe as mp
import numpy as np
import pyvjoy
import time
import math
import tkinter as tk
from tkinter import ttk # Ensure ttk is imported
from tkinter import messagebox
from PIL import Image, ImageTk
import threading
import queue
import json
import sys
import struct

# --- Constants ---
VJOY_MAX_AXIS = 32767
VJOY_CENTER_AXIS = VJOY_MAX_AXIS // 2
DEFAULT_DEADZONE = 0.05
CONFIG_FILE = "tilt_config.json"
MAX_CAMERAS_TO_CHECK = 10 # Check camera indices 0 through 9

if getattr(sys, 'frozen', False):
    # If we're running as a pyinstaller bundle
    SCRIPT_DIR = sys._MEIPASS
else:
    SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))

class TiltApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Body Tilt Steering")

        # --- State Variables ---
        self.processing_active = False
        self.calibrating = False
        self.calibration_step = 0 # 0: Not started, 1: Center, 2: Left, 3: Right, 4: Done
        self.min_angle_seen = 0.0
        self.max_angle_seen = 0.0
        self.calibrated_center_angle = 0.0
        self.calibrated_tilt_range = 0.0
        self.current_tilt_metric = None
        self.tilt_value = 0.0
        self.deadzone = tk.DoubleVar(value=DEFAULT_DEADZONE)
        self.sensitivity = tk.DoubleVar(value=1.0) # Default sensitivity
        self.camera_index = tk.IntVar(value=0) # Default camera index

        # --- Camera Discovery ---
        self.available_cameras = self.find_available_cameras()
        if not self.available_cameras:
             messagebox.showwarning("Camera Error", "No cameras found. Please ensure a camera is connected.")
             # Optionally disable start button or exit
             # For now, we'll let it proceed but it will fail in the thread

        # --- Threading & Queues ---
        self.video_queue = queue.Queue(maxsize=1)
        self.command_queue = queue.Queue() # For sending commands to thread
        self.status_queue = queue.Queue() # For receiving status from thread
        self.processing_thread = None
        self.stop_event = threading.Event()

        # --- vJoy ---
        try:
            self.j = pyvjoy.VJoyDevice(1)
            self.vjoy_available = True
        except Exception as e:
            messagebox.showerror("vJoy Error", f"Could not initialize vJoy Device 1: {e}\nRunning without vJoy output.")
            self.j = None
            self.vjoy_available = False

        # --- GUI Setup ---
        self.setup_gui()
        self.load_config() # Load config after GUI elements are created

        # --- Protocol Handler ---
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # --- Icon Setup ---
        try:
            # Best for Windows .ico files
            self.root.iconbitmap(os.path.join(SCRIPT_DIR, 'icon.ico'))
        except tk.TclError:
            print("Icon file not found or invalid format. Using default icon.")
            # Optional: Try with PhotoImage for .png/.gif if .ico fails or isn't available
            # try:
            #     icon_image = tk.PhotoImage(file='path/to/your/icon.png')
            #     self.root.iconphoto(True, icon_image)
            # except Exception as e:
            #     print(f"Could not load fallback icon: {e}")

    def find_available_cameras(self):
        """Checks for available camera devices."""
        available = []
        print("Searching for available cameras...")
        for i in range(MAX_CAMERAS_TO_CHECK):
            cap = cv2.VideoCapture(i)
            if cap is not None and cap.isOpened():
                print(f"  Found camera at index {i}")
                available.append(i)
                cap.release()
            else:
                # Optimization: Stop searching if we encounter a non-existent index
                # This assumes indices are mostly sequential. Remove if needed.
                # print(f"  No camera found at index {i}, stopping search.")
                # break
                pass # Continue checking up to MAX_CAMERAS_TO_CHECK
        print(f"Available cameras: {available}")
        return available

    def setup_gui(self):
        # --- Main Frames ---
        # Main control panel on the left
        left_panel = ttk.Frame(self.root, padding="10")
        left_panel.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        # Video panel on the right
        video_frame = ttk.Frame(self.root, padding="10")
        video_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure resizing behavior
        self.root.columnconfigure(0, weight=0) # Control panel fixed width
        self.root.columnconfigure(1, weight=1) # Video panel expands
        self.root.rowconfigure(0, weight=1)

        # --- Left Panel Content ---
        left_panel.rowconfigure(4, weight=1) # Add some space before config buttons

        # --- Camera Group ---
        camera_group = ttk.Labelframe(left_panel, text="Camera", padding="10")
        camera_group.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)
        camera_group.columnconfigure(1, weight=1)

        ttk.Label(camera_group, text="Device:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.camera_combobox = ttk.Combobox(camera_group, textvariable=self.camera_index, state="readonly")
        if self.available_cameras:
            self.camera_combobox['values'] = self.available_cameras
            # Try setting initial value, default to first available if saved index is invalid
            initial_cam_index = self.camera_index.get()
            if initial_cam_index not in self.available_cameras:
                self.camera_index.set(self.available_cameras[0])
        else:
             self.camera_combobox['values'] = ["N/A"]
             self.camera_index.set(-1) # Indicate no camera selected/available
             self.camera_combobox.config(state=tk.DISABLED)

        self.camera_combobox.grid(row=0, column=1, sticky=tk.EW)


        # --- Control Group ---
        control_group = ttk.Labelframe(left_panel, text="Control", padding="10")
        control_group.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=5, pady=5) # Shifted down
        control_group.columnconfigure(0, weight=1)

        self.start_stop_button = ttk.Button(control_group, text="Start", command=self.toggle_processing)
        self.start_stop_button.grid(row=0, column=0, pady=5, sticky=tk.EW)
        # Disable start if no cameras found
        if not self.available_cameras:
            self.start_stop_button.config(state=tk.DISABLED)


        self.calibrate_button = ttk.Button(control_group, text="Start Calibration", command=self.handle_calibration_press, state=tk.DISABLED)
        self.calibrate_button.grid(row=1, column=0, pady=5, sticky=tk.EW)

        # --- Status Group ---
        status_group = ttk.Labelframe(left_panel, text="Status", padding="10")
        status_group.grid(row=2, column=0, sticky=(tk.W, tk.E), padx=5, pady=5) # Shifted down
        status_group.columnconfigure(0, weight=1)

        self.status_label = ttk.Label(status_group, text="Status: Idle")
        self.status_label.grid(row=0, column=0, columnspan=2, pady=2, sticky=tk.W)

        self.metric_label = ttk.Label(status_group, text="Tilt Metric: N/A")
        self.metric_label.grid(row=1, column=0, columnspan=2, pady=2, sticky=tk.W)

        self.output_label = ttk.Label(status_group, text="Output Tilt: N/A")
        self.output_label.grid(row=2, column=0, columnspan=2, pady=2, sticky=tk.W)

        # --- Tuning Group ---
        tuning_group = ttk.Labelframe(left_panel, text="Tuning", padding="10")
        tuning_group.grid(row=3, column=0, sticky=(tk.W, tk.E), padx=5, pady=5) # Shifted down
        tuning_group.columnconfigure(1, weight=1) # Allow sliders to expand

        # Deadzone Slider
        ttk.Label(tuning_group, text="Deadzone:").grid(row=0, column=0, sticky=tk.W, padx=2)
        self.deadzone_value_label = ttk.Label(tuning_group, text=f"{self.deadzone.get():.2f}", width=4, anchor=tk.E)
        self.deadzone_value_label.grid(row=0, column=2, sticky=tk.E, padx=2)
        self.deadzone_slider = ttk.Scale(tuning_group, from_=0.0, to=0.5, orient=tk.HORIZONTAL, variable=self.deadzone, command=self.update_deadzone_value)
        self.deadzone_slider.grid(row=1, column=0, columnspan=3, sticky=tk.EW, pady=(0, 5))

        # Sensitivity Slider
        ttk.Label(tuning_group, text="Sensitivity:").grid(row=2, column=0, sticky=tk.W, padx=2)
        self.sensitivity_value_label = ttk.Label(tuning_group, text=f"{self.sensitivity.get():.2f}", width=4, anchor=tk.E)
        self.sensitivity_value_label.grid(row=2, column=2, sticky=tk.E, padx=2)
        self.sensitivity_slider = ttk.Scale(tuning_group, from_=0.5, to=3.0, orient=tk.HORIZONTAL, variable=self.sensitivity, command=self.update_sensitivity_value)
        self.sensitivity_slider.grid(row=3, column=0, columnspan=3, sticky=tk.EW, pady=(0, 5))

        # --- Configuration Group ---
        config_group = ttk.Labelframe(left_panel, text="Configuration", padding="10")
        config_group.grid(row=5, column=0, sticky=(tk.W, tk.E, tk.S), padx=5, pady=5) # Shifted down, Place at bottom
        config_group.columnconfigure(0, weight=1)
        config_group.columnconfigure(1, weight=1)

        save_button = ttk.Button(config_group, text="Save Config", command=self.save_config)
        save_button.grid(row=0, column=0, padx=5, pady=5, sticky=tk.EW)
        load_button = ttk.Button(config_group, text="Load Config", command=self.load_config)
        load_button.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)


        # --- Video Frame Widgets ---
        self.video_label = ttk.Label(video_frame)
        self.video_label.pack(expand=True, fill=tk.BOTH)

    def update_deadzone_value(self, value):
        self.deadzone_value_label.config(text=f"{float(value):.2f}")
        if self.processing_active:
             # Send updated deadzone to processing thread if needed
             self.command_queue.put({'action': 'set_deadzone', 'value': self.deadzone.get()})

    # Add this new method
    def update_sensitivity_value(self, value):
        self.sensitivity_value_label.config(text=f"{float(value):.2f}")
        if self.processing_active:
             # Send updated sensitivity to processing thread
             self.command_queue.put({'action': 'set_sensitivity', 'value': self.sensitivity.get()})

    def toggle_processing(self):
        if not self.processing_active:
            self.start_processing()
        else:
            self.stop_processing()

    def start_processing(self):
        if self.processing_active:
            return
        if not self.available_cameras:
             messagebox.showerror("Error", "Cannot start processing: No cameras available.")
             return
        if self.camera_index.get() < 0:
             messagebox.showerror("Error", "Cannot start processing: No camera selected.")
             return


        # --- Clear stale commands before starting ---
        try:
            while not self.command_queue.empty():
                self.command_queue.get_nowait()
            print("Command queue cleared.")
        except queue.Empty:
            pass # Queue is already empty
        except Exception as e:
            print(f"Warning: Could not clear command queue: {e}")

        selected_camera = self.camera_index.get() # Get selected camera index

        self.stop_event.clear()
        # Pass selected camera index to the processing loop
        self.processing_thread = threading.Thread(target=self.processing_loop, args=(selected_camera,), daemon=True)
        self.processing_thread.start()
        self.processing_active = True
        self.start_stop_button.config(text="Stop")
        self.calibrate_button.config(state=tk.NORMAL)
        self.camera_combobox.config(state=tk.DISABLED) # Disable camera selection while running
        self.status_label.config(text="Status: Running")
        self.update_gui() # Start the GUI update loop

    def stop_processing(self):
        if not self.processing_active:
            return

        self.stop_event.set() # Signal thread to stop
        self.command_queue.put({'action': 'stop'}) # Send stop command

        if self.processing_thread and self.processing_thread.is_alive():
             self.processing_thread.join(timeout=1.0) # Wait briefly for thread

        self.processing_active = False
        self.start_stop_button.config(text="Start")
        self.calibrate_button.config(state=tk.DISABLED)
        if self.available_cameras: # Only enable if cameras exist
            self.camera_combobox.config(state="readonly") # Re-enable camera selection
        self.status_label.config(text="Status: Idle")
        self.metric_label.config(text="Tilt Metric: N/A")
        self.output_label.config(text="Output Tilt: N/A")
        self.video_label.config(image='') # Clear video label

        # Reset vJoy axis on stop
        if self.j and self.vjoy_available:
            try:
                self.j.set_axis(pyvjoy.HID_USAGE_X, VJOY_CENTER_AXIS)
            except Exception as e:
                print(f"Warning: Could not reset vJoy axis on stop: {e}")

        # Reset calibration state visually
        self.calibration_step = 0
        self.update_calibration_button_text()

    def handle_calibration_press(self):
        if not self.processing_active:
            return
        # Send command to processing thread to advance calibration
        self.command_queue.put({'action': 'calibrate_step'})

    def update_calibration_button_text(self):
        if self.calibration_step == 0:
            self.calibrate_button.config(text="Start Calibration")
        elif self.calibration_step == 1:
            self.calibrate_button.config(text="Calibrate: Look STRAIGHT")
        elif self.calibration_step == 2:
            self.calibrate_button.config(text="Calibrate: Tilt LEFT")
        elif self.calibration_step == 3:
            self.calibrate_button.config(text="Calibrate: Tilt RIGHT")
        elif self.calibration_step == 4:
            self.calibrate_button.config(text="Recalibrate")

    def update_gui(self):
        """ Checks queues and updates GUI elements. Schedules itself to run again. """
        try:
            # Update Video Feed
            while not self.video_queue.empty():
                frame_rgb = self.video_queue.get_nowait()
                img = Image.fromarray(frame_rgb)
                imgtk = ImageTk.PhotoImage(image=img)
                self.video_label.imgtk = imgtk # Keep reference
                self.video_label.config(image=imgtk)

            # Update Status/Data Labels
            while not self.status_queue.empty():
                status_data = self.status_queue.get_nowait()
                if 'status_text' in status_data:
                    self.status_label.config(text=f"Status: {status_data['status_text']}")
                if 'metric' in status_data:
                    metric_val = status_data['metric']
                    self.metric_label.config(text=f"Tilt Metric: {metric_val:.2f}" if metric_val is not None else "Tilt Metric: N/A")
                if 'output' in status_data:
                    self.output_label.config(text=f"Output Tilt: {status_data['output']:.2f}")
                if 'calibration_step' in status_data:
                    self.calibration_step = status_data['calibration_step']
                    self.update_calibration_button_text()
                if 'calibrated_range' in status_data: # Display final range
                    c_min, c_max, c_center = status_data['calibrated_range']
                    self.status_label.config(text=f"Status: Calibrated! R:[{c_min:.2f},{c_max:.2f}] C:{c_center:.2f}")


        except queue.Empty:
            pass # No updates available
        except Exception as e:
            print(f"Error updating GUI: {e}")

        # Schedule next update if processing
        if self.processing_active:
            self.root.after(30, self.update_gui) # Approx 33 FPS update rate

    def save_config(self):
        config_data = {
            'camera_index': self.camera_index.get(), # Save selected camera index
            'deadzone': self.deadzone.get(),
            'sensitivity': self.sensitivity.get(), # Add sensitivity
            'calibrated_center_angle': self.calibrated_center_angle,
            'min_angle_seen': self.min_angle_seen,
            'max_angle_seen': self.max_angle_seen,
            'calibrated_tilt_range': self.calibrated_tilt_range,
            'calibration_step': self.calibration_step if self.calibration_step == 4 else 0 # Only save if fully calibrated
        }
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config_data, f, indent=4)
            print(f"Configuration saved to {CONFIG_FILE}")
            status_msg = "Config Saved"
            if self.processing_active:
                 self.status_label.config(text=f"Status: {status_msg}")
            else:
                 self.status_label.config(text=f"Status: Idle - {status_msg}")

        except Exception as e:
            messagebox.showerror("Save Error", f"Could not save configuration: {e}")

    def load_config(self):
        if not os.path.exists(CONFIG_FILE):
            print(f"Configuration file {CONFIG_FILE} not found. Using defaults.")
            # Apply defaults explicitly if needed
            self.deadzone.set(DEFAULT_DEADZONE)
            self.update_deadzone_value(self.deadzone.get()) # Update label
            self.sensitivity.set(1.0)
            self.update_sensitivity_value(self.sensitivity.get())
            # Set camera to first available if possible
            if self.available_cameras:
                self.camera_index.set(self.available_cameras[0])
            else:
                self.camera_index.set(-1)
            self.calibration_step = 0
            # Reset other calibration vars if needed
            return

        try:
            with open(CONFIG_FILE, 'r') as f:
                config_data = json.load(f)

            # Load Camera Index
            loaded_cam_index = config_data.get('camera_index', 0)
            # Validate loaded index against available cameras
            if self.available_cameras:
                if loaded_cam_index in self.available_cameras:
                    self.camera_index.set(loaded_cam_index)
                else:
                    print(f"Warning: Saved camera index {loaded_cam_index} not found. Defaulting to {self.available_cameras[0]}.")
                    self.camera_index.set(self.available_cameras[0]) # Default to first available
            else:
                 # No cameras available, set index to invalid state
                 self.camera_index.set(-1)


            self.deadzone.set(config_data.get('deadzone', DEFAULT_DEADZONE))
            self.update_deadzone_value(self.deadzone.get()) # Update label

            self.sensitivity.set(config_data.get('sensitivity', 1.0)) # Load sensitivity
            self.update_sensitivity_value(self.sensitivity.get()) # Update label

            # Load calibration data only if it was saved as completed (step 4)
            if config_data.get('calibration_step') == 4:
                self.calibrated_center_angle = config_data.get('calibrated_center_angle', 0.0)
                self.min_angle_seen = config_data.get('min_angle_seen', 0.0)
                self.max_angle_seen = config_data.get('max_angle_seen', 0.0)
                self.calibrated_tilt_range = config_data.get('calibrated_tilt_range', 0.0)
                # Basic validation on loaded range/center
                if abs(self.calibrated_tilt_range) < 1e-6 and abs(self.max_angle_seen - self.min_angle_seen) > 1e-6:
                    self.calibrated_tilt_range = self.max_angle_seen - self.min_angle_seen
                if abs(self.calibrated_center_angle - (self.min_angle_seen + self.max_angle_seen) / 2.0) > 1e-6:
                    self.calibrated_center_angle = (self.min_angle_seen + self.max_angle_seen) / 2.0

                self.calibration_step = 4
                print("Loaded calibrated values.")
                # Update status display if needed (will be overwritten if processing starts)
                self.status_label.config(text=f"Status: Loaded Calib. R:[{self.min_angle_seen:.2f},{self.max_angle_seen:.2f}]")

            else:
                 self.calibration_step = 0
                 # Reset calibration vars to default if loaded config wasn't calibrated
                 self.calibrated_center_angle = 0.0
                 self.min_angle_seen = 0.0
                 self.max_angle_seen = 0.0
                 self.calibrated_tilt_range = 0.0
                 print("Loaded config, but not calibrated. Ready to calibrate.")
                 self.status_label.config(text="Status: Idle - Config Loaded")


            self.update_calibration_button_text()
            print(f"Configuration loaded from {CONFIG_FILE}")

            # If processing is active, send loaded values to thread
            if self.processing_active:
                # Send the whole config dict, thread will pick what it needs
                # Note: Camera index cannot be changed while running with this setup
                self.command_queue.put({'action': 'load_config', 'data': config_data})

        except Exception as e:
            messagebox.showerror("Load Error", f"Could not load configuration: {e}")
            # Reset to defaults on error?
            if self.available_cameras:
                self.camera_index.set(self.available_cameras[0])
            else:
                self.camera_index.set(-1)
            self.deadzone.set(DEFAULT_DEADZONE)
            self.update_deadzone_value(self.deadzone.get())
            self.sensitivity.set(1.0) # Reset sensitivity
            self.update_sensitivity_value(self.sensitivity.get())
            self.calibration_step = 0
            self.update_calibration_button_text()

    def on_closing(self):
        """ Handles window closing """
        print("Closing application...")
        self.stop_processing() # Ensure thread is stopped and vJoy is reset
        # Add delay to ensure vJoy reset command is processed if needed
        time.sleep(0.1)
        self.root.destroy()


    # ==================================================================
    #                   Core Processing Logic (Thread)
    # ==================================================================
    # Modify the signature to accept the camera index
    def processing_loop(self, camera_index):
        """ The main loop executed in a separate thread """
        print(f"Processing thread started for camera index {camera_index}.")
        cap = None
        pose = None
        try: # Wrap the whole setup and loop
            # Use the passed camera_index
            cap = cv2.VideoCapture(camera_index)
            if not cap.isOpened():
                print(f"Error: Could not open camera at index {camera_index}.")
                # Use status queue to report error back to GUI thread
                try: self.status_queue.put({'status_text': f'Error: Cam {camera_index} failed'})
                except Exception as qe: print(f"Could not put webcam error status onto queue: {qe}")
                return # Exit thread if webcam fails

            mp_pose = mp.solutions.pose
            # Ensure pose is initialized within the try block
            pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
            mp_drawing = mp.solutions.drawing_utils

            # --- Local state for the thread ---
            thread_calibrating = False
            # Initialize thread state from main app state correctly
            thread_calibration_step = self.calibration_step
            thread_min_angle = self.min_angle_seen
            thread_max_angle = self.max_angle_seen
            thread_center_angle = self.calibrated_center_angle
            thread_tilt_range = self.calibrated_tilt_range
            thread_deadzone = self.deadzone.get()
            thread_sensitivity = self.sensitivity.get()

            # --- Load Config Handling Helper ---
            def apply_loaded_config(config_data):
                nonlocal thread_deadzone, thread_sensitivity, thread_calibration_step
                nonlocal thread_min_angle, thread_max_angle, thread_center_angle, thread_tilt_range
                nonlocal thread_calibrating

                # Note: Camera index is fixed when the thread starts and not updated here
                thread_deadzone = config_data.get('deadzone', DEFAULT_DEADZONE)
                thread_sensitivity = config_data.get('sensitivity', 1.0)

                loaded_step = config_data.get('calibration_step')
                if loaded_step == 4:
                    thread_center_angle = config_data.get('calibrated_center_angle', 0.0)
                    thread_min_angle = config_data.get('min_angle_seen', 0.0)
                    thread_max_angle = config_data.get('max_angle_seen', 0.0)
                    thread_tilt_range = config_data.get('calibrated_tilt_range', 0.0)
                    # Ensure range is not zero if loading potentially inconsistent data
                    if abs(thread_tilt_range) < 1e-6 and abs(thread_max_angle - thread_min_angle) > 1e-6:
                        thread_tilt_range = thread_max_angle - thread_min_angle
                    # Recalculate center based on min/max seen if inconsistent
                    if abs(thread_center_angle - (thread_min_angle + thread_max_angle) / 2.0) > 1e-6:
                         thread_center_angle = (thread_min_angle + thread_max_angle) / 2.0

                    thread_calibration_step = 4
                    thread_calibrating = False
                    print("Thread: Applied loaded calibrated values.")
                    try:
                        self.status_queue.put({
                            'status_text': f'Running - Loaded Calib.',
                            'calibration_step': 4,
                            'calibrated_range': (thread_min_angle, thread_max_angle, thread_center_angle)
                         })
                    except Exception as qe: print(f"Could not put loaded calib status onto queue: {qe}")
                else:
                    # Reset calibration if loaded config wasn't fully calibrated
                    thread_calibration_step = 0
                    thread_calibrating = False
                    thread_min_angle = 0.0
                    thread_max_angle = 0.0
                    thread_center_angle = 0.0
                    thread_tilt_range = 0.0
                    print("Thread: Applied loaded config (not calibrated).")
                    try:
                        self.status_queue.put({'status_text': 'Running - Ready to Calibrate', 'calibration_step': 0})
                    except Exception as qe: print(f"Could not put loaded non-calib status onto queue: {qe}")

            # Apply initial config state when thread starts
            initial_config = {
                # Camera index is handled by the thread argument
                'deadzone': thread_deadzone, # Use thread's initial values
                'sensitivity': thread_sensitivity,
                'calibrated_center_angle': thread_center_angle,
                'min_angle_seen': thread_min_angle,
                'max_angle_seen': thread_max_angle,
                'calibrated_tilt_range': thread_tilt_range,
                'calibration_step': thread_calibration_step
            }
            apply_loaded_config(initial_config)


            while not self.stop_event.is_set():
                # --- Check for commands from GUI ---
                try:
                    command = self.command_queue.get_nowait()
                    if command['action'] == 'stop':
                        print("Thread: Stop command received.")
                        break # Exit loop signal
                    elif command['action'] == 'calibrate_step':
                        # --- Handle Calibration Step Advancement ---
                        current_metric_for_calib = self.current_tilt_metric # Capture metric at time of command
                        if thread_calibration_step == 0: # Start calibration -> Capture Center
                            thread_calibrating = True
                            thread_calibration_step = 1
                            self.status_queue.put({'status_text': 'Calibrating: Look STRAIGHT', 'calibration_step': 1})
                        elif thread_calibration_step == 1: # Finish Center -> Capture Left
                            if current_metric_for_calib is not None:
                                thread_center_angle = current_metric_for_calib
                                thread_calibration_step = 2
                                self.status_queue.put({'status_text': f'Center: {thread_center_angle:.2f}. Tilt LEFT', 'calibration_step': 2})
                            else:
                                 self.status_queue.put({'status_text': 'Cannot Calibrate: Shoulders not detected'})
                        elif thread_calibration_step == 2: # Finish Left -> Capture Right
                             if current_metric_for_calib is not None:
                                thread_min_angle = current_metric_for_calib
                                thread_calibration_step = 3
                                self.status_queue.put({'status_text': f'Left: {thread_min_angle:.2f}. Tilt RIGHT', 'calibration_step': 3})
                             else:
                                 self.status_queue.put({'status_text': 'Cannot Calibrate: Shoulders not detected'})
                        elif thread_calibration_step == 3: # Finish Right -> Complete
                             if current_metric_for_calib is not None:
                                thread_max_angle = current_metric_for_calib
                                thread_calibrating = False
                                thread_calibration_step = 4
                                if thread_min_angle > thread_max_angle: # Ensure min < max
                                    thread_min_angle, thread_max_angle = thread_max_angle, thread_min_angle
                                thread_tilt_range = thread_max_angle - thread_min_angle
                                # Recalculate center based on actual min/max extremes
                                thread_center_angle = (thread_min_angle + thread_max_angle) / 2.0
                                # Update main app variables (important for saving config)
                                self.min_angle_seen = thread_min_angle
                                self.max_angle_seen = thread_max_angle
                                self.calibrated_center_angle = thread_center_angle
                                self.calibrated_tilt_range = thread_tilt_range
                                self.calibration_step = thread_calibration_step # Update main app step
                                self.status_queue.put({
                                    'status_text': f'Right: {thread_max_angle:.2f}. Calibrated!',
                                    'calibration_step': 4,
                                    'calibrated_range': (thread_min_angle, thread_max_angle, thread_center_angle)
                                })
                             else:
                                 self.status_queue.put({'status_text': 'Cannot Calibrate: Shoulders not detected'})
                        elif thread_calibration_step == 4: # Restart calibration
                             thread_calibration_step = 0
                             thread_calibrating = False
                             thread_tilt_range = 0.0
                             thread_min_angle = 0.0
                             thread_max_angle = 0.0
                             thread_center_angle = 0.0
                             # Reset main app vars
                             self.min_angle_seen = 0.0
                             self.max_angle_seen = 0.0
                             self.calibrated_center_angle = 0.0
                             self.calibrated_tilt_range = 0.0
                             self.calibration_step = thread_calibration_step # Update main app step
                             self.status_queue.put({'status_text': 'Ready to Calibrate', 'calibration_step': 0})

                    elif command['action'] == 'set_deadzone':
                        thread_deadzone = command['value']
                        print(f"Thread: Deadzone updated to {thread_deadzone:.2f}")
                    elif command['action'] == 'set_sensitivity':
                        thread_sensitivity = command['value']
                        print(f"Thread: Sensitivity updated to {thread_sensitivity:.2f}")
                    elif command['action'] == 'load_config':
                        print("Thread: Received load_config command.")
                        apply_loaded_config(command['data'])
                        # Ensure main app state also reflects loaded state (except camera)
                        self.deadzone.set(thread_deadzone)
                        self.sensitivity.set(thread_sensitivity)
                        self.calibration_step = thread_calibration_step
                        self.min_angle_seen = thread_min_angle
                        self.max_angle_seen = thread_max_angle
                        self.calibrated_center_angle = thread_center_angle
                        self.calibrated_tilt_range = thread_tilt_range


                except queue.Empty:
                    pass # No commands
                except Exception as cmd_e:
                     print(f"Error processing command queue: {cmd_e}")


                # --- Read Frame ---
                success, image = cap.read()
                if not success:
                    # print("Ignoring empty camera frame.") # Reduce console spam
                    time.sleep(0.05) # Wait a bit longer if frames fail
                    continue

                # --- Image Processing ---
                image = cv2.flip(image, 1)
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                image_rgb.flags.writeable = False
                results = pose.process(image_rgb)
                image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
                image_bgr.flags.writeable = True


                # --- Pose Logic ---
                self.current_tilt_metric = None # Reset each frame
                current_output_tilt = 0.0 # Use a local variable

                if results.pose_landmarks:
                    landmarks = results.pose_landmarks.landmark
                    # Use inner try/except for landmark access, let outer handle bigger issues
                    try:
                        left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
                        right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]

                        if left_shoulder.visibility > 0.5 and right_shoulder.visibility > 0.5:
                            dx = right_shoulder.x - left_shoulder.x
                            dy = right_shoulder.y - left_shoulder.y

                            if abs(dx) > 1e-6:
                                self.current_tilt_metric = dy / dx
                            else:
                                self.current_tilt_metric = 0.0

                            # --- Normalization, Deadzone, Sensitivity (Post-Calibration) ---
                            if thread_calibration_step == 4:
                                half_range = thread_tilt_range / 2.0
                                if half_range > 1e-6:
                                    deviation = self.current_tilt_metric - thread_center_angle
                                    normalized_tilt = np.clip(deviation / half_range, -1.0, 1.0)

                                    # Apply Deadzone
                                    if abs(normalized_tilt) < thread_deadzone:
                                        rescaled_tilt = 0.0
                                    else:
                                        # Rescale to use the full range outside the deadzone
                                        if normalized_tilt > 0:
                                            rescaled_tilt = (normalized_tilt - thread_deadzone) / (1.0 - thread_deadzone)
                                        else:
                                            rescaled_tilt = (normalized_tilt + thread_deadzone) / (1.0 - thread_deadzone)
                                        rescaled_tilt = np.clip(rescaled_tilt, -1.0, 1.0)

                                    # Apply Sensitivity
                                    current_output_tilt = rescaled_tilt * thread_sensitivity
                                    # Clip final output value after sensitivity
                                    current_output_tilt = np.clip(current_output_tilt, -1.0, 1.0)

                                else: # Cannot normalize if range is too small
                                    current_output_tilt = 0.0
                            else: # If not calibrated, output is 0
                                current_output_tilt = 0.0

                            # --- Draw Landmarks ---
                            mp_drawing.draw_landmarks(
                                image_bgr, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

                        else: # Shoulders not visible
                            self.current_tilt_metric = None
                            current_output_tilt = 0.0

                    except IndexError:
                        # print("Error accessing shoulder landmarks.") # Reduce spam
                        self.current_tilt_metric = None
                        current_output_tilt = 0.0
                    # Let outer try/except catch other pose processing errors

                else: # No pose landmarks detected
                    self.current_tilt_metric = None
                    current_output_tilt = 0.0

                # Update the class variable *after* calculations
                self.tilt_value = current_output_tilt

                # --- vJoy Output ---
                if self.j and self.vjoy_available:
                    try:
                        # Map the final tilt_value (-1 to 1, already includes sensitivity) to vJoy axis
                        vjoy_x_value = int(VJOY_CENTER_AXIS + (self.tilt_value * (VJOY_MAX_AXIS / 2)))
                        # Clip the FINAL vJoy value
                        vjoy_x_value = np.clip(vjoy_x_value, 0, VJOY_MAX_AXIS)
                        self.j.set_axis(pyvjoy.HID_USAGE_X, int(vjoy_x_value))
                    except Exception as e:
                        print(f"Warning: Could not set vJoy axis: {e}")
                        # Maybe disable vJoy if it keeps failing?
                        # self.vjoy_available = False
                else:
                    try:
                        with open(r"\\.\pipe\tilt", "wb") as pipe:
                            pipe.write(struct.pack("f", self.tilt_value))
                            pipe.flush()
                    except:
                        pass

                # --- Prepare data for GUI ---
                # Put frame onto queue
                try:
                    # Clear queue to show latest frame
                    while not self.video_queue.empty():
                        self.video_queue.get_nowait()
                    self.video_queue.put_nowait(cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB))
                except queue.Full:
                    pass # Should be rare after clearing
                except Exception as e:
                     print(f"Error putting frame onto queue: {e}")

                # Put status data onto queue
                try:
                    status_update = {
                        'metric': self.current_tilt_metric,
                        'output': self.tilt_value
                        # Status text is handled by calibration/command logic
                    }
                    # Limit queue size to prevent memory issues if GUI hangs
                    while self.status_queue.qsize() >= 10:
                        self.status_queue.get_nowait() # Discard oldest status
                    self.status_queue.put_nowait(status_update)
                except queue.Empty: # Can happen if qsize check and get race
                    pass
                except queue.Full: # Should not happen after clearing space
                    pass
                except Exception as e:
                    print(f"Error putting status onto queue: {e}")

                # Yield control briefly
                time.sleep(0.001) # Small sleep even if processing is fast

        except Exception as e:
            # --- Catch ALL exceptions in the thread's main execution ---
            import traceback
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print(f"FATAL ERROR in processing thread: {e}")
            print(traceback.format_exc())
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            # Send error message to GUI status
            try:
                # Ensure queue isn't full
                while self.status_queue.qsize() >= 10: self.status_queue.get_nowait()
                self.status_queue.put({'status_text': f'THREAD ERROR: Check Console'})
            except Exception as qe:
                 print(f"Could not put error status onto queue: {qe}")

        finally:
            # --- Cleanup Thread Resources ---
            print("Processing thread stopping / cleanup...")
            if self.j and self.vjoy_available:
                try:
                    self.j.set_axis(pyvjoy.HID_USAGE_X, VJOY_CENTER_AXIS)
                    print("vJoy axis centered.")
                except Exception as e:
                     print(f"Warning: Could not reset vJoy axis on thread stop: {e}")
            if cap is not None and cap.isOpened():
                cap.release()
                print(f"Camera {camera_index} released.") # Log which camera was released
            if pose is not None:
                pose.close()
                print("MediaPipe Pose closed.")

            # Signal GUI that processing has stopped
            # This needs to be done carefully to avoid race conditions if called from GUI thread too
            # Setting the flag here ensures GUI loop stops scheduling updates
            self.processing_active = False

            # Attempt to put one final status update from the thread
            try:
                 while self.status_queue.qsize() >= 10: self.status_queue.get_nowait()
                 # Use a distinct message for thread exit vs. GUI stop button
                 final_status = 'Stopped (Thread Exit)'
                 if self.stop_event.is_set(): # Check if stop was requested by GUI
                     final_status = 'Stopped'
                 self.status_queue.put({'status_text': final_status})
            except Exception as qe:
                 print(f"Could not put final status onto queue: {qe}")

            print("Processing thread finished.")

# --- Main Execution ---
if __name__ == "__main__":
    root = tk.Tk()
    # Optional: Apply a ttk theme for a more modern look
    style = ttk.Style(root)
    # print(style.theme_names()) # See available themes: ('winnative', 'clam', 'alt', 'default', 'classic', 'vista', 'xpnative') on Windows
    try:
        # Use a theme that generally looks better than default if available
        if 'vista' in style.theme_names():
            style.theme_use('vista')
        elif 'clam' in style.theme_names():
             style.theme_use('clam')
    except tk.TclError:
        print("Could not set ttk theme.") # Ignore if theme setting fails

    app = TiltApp(root)
    root.mainloop()
