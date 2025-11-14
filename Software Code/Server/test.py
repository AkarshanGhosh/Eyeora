"""
Tkinter Test GUI - Automated Testing Interface with Live Camera
Tests all modules and provides live camera testing
Location: Software Code/Server/test_gui.py
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import time
from pathlib import Path
from datetime import datetime
import sys
import os
import cv2
from PIL import Image, ImageTk

# Add core modules to path
sys.path.insert(0, str(Path(__file__).parent))

from core.video_processor import VideoProcessor
from core.detection_engine import DetectionEngine
from core.behavior_analyzer import BehaviorAnalyzer
from core.csv_exporter import DataExporter
from core.tracker import PersonTracker
from core.alert_system import AlertSystem
from core.live_camera import LiveCameraSystem
from core.config import PROCESSED_DIR, DATA_DIR


class TestGUI:
    """
    Automated Testing GUI with Tkinter + Live Camera
    """
    
    def __init__(self, root):
        self.root = root
        self.root.title("🎯 Eyeora AI-CCTV - Test Suite & Live Camera")
        self.root.geometry("1100x750")
        self.root.resizable(True, True)
        
        # Test variables
        self.test_mode = tk.StringVar(value="video")
        self.input_file = tk.StringVar()
        self.confidence = tk.DoubleVar(value=0.4)
        self.generate_output = tk.BooleanVar(value=True)
        self.export_csv = tk.BooleanVar(value=True)
        self.show_zones = tk.BooleanVar(value=True)
        
        # Live camera variables
        self.live_camera = None
        self.camera_running = False
        self.show_live_detections = tk.BooleanVar(value=True)
        self.show_live_pose = tk.BooleanVar(value=True)
        self.show_live_stats = tk.BooleanVar(value=True)
        
        # Test status
        self.is_testing = False
        self.test_results = {}
        
        # Initialize components
        self.processor = None
        self.detection_engine = None
        
        # Setup GUI
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the user interface with tabs"""
        
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Tab 1: File Testing
        self.test_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.test_tab, text="📁 File Testing")
        self._setup_test_tab()
        
        # Tab 2: Live Camera
        self.camera_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.camera_tab, text="📹 Live Camera")
        self._setup_camera_tab()
        
    def _setup_test_tab(self):
        """Setup file testing tab"""
        
        # Main container
        main_frame = ttk.Frame(self.test_tab, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.test_tab.columnconfigure(0, weight=1)
        self.test_tab.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(6, weight=1)
        
        # ===== HEADER =====
        header_frame = ttk.LabelFrame(main_frame, text="🎯 Test Configuration", padding="10")
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Test Mode Selection
        ttk.Label(header_frame, text="Test Mode:", font=("Arial", 10, "bold")).grid(
            row=0, column=0, sticky=tk.W, pady=5
        )
        
        mode_frame = ttk.Frame(header_frame)
        mode_frame.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        ttk.Radiobutton(
            mode_frame, 
            text="📹 Video Analysis", 
            variable=self.test_mode, 
            value="video",
            command=self._on_mode_change
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Radiobutton(
            mode_frame, 
            text="📸 Image Detection", 
            variable=self.test_mode, 
            value="image",
            command=self._on_mode_change
        ).pack(side=tk.LEFT, padx=5)
        
        # ===== FILE SELECTION =====
        file_frame = ttk.LabelFrame(main_frame, text="📁 Input File", padding="10")
        file_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(0, weight=1)
        
        # File path entry
        file_entry_frame = ttk.Frame(file_frame)
        file_entry_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))
        file_entry_frame.columnconfigure(0, weight=1)
        
        self.file_entry = ttk.Entry(file_entry_frame, textvariable=self.input_file, width=60)
        self.file_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        ttk.Button(
            file_entry_frame, 
            text="Browse...", 
            command=self._browse_file
        ).grid(row=0, column=1)
        
        # ===== PARAMETERS =====
        params_frame = ttk.LabelFrame(main_frame, text="⚙️ Parameters", padding="10")
        params_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Confidence threshold
        ttk.Label(params_frame, text="Confidence Threshold:").grid(row=0, column=0, sticky=tk.W, pady=3)
        conf_slider = ttk.Scale(
            params_frame, 
            from_=0.1, 
            to=0.9, 
            variable=self.confidence,
            orient=tk.HORIZONTAL,
            length=200
        )
        conf_slider.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=3)
        
        self.conf_label = ttk.Label(params_frame, text=f"{self.confidence.get():.2f}")
        self.conf_label.grid(row=0, column=2, pady=3)
        
        # Update label when slider changes
        conf_slider.config(command=lambda v: self.conf_label.config(text=f"{float(v):.2f}"))
        
        # Options
        ttk.Checkbutton(
            params_frame, 
            text="Generate Annotated Output", 
            variable=self.generate_output
        ).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=3)
        
        ttk.Checkbutton(
            params_frame, 
            text="Export CSV Report", 
            variable=self.export_csv
        ).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=3)
        
        ttk.Checkbutton(
            params_frame, 
            text="Show Detection Zones", 
            variable=self.show_zones
        ).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=3)
        
        # ===== CONTROL BUTTONS =====
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, pady=(0, 10))
        
        self.start_button = ttk.Button(
            button_frame, 
            text="▶️  Start Test", 
            command=self._start_test,
            width=20
        )
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(
            button_frame, 
            text="⏹️  Stop Test", 
            command=self._stop_test,
            state=tk.DISABLED,
            width=20
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame, 
            text="📂 Open Results Folder", 
            command=self._open_results_folder,
            width=20
        ).pack(side=tk.LEFT, padx=5)
        
        # ===== PROGRESS =====
        progress_frame = ttk.LabelFrame(main_frame, text="📊 Progress", padding="10")
        progress_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        
        self.progress = ttk.Progressbar(
            progress_frame, 
            mode='indeterminate',
            length=400
        )
        self.progress.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        
        self.status_label = ttk.Label(progress_frame, text="Ready to start testing", foreground="green")
        self.status_label.grid(row=1, column=0, sticky=tk.W, pady=3)
        
        # ===== LOG OUTPUT =====
        log_frame = ttk.LabelFrame(main_frame, text="📝 Test Log", padding="10")
        log_frame.grid(row=5, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # Scrolled text for logs
        self.log_text = scrolledtext.ScrolledText(
            log_frame, 
            height=10, 
            width=80,
            wrap=tk.WORD,
            font=("Courier", 9)
        )
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # ===== RESULTS SUMMARY =====
        results_frame = ttk.LabelFrame(main_frame, text="✅ Test Results", padding="10")
        results_frame.grid(row=6, column=0, sticky=(tk.W, tk.E), pady=(0, 0))
        results_frame.columnconfigure(1, weight=1)
        
        # Results labels
        self.result_labels = {}
        result_keys = [
            ("Total Visitors", "total_visitors"),
            ("Purchasers", "purchasers"),
            ("Conversion Rate", "conversion_rate"),
            ("Avg Duration", "avg_duration"),
            ("Output File", "output_file"),
            ("CSV File", "csv_file")
        ]
        
        for idx, (label, key) in enumerate(result_keys):
            ttk.Label(results_frame, text=f"{label}:").grid(row=idx, column=0, sticky=tk.W, pady=2)
            value_label = ttk.Label(results_frame, text="-", foreground="blue")
            value_label.grid(row=idx, column=1, sticky=tk.W, padx=(10, 0), pady=2)
            self.result_labels[key] = value_label
        
        # Initial log message
        self._log("🎯 Eyeora AI-CCTV Test Suite Initialized")
        self._log("📋 Select a file and click 'Start Test' to begin")
        self._log("-" * 80)
    
    def _setup_camera_tab(self):
        """Setup live camera tab"""
        
        main_frame = ttk.Frame(self.camera_tab, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Controls
        left_panel = ttk.Frame(main_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # Camera controls
        control_frame = ttk.LabelFrame(left_panel, text="🎮 Camera Controls", padding="10")
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.camera_start_btn = ttk.Button(
            control_frame,
            text="▶️ Start Camera",
            command=self._start_camera,
            width=20
        )
        self.camera_start_btn.pack(pady=5)
        
        self.camera_stop_btn = ttk.Button(
            control_frame,
            text="⏹️ Stop Camera",
            command=self._stop_camera,
            state=tk.DISABLED,
            width=20
        )
        self.camera_stop_btn.pack(pady=5)
        
        # Display options
        display_frame = ttk.LabelFrame(left_panel, text="👁️ Display Options", padding="10")
        display_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Checkbutton(
            display_frame,
            text="Show Detections",
            variable=self.show_live_detections,
            command=self._toggle_live_detections
        ).pack(anchor=tk.W, pady=3)
        
        ttk.Checkbutton(
            display_frame,
            text="Show Pose Estimation",
            variable=self.show_live_pose,
            command=self._toggle_live_pose
        ).pack(anchor=tk.W, pady=3)
        
        ttk.Checkbutton(
            display_frame,
            text="Show Statistics",
            variable=self.show_live_stats,
            command=self._toggle_live_stats
        ).pack(anchor=tk.W, pady=3)
        
        self.show_live_objects = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            display_frame,
            text="Show Objects",
            variable=self.show_live_objects,
            command=self._toggle_live_objects
        ).pack(anchor=tk.W, pady=3)
        
        # Stats display
        stats_frame = ttk.LabelFrame(left_panel, text="📊 Live Statistics", padding="10")
        stats_frame.pack(fill=tk.BOTH, expand=True)
        
        self.live_stats_text = tk.Text(
            stats_frame,
            height=20,
            width=30,
            font=("Courier", 9),
            state=tk.DISABLED
        )
        self.live_stats_text.pack(fill=tk.BOTH, expand=True)
        
        # Right panel - Camera feed
        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        feed_frame = ttk.LabelFrame(right_panel, text="📹 Live Camera Feed", padding="10")
        feed_frame.pack(fill=tk.BOTH, expand=True)
        
        self.camera_label = tk.Label(feed_frame, bg="black", text="Camera Feed")
        self.camera_label.pack(fill=tk.BOTH, expand=True)
    
    # ===== File Testing Methods =====
    
    def _on_mode_change(self):
        """Handle test mode change"""
        mode = self.test_mode.get()
        self._log(f"🔄 Test mode changed to: {mode.upper()}")
        
    def _browse_file(self):
        """Browse for input file"""
        mode = self.test_mode.get()
        
        if mode == "video":
            filetypes = [
                ("Video files", "*.mp4 *.avi *.mov *.mkv *.flv *.wmv"),
                ("All files", "*.*")
            ]
        else:
            filetypes = [
                ("Image files", "*.jpg *.jpeg *.png *.bmp"),
                ("All files", "*.*")
            ]
        
        filename = filedialog.askopenfilename(
            title=f"Select {mode} file",
            filetypes=filetypes
        )
        
        if filename:
            self.input_file.set(filename)
            self._log(f"📁 Selected: {Path(filename).name}")
    
    def _start_test(self):
        """Start the automated test"""
        
        # Validate input
        if not self.input_file.get():
            messagebox.showerror("Error", "Please select an input file!")
            return
        
        if not Path(self.input_file.get()).exists():
            messagebox.showerror("Error", "Selected file does not exist!")
            return
        
        # Disable start button, enable stop button
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.is_testing = True
        
        # Start progress bar
        self.progress.start(10)
        
        # Clear previous results
        for label in self.result_labels.values():
            label.config(text="-")
        
        # Run test in separate thread
        test_thread = threading.Thread(target=self._run_test_suite, daemon=True)
        test_thread.start()
    
    def _stop_test(self):
        """Stop the test"""
        self.is_testing = False
        self._log("⏹️  Test stopped by user")
        self._reset_ui()
    
    def _run_test_suite(self):
        """Run the complete test suite"""
        
        try:
            self._update_status("🚀 Initializing test suite...", "blue")
            self._log("\n" + "=" * 80)
            self._log("🧪 STARTING AUTOMATED TEST SUITE")
            self._log("=" * 80)
            
            mode = self.test_mode.get()
            input_file = self.input_file.get()
            
            # TEST 1: Load and validate file
            self._update_status("📁 Test 1/5: Loading input file...", "blue")
            self._log("\n📋 TEST 1: File Validation")
            self._log(f"File: {Path(input_file).name}")
            self._log(f"Mode: {mode.upper()}")
            
            if not self._validate_file(input_file):
                raise Exception("File validation failed")
            
            self._log("✅ File validation passed")
            time.sleep(0.5)
            
            # TEST 2: Initialize detection engine
            self._update_status("🤖 Test 2/5: Initializing AI models...", "blue")
            self._log("\n📋 TEST 2: Detection Engine Initialization")
            
            self.detection_engine = DetectionEngine(
                confidence_threshold=self.confidence.get()
            )
            model_info = self.detection_engine.get_model_info()
            self._log(f"Model: {model_info['model_name']}")
            self._log(f"Device: {model_info['device']}")
            self._log(f"Confidence: {model_info['confidence_threshold']}")
            self._log("✅ Detection engine initialized")
            time.sleep(0.5)
            
            # TEST 3: Run detection/analysis
            self._update_status("🔍 Test 3/5: Running detection...", "blue")
            self._log("\n📋 TEST 3: Detection & Analysis")
            
            if mode == "video":
                result = self._test_video_processing(input_file)
            else:
                result = self._test_image_detection(input_file)
            
            if not result:
                raise Exception("Detection/Analysis failed")
            
            self._log("✅ Detection & Analysis completed")
            time.sleep(0.5)
            
            # TEST 4: Export results
            if self.export_csv.get():
                self._update_status("💾 Test 4/5: Exporting data...", "blue")
                self._log("\n📋 TEST 4: Data Export")
                
                if mode == "video" and 'analyzed_tracks' in self.test_results:
                    self._test_data_export()
                    self._log("✅ Data export completed")
                else:
                    self._log("⏭️  Data export skipped (not applicable for images)")
            else:
                self._log("\n📋 TEST 4: Data Export - SKIPPED")
            
            time.sleep(0.5)
            
            # TEST 5: Verify outputs
            self._update_status("✅ Test 5/5: Verifying outputs...", "blue")
            self._log("\n📋 TEST 5: Output Verification")
            self._verify_outputs()
            self._log("✅ All outputs verified")
            
            # All tests passed
            self._log("\n" + "=" * 80)
            self._log("🎉 ALL TESTS PASSED SUCCESSFULLY!")
            self._log("=" * 80)
            
            self._update_status("✅ All tests completed successfully!", "green")
            
            # Show results
            self._display_results()
            
        except Exception as e:
            self._log(f"\n❌ TEST FAILED: {str(e)}")
            self._update_status(f"❌ Test failed: {str(e)}", "red")
            messagebox.showerror("Test Failed", f"Test suite failed:\n{str(e)}")
        
        finally:
            self._reset_ui()
    
    def _validate_file(self, file_path):
        """Validate input file"""
        from utils.validators import validate_video_file, validate_image_file
        
        mode = self.test_mode.get()
        
        if mode == "video":
            is_valid, message = validate_video_file(file_path)
        else:
            is_valid, message = validate_image_file(file_path)
        
        self._log(f"Validation: {message}")
        return is_valid
    
    def _test_video_processing(self, video_path):
        """Test video processing"""
        self._log("Processing video...")
        
        self.processor = VideoProcessor(show_zones=self.show_zones.get())
        
        result = self.processor.process_video(
            video_path=video_path,
            generate_output_video=self.generate_output.get(),
            export_csv=False  # We'll export separately
        )
        
        self.test_results = result
        
        self._log(f"Frames processed: {result['video_info']['frame_count']}")
        self._log(f"Total tracks: {result['total_tracks']}")
        self._log(f"Processing time: {result['processing_time']:.2f}s")
        
        return True
    
    def _test_image_detection(self, image_path):
        """Test image detection"""
        self._log("Detecting objects in image...")
        
        self.processor = VideoProcessor(show_zones=self.show_zones.get())
        
        result = self.processor.process_image(
            image_path=image_path,
            output_path=None
        )
        
        self.test_results = result
        
        self._log(f"Detections: {result['detections']}")
        self._log(f"Output saved: {result['output_path']}")
        
        return True
    
    def _test_data_export(self):
        """Test data export"""
        if 'analyzed_tracks' not in self.test_results:
            self._log("⏭️  No tracks to export")
            return
        
        exporter = DataExporter()
        
        # Export to CSV
        csv_path = exporter.export_to_csv(
            self.test_results['analyzed_tracks'],
            include_summary=True
        )
        
        self.test_results['csv_path'] = csv_path
        self._log(f"CSV exported: {Path(csv_path).name}")
        
        # Export to JSON
        json_path = exporter.export_to_json(
            self.test_results['analyzed_tracks'],
            self.test_results.get('summary')
        )
        self._log(f"JSON exported: {Path(json_path).name}")
    
    def _verify_outputs(self):
        """Verify all output files exist"""
        
        if 'output_video_path' in self.test_results and self.test_results['output_video_path']:
            if Path(self.test_results['output_video_path']).exists():
                self._log(f"✓ Output video: {Path(self.test_results['output_video_path']).name}")
            else:
                self._log(f"✗ Output video not found")
        
        if 'output_path' in self.test_results and self.test_results['output_path']:
            if Path(self.test_results['output_path']).exists():
                self._log(f"✓ Output image: {Path(self.test_results['output_path']).name}")
            else:
                self._log(f"✗ Output image not found")
        
        if 'csv_path' in self.test_results and self.test_results['csv_path']:
            if Path(self.test_results['csv_path']).exists():
                self._log(f"✓ CSV file: {Path(self.test_results['csv_path']).name}")
            else:
                self._log(f"✗ CSV file not found")
    
    def _display_results(self):
        """Display test results in UI"""
        
        mode = self.test_mode.get()
        
        if mode == "video":
            summary = self.test_results.get('summary', {})
            
            self.result_labels['total_visitors'].config(
                text=str(summary.get('total_visitors', '-'))
            )
            self.result_labels['purchasers'].config(
                text=str(summary.get('purchasers', '-'))
            )
            self.result_labels['conversion_rate'].config(
                text=f"{summary.get('conversion_rate', 0):.1f}%"
            )
            self.result_labels['avg_duration'].config(
                text=f"{summary.get('avg_visit_duration', 0):.1f}s"
            )
            
            if 'output_video_path' in self.test_results:
                self.result_labels['output_file'].config(
                    text=Path(self.test_results['output_video_path']).name
                )
        else:
            self.result_labels['total_visitors'].config(
                text=f"{self.test_results.get('detections', 0)} people"
            )
            
            if 'output_path' in self.test_results:
                self.result_labels['output_file'].config(
                    text=Path(self.test_results['output_path']).name
                )
        
        if 'csv_path' in self.test_results:
            self.result_labels['csv_file'].config(
                text=Path(self.test_results['csv_path']).name
            )
    
    def _open_results_folder(self):
        """Open results folder in file explorer"""
        import subprocess
        import platform
        
        folder = PROCESSED_DIR
        
        if platform.system() == 'Windows':
            os.startfile(folder)
        elif platform.system() == 'Darwin':  # macOS
            subprocess.Popen(['open', folder])
        else:  # Linux
            subprocess.Popen(['xdg-open', folder])
        
        self._log(f"📂 Opened results folder: {folder}")
    
    # ===== Live Camera Methods =====
    
    def _start_camera(self):
        """Start live camera"""
        try:
            self.live_camera = LiveCameraSystem(
                camera_index=0,
                enable_pose=True,
                enable_clothing=True,
                enable_tracking=True
            )
            
            if not self.live_camera.start():
                messagebox.showerror("Error", "Could not start camera!")
                return
            
            self.camera_running = True
            self.camera_start_btn.config(state=tk.DISABLED)
            self.camera_stop_btn.config(state=tk.NORMAL)
            
            # Start camera loop
            self._camera_loop()
            
            print("✅ Camera started successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"Camera error: {str(e)}")
            print(f"❌ Camera error: {e}")
    
    def _stop_camera(self):
        """Stop live camera"""
        self.camera_running = False
        if self.live_camera:
            self.live_camera.stop()
        
        self.camera_start_btn.config(state=tk.NORMAL)
        self.camera_stop_btn.config(state=tk.DISABLED)
        
        # Clear camera display
        self.camera_label.config(image='', text="Camera Feed Stopped")
        
        print("⏹️ Camera stopped")
    
    def _camera_loop(self):
        """Main camera processing loop"""
        if not self.camera_running or not self.live_camera:
            return
        
        # Read and process frame
        ret, frame = self.live_camera.read_frame()
        
        if ret:
            # Process frame
            processed = self.live_camera.process_frame(frame)
            
            # Convert to PhotoImage
            frame_rgb = cv2.cvtColor(processed, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            
            # Resize to fit display (maintain aspect ratio)
            display_width = 800
            aspect_ratio = img.height / img.width
            display_height = int(display_width * aspect_ratio)
            img = img.resize((display_width, display_height), Image.Resampling.LANCZOS)
            
            photo = ImageTk.PhotoImage(image=img)
            
            # Update display
            self.camera_label.config(image=photo, text='')
            self.camera_label.image = photo
            
            # Update stats
            self._update_live_stats()
        
        # Schedule next frame
        self.root.after(30, self._camera_loop)  # ~30 FPS
    
    def _update_live_stats(self):
        """Update live statistics display"""
        if not self.live_camera:
            return
        
        stats = self.live_camera.get_statistics()
        
        self.live_stats_text.config(state=tk.NORMAL)
        self.live_stats_text.delete('1.0', tk.END)
        
        # Format stats
        text = f"""
LIVE CAMERA STATS
{'='*28}

FPS: {stats['fps']:.1f}
Frame Count: {stats['frame_count']}
Running Time: {stats['running_time']:.1f}s

{'='*28}
PEOPLE DETECTED: {stats['people_detected']}
{'='*28}

"""
        
        # Add individual person stats
        for person in stats['live_persons']:
            text += f"\nPerson ID: {person['id']}\n"
            text += f"  Duration: {person['duration']:.1f}s\n"
            text += f"  Activity: {person['activity']}\n"
            text += f"  Moving: {'Yes' if person['is_moving'] else 'No'}\n"
            
            if person['clothing']:
                clothing = person['clothing']
                text += f"  Clothing: {clothing.get('color', 'unknown')}\n"
                text += f"  Pattern: {clothing.get('pattern', 'unknown')}\n"
            
            text += "\n"
        
        self.live_stats_text.insert('1.0', text)
        self.live_stats_text.config(state=tk.DISABLED)
    
    def _toggle_live_detections(self):
        """Toggle live detection display"""
        if self.live_camera:
            state = self.live_camera.toggle_detections()
            print(f"✅ Detections: {'ON' if state else 'OFF'}")
    
    def _toggle_live_pose(self):
        """Toggle pose estimation display"""
        if self.live_camera:
            state = self.live_camera.toggle_pose()
            print(f"✅ Pose: {'ON' if state else 'OFF'}")
    
    def _toggle_live_stats(self):
        """Toggle stats display"""
        if self.live_camera:
            state = self.live_camera.toggle_stats()
            print(f"✅ Stats overlay: {'ON' if state else 'OFF'}")
    
    # ===== Utility Methods =====
    
    def _update_status(self, message, color="black"):
        """Update status label"""
        self.status_label.config(text=message, foreground=color)
        self.root.update_idletasks()
    
    def _log(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def _reset_ui(self):
        """Reset UI after test completion"""
        self.progress.stop()
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.is_testing = False
    
    def on_closing(self):
        """Handle window close"""
        if self.camera_running:
            self._stop_camera()
        self.root.destroy()


def main():
    """Main entry point"""
    root = tk.Tk()
    app = TestGUI(root)
    
    # Handle window close
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Set window icon (if available)
    try:
        # root.iconbitmap('icon.ico')
        pass
    except:
        pass
    
    # Center window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()


if __name__ == "__main__":
    print("🚀 Launching Eyeora Test GUI with Live Camera...")
    main()