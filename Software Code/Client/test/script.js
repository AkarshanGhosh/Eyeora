// ==================== CONFIGURATION ====================
const API_URL = "http://localhost:8000";

// ==================== GLOBAL VARIABLES ====================
// Live Stream Variables
let streaming = false;
let detecting = false;
let detectionInterval = null;
let videoStream = null;
let currentDetections = [];

// Canvas Elements
const liveCanvas = document.getElementById("liveCanvas");
const liveCtx = liveCanvas.getContext("2d");
const imageCanvas = document.getElementById("imageCanvas");
const imageCtx = imageCanvas.getContext("2d");
const videoCanvas = document.getElementById("videoCanvas");
const videoCtx = videoCanvas.getContext("2d");

// ==================== TAB SWITCHING ====================
function switchTab(index) {
    const tabs = document.querySelectorAll('.tab');
    const contents = document.querySelectorAll('.tab-content');
    
    tabs.forEach((tab, i) => {
        if (i === index) {
            tab.classList.add('active');
        } else {
            tab.classList.remove('active');
        }
    });
    
    contents.forEach((content, i) => {
        if (i === index) {
            content.classList.add('active');
        } else {
            content.classList.remove('active');
        }
    });
}

// ==================== LIVE STREAM FUNCTIONS ====================

async function startStream() {
    try {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            alert("❌ Your browser doesn't support camera access. Please use Chrome, Firefox, or Edge.");
            return;
        }

        videoStream = await navigator.mediaDevices.getUserMedia({ 
            video: { 
                width: { ideal: 640 },
                height: { ideal: 480 },
                facingMode: "user"
            } 
        });
        
        const videoElement = document.createElement('video');
        videoElement.srcObject = videoStream;
        videoElement.autoplay = true;
        videoElement.playsInline = true;
        
        videoElement.onloadedmetadata = () => {
            liveCanvas.width = videoElement.videoWidth || 640;
            liveCanvas.height = videoElement.videoHeight || 480;
            streaming = true;
            updateStreamStatus("🟢 Stream: Running");
            drawStreamFrame(videoElement);
        };
        
    } catch (error) {
        console.error("Camera access error:", error);
        
        let errorMessage = "❌ Could not access camera.\n\n";
        
        if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
            errorMessage += "Camera permission was denied.\n\nPlease:\n1. Click the camera icon in the address bar\n2. Allow camera access\n3. Refresh the page and try again";
        } else if (error.name === 'NotFoundError') {
            errorMessage += "No camera found on this device.";
        } else if (error.name === 'NotReadableError') {
            errorMessage += "Camera is already in use by another application.";
        } else {
            errorMessage += `Error: ${error.message}`;
        }
        
        alert(errorMessage);
        updateStreamStatus("❌ Camera Error");
    }
}

function drawStreamFrame(videoElement) {
    if (!streaming) return;
    
    liveCtx.drawImage(videoElement, 0, 0, liveCanvas.width, liveCanvas.height);
    
    if (detecting && currentDetections.length > 0) {
        drawDetectionsOnCanvas(liveCtx, currentDetections, liveCanvas.width, liveCanvas.height);
    }
    
    requestAnimationFrame(() => drawStreamFrame(videoElement));
}

function stopStream() {
    if (videoStream) {
        videoStream.getTracks().forEach(track => track.stop());
        videoStream = null;
    }
    streaming = false;
    stopLiveDetection();
    currentDetections = [];
    liveCtx.clearRect(0, 0, liveCanvas.width, liveCanvas.height);
    updateStreamStatus("⚪ Stream: Stopped");
    document.getElementById("liveDetectionInfo").innerHTML = "";
}

function startLiveDetection() {
    if (!streaming) {
        alert("⚠️ Please start the stream first!");
        return;
    }
    detecting = true;
    updateStreamStatus("🔴 Stream: Running | Detection: Active");
    captureFrameLoop();
}

function stopLiveDetection() {
    detecting = false;
    currentDetections = [];
    if (detectionInterval) {
        clearTimeout(detectionInterval);
    }
    if (streaming) {
        updateStreamStatus("🟢 Stream: Running | Detection: Stopped");
    }
    document.getElementById("liveDetectionInfo").innerHTML = "";
}

function captureFrameLoop() {
    if (!detecting || !streaming) return;
    sendFrameForDetection();
    detectionInterval = setTimeout(captureFrameLoop, 500);
}

async function sendFrameForDetection() {
    try {
        const dataURL = liveCanvas.toDataURL("image/jpeg", 0.7);

        const response = await fetch(`${API_URL}/detect/frame`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ image: dataURL })
        });

        const result = await response.json();
        
        if (result.error) {
            console.error("Detection error:", result.error);
            return;
        }
        
        if (result.detections && result.detections.length > 0) {
            currentDetections = result.detections;
            updateDetectionInfo("liveDetectionInfo", result.detections);
        } else {
            currentDetections = [];
            document.getElementById("liveDetectionInfo").innerHTML = 
                '<div class="detection-info">No objects detected</div>';
        }
    } catch (error) {
        console.error("Detection error:", error);
    }
}

// ==================== IMAGE DETECTION FUNCTIONS ====================

async function detectImage() {
    const fileInput = document.getElementById("imageInput");
    const file = fileInput.files[0];
    
    if (!file) {
        alert("⚠️ Please select an image first!");
        return;
    }

    updateStatus("imageStatus", "🔄 Processing...", "processing");
    document.getElementById("imageDetectionInfo").innerHTML = "";
    
    const reader = new FileReader();
    reader.onload = async function(e) {
        const img = new Image();
        img.onload = async function() {
            imageCanvas.width = img.width;
            imageCanvas.height = img.height;
            imageCtx.drawImage(img, 0, 0);
            document.getElementById("imageCanvasContainer").style.display = "block";
            
            await performImageDetection(file, img);
        };
        img.src = e.target.result;
    };
    reader.readAsDataURL(file);
}

async function performImageDetection(file, originalImage) {
    const formData = new FormData();
    formData.append("file", file);

    try {
        const response = await fetch(`${API_URL}/detect/image`, {
            method: "POST",
            body: formData
        });

        const result = await response.json();
        
        if (result.status === "success") {
            const annotatedImageUrl = `${API_URL}${result.annotated_file}?t=${Date.now()}`;
            
            const annotatedImg = new Image();
            annotatedImg.crossOrigin = "anonymous";
            
            annotatedImg.onload = function() {
                imageCanvas.width = annotatedImg.width;
                imageCanvas.height = annotatedImg.height;
                imageCtx.drawImage(annotatedImg, 0, 0);
                updateStatus("imageStatus", "✅ Detection Complete!", "success");
            };
            
            annotatedImg.onerror = function() {
                console.log("Could not load annotated image from backend");
                updateStatus("imageStatus", "✅ Detection Complete!", "success");
            };
            
            annotatedImg.src = annotatedImageUrl;
        } else {
            updateStatus("imageStatus", "❌ Detection failed", "error");
        }
    } catch (error) {
        console.error("Error:", error);
        updateStatus("imageStatus", `❌ Error: ${error.message}`, "error");
    }
}

// ==================== VIDEO DETECTION FUNCTIONS ====================

async function detectVideo() {
    const fileInput = document.getElementById("videoInput");
    const file = fileInput.files[0];
    
    if (!file) {
        alert("⚠️ Please select a video first!");
        return;
    }

    // Validate file type
    const validTypes = ['video/mp4', 'video/webm', 'video/avi', 'video/mov', 'video/quicktime'];
    const validExtensions = /\.(mp4|webm|avi|mov|mkv)$/i;
    
    if (!validTypes.includes(file.type) && !file.name.match(validExtensions)) {
        alert("⚠️ Please select a valid video file (MP4, WebM, AVI, or MOV)");
        return;
    }

    updateStatus("videoStatus", "🔄 Uploading and processing video... This may take several minutes.", "processing");
    document.getElementById("videoDetectionInfo").innerHTML = 
        '<div class="detection-info">⏳ Processing video frames... Please wait.</div>';
    
    const formData = new FormData();
    formData.append("file", file);

    try {
        const response = await fetch(`${API_URL}/detect/video`, {
            method: "POST",
            body: formData
        });

        const result = await response.json();
        console.log("Video detection result:", result);
        
        if (result.status === "success") {
            const videoPlayer = document.getElementById("videoPlayer");
            const videoUrl = `${API_URL}${result.annotated_file}?t=${Date.now()}`;
            
            console.log("Loading video from:", videoUrl);
            console.log("Video info:", result.video_info);
            
            // Clear any previous video
            videoPlayer.pause();
            videoPlayer.removeAttribute('src');
            videoPlayer.load();
            
            // Hide canvas, show video player
            videoPlayer.style.display = "block";
            document.getElementById("videoCanvasContainer").style.display = "none";
            
            updateStatus("videoStatus", "🔄 Loading processed video in player...", "processing");
            document.getElementById("videoDetectionInfo").innerHTML = 
                '<div class="detection-info">⏳ Loading video player...</div>';
            
            // Set up event handlers before setting source
            let loadTimeout = setTimeout(() => {
                console.warn("Video taking long to load...");
                document.getElementById("videoDetectionInfo").innerHTML = 
                    '<div class="detection-info">⏳ Large video detected, still loading...</div>';
            }, 5000);
            
            videoPlayer.onloadstart = function() {
                console.log("Video loading started...");
            };
            
            videoPlayer.onloadedmetadata = function() {
                clearTimeout(loadTimeout);
                console.log("✅ Video metadata loaded successfully");
                console.log(`Video dimensions: ${videoPlayer.videoWidth}x${videoPlayer.videoHeight}`);
                console.log(`Video duration: ${videoPlayer.duration} seconds`);
            };
            
            videoPlayer.oncanplay = function() {
                clearTimeout(loadTimeout);
                console.log("✅ Video ready to play");
                updateStatus("videoStatus", "✅ Video Processing Complete!", "success");
                document.getElementById("videoDetectionInfo").innerHTML = 
                    `<div class="detection-info">
                        ✅ Processed ${result.frames_processed} frames<br>
                        📹 ${result.video_info.width}x${result.video_info.height} @ ${result.video_info.fps}fps<br>
                        ▶️ Ready to play!
                    </div>`;
            };
            
            videoPlayer.onerror = function(e) {
                clearTimeout(loadTimeout);
                console.error("❌ Video load error:", e);
                console.error("Error code:", videoPlayer.error?.code);
                console.error("Error message:", videoPlayer.error?.message);
                
                let errorMsg = "Error loading video. ";
                
                if (videoPlayer.error) {
                    switch(videoPlayer.error.code) {
                        case 1:
                            errorMsg += "Loading was aborted.";
                            break;
                        case 2:
                            errorMsg += "Network error occurred.";
                            break;
                        case 3:
                            errorMsg += "Video format may not be supported by your browser.";
                            break;
                        case 4:
                            errorMsg += "Video source not found.";
                            break;
                        default:
                            errorMsg += "Unknown error occurred.";
                    }
                }
                
                updateStatus("videoStatus", `❌ ${errorMsg}`, "error");
                
                // Offer download option
                document.getElementById("videoDetectionInfo").innerHTML = `
                    <div class="detection-info" style="color: #f87171;">
                        ${errorMsg}<br><br>
                        The video was processed but your browser may not support the format.<br><br>
                        <a href="${videoUrl}" download="detected_video.mp4" 
                           style="color: #60a5fa; text-decoration: underline; font-weight: bold;">
                            📥 Click here to download the processed video
                        </a><br><br>
                        <small>Try opening the downloaded video in VLC or another media player.</small>
                    </div>
                `;
            };
            
            // Now set the source and load
            videoPlayer.src = videoUrl;
            videoPlayer.load();
            
        } else {
            updateStatus("videoStatus", `❌ ${result.error || "Video processing failed"}`, "error");
            document.getElementById("videoDetectionInfo").innerHTML = 
                `<div class="detection-info" style="color: #f87171;">${result.error || "Processing failed"}</div>`;
        }
    } catch (error) {
        console.error("Error:", error);
        updateStatus("videoStatus", `❌ Network Error: ${error.message}`, "error");
        document.getElementById("videoDetectionInfo").innerHTML = 
            `<div class="detection-info" style="color: #f87171;">
                Network error occurred: ${error.message}<br>
                Please check if the backend server is running.
            </div>`;
    }
}

// ==================== UTILITY FUNCTIONS ====================

function drawDetectionsOnCanvas(ctx, detections, canvasWidth, canvasHeight) {
    ctx.strokeStyle = "#00ff00";
    ctx.lineWidth = 3;
    ctx.font = "bold 16px Arial";
    ctx.shadowColor = "rgba(0, 0, 0, 0.5)";
    ctx.shadowBlur = 4;

    detections.forEach(det => {
        const [x1, y1, x2, y2] = det.bbox;
        
        // Draw bounding box
        ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
        
        // Draw label with background
        const label = `${det.class} ${Math.round(det.confidence * 100)}%`;
        const textMetrics = ctx.measureText(label);
        const textWidth = textMetrics.width;
        const textHeight = 20;
        
        // Background for text
        ctx.shadowBlur = 0;
        ctx.fillStyle = "rgba(0, 255, 0, 0.9)";
        ctx.fillRect(x1, y1 - textHeight - 5, textWidth + 10, textHeight + 5);
        
        // Text
        ctx.fillStyle = "#000";
        ctx.fillText(label, x1 + 5, y1 - 8);
        
        // Reset shadow for next box
        ctx.shadowBlur = 4;
    });
    
    // Reset shadow
    ctx.shadowBlur = 0;
}

function updateStatus(elementId, message, type = "") {
    const statusElement = document.getElementById(elementId);
    statusElement.textContent = message;
    statusElement.className = `status ${type}`;
}

function updateStreamStatus(message) {
    const statusElement = document.getElementById("streamStatus");
    statusElement.textContent = message;
}

function updateDetectionInfo(elementId, detections) {
    const infoElement = document.getElementById(elementId);
    
    if (detections.length === 0) {
        infoElement.innerHTML = '<div class="detection-info">No objects detected</div>';
        return;
    }
    
    // Count objects by class
    const objectCounts = {};
    detections.forEach(det => {
        objectCounts[det.class] = (objectCounts[det.class] || 0) + 1;
    });
    
    const objectList = Object.entries(objectCounts)
        .map(([cls, count]) => `${cls}: ${count}`)
        .join(", ");
    
    infoElement.innerHTML = `
        <div class="detection-info">
            🎯 Detected ${detections.length} object(s): ${objectList}
        </div>
    `;
}

function checkVideoSupport() {
    const video = document.createElement('video');
    const support = {
        mp4: video.canPlayType('video/mp4; codecs="avc1.42E01E"'),
        webm: video.canPlayType('video/webm; codecs="vp8, vorbis"'),
        mp4v: video.canPlayType('video/mp4; codecs="mp4v.20.8"')
    };
    console.log("🎥 Browser video format support:", support);
    return support;
}

// ==================== INITIALIZE ====================

window.addEventListener('load', () => {
    console.log("✅ Eyeora Vision Interface Loaded");
    console.log(`🔗 API URL: ${API_URL}`);
    checkVideoSupport();
    
    // Check if backend is reachable
    fetch(`${API_URL}/`)
        .then(response => {
            if (response.ok) {
                console.log("✅ Backend server is reachable");
            }
        })
        .catch(error => {
            console.warn("⚠️ Backend server is not reachable. Please start the server.");
            console.error(error);
        });
});