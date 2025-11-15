import { useState, useEffect, useRef } from 'react';
import { Video, Upload, Camera, Settings, PlayCircle, X, Plus, Trash2, Monitor, Eye, Activity, Users, Clock, CheckCircle, XCircle, Loader } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';

const API_BASE = 'http://localhost:8000';

const UserDashboard = () => {
  // User Info
  const [userInfo] = useState({
    name: 'John Doe',
    email: 'john.doe@example.com',
    plan: 'Premium',
    camerasAllowed: 5
  });

  // Video Upload
  const [selectedFile, setSelectedFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadedVideos, setUploadedVideos] = useState([]);
  const [processingJobs, setProcessingJobs] = useState({});

  // Camera Management
  const [savedCameras, setSavedCameras] = useState([
    { id: 'device-0', name: 'Device Camera', type: 'device', uid: 0 },
  ]);
  const [newCameraName, setNewCameraName] = useState('');
  const [newCameraUID, setNewCameraUID] = useState('');
  
  // Active Streams
  const [activeStreams, setActiveStreams] = useState([]);
  const [streamStats, setStreamStats] = useState({});
  const [streamErrors, setStreamErrors] = useState({});
  
  // Notification
  const [notification, setNotification] = useState(null);

  // Refs
  const wsRefs = useRef({});
  const streamImgRefs = useRef({});

  // Show notification
  const showNotification = (message, type = 'info') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 5000);
  };

  // Cleanup WebSockets on unmount
  useEffect(() => {
    return () => {
      Object.values(wsRefs.current).forEach(ws => {
        if (ws && ws.readyState === WebSocket.OPEN) {
          ws.close();
        }
      });
    };
  }, []);

  // ==================== VIDEO UPLOAD ====================
  const handleVideoUpload = async () => {
    if (!selectedFile) {
      showNotification('Please select a video file first', 'error');
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const xhr = new XMLHttpRequest();

      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          const percentComplete = Math.round((e.loaded / e.total) * 100);
          setUploadProgress(percentComplete);
        }
      });

      xhr.addEventListener('load', async () => {
        if (xhr.status === 200) {
          const data = JSON.parse(xhr.responseText);
          showNotification('Video uploaded! Starting processing...', 'success');
          
          const videoEntry = {
            name: selectedFile.name,
            timestamp: new Date().toISOString(),
            status: 'uploaded',
            jobId: data.job_id,
            ...data
          };
          
          setUploadedVideos(prev => [videoEntry, ...prev]);
          setSelectedFile(null);
          setUploadProgress(0);

          // Start processing
          await startVideoProcessing(data.job_id);
        } else {
          showNotification('Upload failed. Please try again.', 'error');
        }
        setIsUploading(false);
      });

      xhr.addEventListener('error', () => {
        showNotification('Network error during upload', 'error');
        setIsUploading(false);
      });

      xhr.open('POST', `${API_BASE}/video/upload?generate_output=true&export_csv=true`);
      xhr.send(formData);

    } catch (error) {
      showNotification('Upload error: ' + error.message, 'error');
      setIsUploading(false);
    }
  };

  const startVideoProcessing = async (jobId) => {
    try {
      const response = await fetch(`${API_BASE}/video/process/${jobId}`, {
        method: 'POST'
      });

      if (response.ok) {
        setProcessingJobs(prev => ({ ...prev, [jobId]: 'processing' }));
        showNotification('Video processing started', 'info');
        
        // Poll for status
        pollJobStatus(jobId);
      }
    } catch (error) {
      showNotification('Failed to start processing', 'error');
    }
  };

  const pollJobStatus = async (jobId) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`${API_BASE}/video/status/${jobId}`);
        
        if (!response.ok) {
          console.error('Failed to fetch job status:', response.status);
          clearInterval(pollInterval);
          return;
        }
        
        const data = await response.json();
        console.log('📊 Job status:', jobId, data);
        
        // Log error if present
        if (data.error) {
          console.error('❌ Processing error:', data.error);
        }

        setProcessingJobs(prev => ({ ...prev, [jobId]: data.status }));

        if (data.status === 'completed') {
          clearInterval(pollInterval);
          showNotification('Video processing completed!', 'success');
          
          // Fetch full results
          const resultsResponse = await fetch(`${API_BASE}/video/results/${jobId}`);
          const resultsData = await resultsResponse.json();
          console.log('✅ Job results:', resultsData);
          
          setUploadedVideos(prev => prev.map(v => 
            v.jobId === jobId ? { 
              ...v, 
              status: 'completed', 
              result: data.result,
              analytics: resultsData.analytics,
              files: resultsData.files
            } : v
          ));
        } else if (data.status === 'failed') {
          clearInterval(pollInterval);
          const errorMsg = data.error || 'Unknown error';
          showNotification('Video processing failed: ' + errorMsg, 'error');
          console.error('💥 Processing failed for job:', jobId, 'Error:', errorMsg);
          
          setUploadedVideos(prev => prev.map(v => 
            v.jobId === jobId ? { ...v, status: 'failed', error: errorMsg } : v
          ));
        }
      } catch (error) {
        console.error('Error polling job status:', error);
        clearInterval(pollInterval);
      }
    }, 3000);
  };

  // ==================== CAMERA MANAGEMENT ====================
  const addCamera = () => {
    if (!newCameraName || !newCameraUID) {
      showNotification('Please enter camera name and UID', 'error');
      return;
    }

    const newCamera = {
      id: `camera-${Date.now()}`,
      name: newCameraName,
      type: 'cctv',
      uid: newCameraUID
    };

    setSavedCameras(prev => [...prev, newCamera]);
    setNewCameraName('');
    setNewCameraUID('');
    showNotification('Camera added successfully', 'success');
  };

  const removeCamera = (cameraId) => {
    const activeStream = activeStreams.find(s => s.cameraId === cameraId);
    if (activeStream) {
      stopStream(cameraId);
    }
    
    setSavedCameras(prev => prev.filter(c => c.id !== cameraId));
    showNotification('Camera removed', 'info');
  };

  // ==================== STREAM MANAGEMENT ====================
  const startStream = async (camera) => {
    if (activeStreams.some(s => s.cameraId === camera.id)) {
      showNotification('Camera is already streaming', 'info');
      return;
    }

    try {
      const statusResponse = await fetch(`${API_BASE}/live/camera/status?camera_index=${camera.uid}`);
      const statusData = await statusResponse.json();

      if (!statusData.is_running) {
        const response = await fetch(
          `${API_BASE}/live/camera/start?camera_index=${camera.uid}&enable_pose=false&enable_clothing=true&enable_tracking=true&enable_objects=true`,
          { method: 'POST' }
        );
        
        const data = await response.json();
        
        if (data.status !== 'success' && data.status !== 'already_running') {
          throw new Error(data.message || 'Failed to start camera');
        }
      }

      const streamId = `stream-${camera.id}`;
      setActiveStreams(prev => [...prev, {
        id: streamId,
        cameraId: camera.id,
        cameraName: camera.name,
        cameraUID: camera.uid,
        startTime: new Date()
      }]);

      setStreamErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[streamId];
        return newErrors;
      });

      startStatsWebSocket(camera.uid, streamId);
      showNotification(`${camera.name} started successfully`, 'success');

    } catch (error) {
      showNotification('Failed to start camera: ' + error.message, 'error');
    }
  };

  const stopStream = async (cameraId) => {
    const stream = activeStreams.find(s => s.cameraId === cameraId);
    if (!stream) return;

    try {
      if (wsRefs.current[stream.id]) {
        wsRefs.current[stream.id].close();
        delete wsRefs.current[stream.id];
      }

      const camera = savedCameras.find(c => c.id === cameraId);
      await fetch(`${API_BASE}/live/camera/stop?camera_index=${camera.uid}`, {
        method: 'POST'
      });
      
      setActiveStreams(prev => prev.filter(s => s.cameraId !== cameraId));
      
      setStreamStats(prev => {
        const newStats = { ...prev };
        delete newStats[stream.id];
        return newStats;
      });
      
      setStreamErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[stream.id];
        return newErrors;
      });
      
      showNotification(`${stream.cameraName} stopped`, 'info');
      
    } catch (error) {
      showNotification('Error stopping camera: ' + error.message, 'error');
    }
  };

  // ==================== WEBSOCKET ====================
  const startStatsWebSocket = (cameraIndex, streamId) => {
    if (wsRefs.current[streamId]) {
      wsRefs.current[streamId].close();
    }

    const ws = new WebSocket(`ws://localhost:8000/live/ws/statistics?camera_index=${cameraIndex}`);
    
    ws.onopen = () => {
      console.log(`📡 WebSocket connected for ${streamId}`);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.type === 'statistics') {
          // Debug: Log the received statistics with full details
          console.log('📊 Received stats for', streamId);
          console.log('   FPS:', data.data.fps);
          console.log('   People:', data.data.people_detected);
          console.log('   Objects:', data.data.objects_detected);
          console.log('   Live Persons:', data.data.live_persons?.length);
          console.log('   Full data:', data.data);
          
          setStreamStats(prev => ({
            ...prev,
            [streamId]: data.data
          }));
          
          setStreamErrors(prev => {
            const newErrors = { ...prev };
            delete newErrors[streamId];
            return newErrors;
          });
        } else if (data.type === 'error') {
          console.error('❌ WebSocket error:', data.message);
          setStreamErrors(prev => ({
            ...prev,
            [streamId]: data.message
          }));
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setStreamErrors(prev => ({
        ...prev,
        [streamId]: 'Connection error'
      }));
    };

    ws.onclose = () => {
      console.log(`📡 WebSocket closed for ${streamId}`);
      delete wsRefs.current[streamId];
    };

    wsRefs.current[streamId] = ws;
  };

  // ==================== RENDER ====================
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-cyan-500 rounded-lg flex items-center justify-center">
                <Video className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">User Dashboard</h1>
                <p className="text-sm text-gray-500">Welcome back! Choose an option to get started.</p>
              </div>
            </div>
            <Button className="bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 flex items-center gap-2">
              <Settings className="w-4 h-4" />
              <span>Settings</span>
            </Button>
          </div>
        </div>
      </header>

      {/* Notification */}
      {notification && (
        <div className="fixed top-20 right-4 z-50 animate-in slide-in-from-right">
          <Alert className={`${
            notification.type === 'error' ? 'bg-red-50 border-red-200 text-red-800' :
            notification.type === 'success' ? 'bg-green-50 border-green-200 text-green-800' :
            'bg-blue-50 border-blue-200 text-blue-800'
          }`}>
            <AlertDescription className="flex items-center gap-2">
              {notification.type === 'success' && <CheckCircle className="w-4 h-4" />}
              {notification.type === 'error' && <XCircle className="w-4 h-4" />}
              {notification.message}
            </AlertDescription>
          </Alert>
        </div>
      )}

      <div className="container mx-auto px-6 py-8 space-y-6">
        {/* ==================== USER INFO ==================== */}
        <Card className="bg-white border border-gray-200 shadow-sm">
          <div className="p-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2 text-gray-900">
              <Settings className="w-5 h-5 text-cyan-500" />
              User Information
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {[
                { label: 'Name', value: userInfo.name },
                { label: 'Email', value: userInfo.email },
                { label: 'Plan', value: userInfo.plan, highlight: true },
                { label: 'Cameras', value: `${savedCameras.length} / ${userInfo.camerasAllowed}` }
              ].map((item, idx) => (
                <div key={idx}>
                  <Label className="text-gray-500 text-sm mb-1">{item.label}</Label>
                  <p className={`text-lg font-semibold ${item.highlight ? 'text-cyan-600' : 'text-gray-900'}`}>
                    {item.value}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </Card>

        {/* ==================== VIDEO UPLOAD ==================== */}
        <Card className="bg-white border border-gray-200 shadow-sm">
          <div className="p-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2 text-gray-900">
              <Upload className="w-5 h-5 text-cyan-500" />
              Video Analysis
            </h2>
            
            <div className="space-y-4">
              <div>
                <Label className="text-gray-700">Select Video File</Label>
                <Input
                  type="file"
                  accept="video/*"
                  onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                  className="mt-2 bg-white border-gray-300 text-gray-900"
                />
              </div>

              {selectedFile && (
                <div className="p-3 bg-gray-50 rounded-lg border border-gray-200">
                  <p className="text-sm text-gray-900 font-medium">Selected: {selectedFile.name}</p>
                  <p className="text-xs text-gray-500">Size: {(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>
                </div>
              )}

              {isUploading && (
                <div className="space-y-2">
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-cyan-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                  <p className="text-sm text-center text-gray-600">{uploadProgress}% uploaded</p>
                </div>
              )}

              <Button
                onClick={handleVideoUpload}
                disabled={!selectedFile || isUploading}
                className="w-full bg-cyan-500 hover:bg-cyan-600 text-white"
              >
                {isUploading ? (
                  <>
                    <Loader className="w-4 h-4 mr-2 animate-spin" />
                    Uploading...
                  </>
                ) : (
                  'Upload & Analyze'
                )}
              </Button>
            </div>

            {/* Recent Uploads */}
            {uploadedVideos.length > 0 && (
              <div className="mt-6">
                <h3 className="font-semibold mb-3 flex items-center gap-2 text-gray-900">
                  Recent Uploads
                  <span className="text-xs text-gray-500">({uploadedVideos.length})</span>
                </h3>
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {uploadedVideos.map((video, idx) => (
                    <div key={idx} className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                      <div className="flex justify-between items-start mb-2">
                        <div className="flex-1">
                          <p className="font-medium text-gray-900">{video.name}</p>
                          <p className="text-xs text-gray-500">
                            {new Date(video.timestamp).toLocaleString()}
                          </p>
                        </div>
                        <span className={`px-3 py-1 rounded-full text-xs font-semibold flex items-center gap-1 ${
                          video.status === 'processing' ? 'bg-yellow-100 text-yellow-800' : 
                          video.status === 'completed' ? 'bg-green-100 text-green-800' :
                          video.status === 'failed' ? 'bg-red-100 text-red-800' : 'bg-blue-100 text-blue-800'
                        }`}>
                          {video.status === 'processing' && <Loader className="w-3 h-3 animate-spin" />}
                          {video.status === 'completed' && <CheckCircle className="w-3 h-3" />}
                          {video.status === 'failed' && <XCircle className="w-3 h-3" />}
                          {video.status}
                        </span>
                      </div>

                      {/* Analytics Results */}
                      {video.status === 'completed' && video.analytics && (
                        <div className="mt-3 p-3 bg-white rounded border border-gray-200">
                          <h4 className="text-xs font-semibold text-gray-700 mb-2">Analytics Results:</h4>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
                            <div>
                              <span className="text-gray-500">Total Visitors:</span>
                              <span className="ml-1 font-semibold text-gray-900">{video.analytics.total_visitors}</span>
                            </div>
                            <div>
                              <span className="text-gray-500">Purchasers:</span>
                              <span className="ml-1 font-semibold text-green-600">{video.analytics.purchasers}</span>
                            </div>
                            <div>
                              <span className="text-gray-500">Conversion:</span>
                              <span className="ml-1 font-semibold text-blue-600">{video.analytics.conversion_rate}%</span>
                            </div>
                            <div>
                              <span className="text-gray-500">Avg Duration:</span>
                              <span className="ml-1 font-semibold text-purple-600">{video.analytics.avg_visit_duration}s</span>
                            </div>
                          </div>
                          
                          {/* Download Links */}
                          {video.files && (
                            <div className="mt-3 flex gap-2">
                              {video.files.output_video && (
                                <a 
                                  href={`${API_BASE}${video.files.output_video}`}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-xs px-3 py-1 bg-cyan-500 text-white rounded hover:bg-cyan-600 flex items-center gap-1"
                                >
                                  <Video className="w-3 h-3" />
                                  Download Video
                                </a>
                              )}
                              {video.files.csv && (
                                <a 
                                  href={`${API_BASE}${video.files.csv}`}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-xs px-3 py-1 bg-green-500 text-white rounded hover:bg-green-600 flex items-center gap-1"
                                >
                                  <Upload className="w-3 h-3" />
                                  Download CSV
                                </a>
                              )}
                            </div>
                          )}
                        </div>
                      )}

                      {/* Error Message */}
                      {video.status === 'failed' && video.error && (
                        <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded">
                          <p className="text-xs text-red-700">Error: {video.error}</p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </Card>

        {/* ==================== CAMERA MANAGEMENT ==================== */}
        <Card className="bg-white border border-gray-200 shadow-sm">
          <div className="p-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2 text-gray-900">
              <Camera className="w-5 h-5 text-cyan-500" />
              Camera Management
            </h2>

            {/* Add Camera */}
            <div className="mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
              <h3 className="font-semibold mb-3 text-gray-900">Add New Camera</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <Input
                  placeholder="Camera Name"
                  value={newCameraName}
                  onChange={(e) => setNewCameraName(e.target.value)}
                  className="bg-white border-gray-300 text-gray-900"
                />
                <Input
                  placeholder="Camera UID (e.g., 0, 1, rtsp://...)"
                  value={newCameraUID}
                  onChange={(e) => setNewCameraUID(e.target.value)}
                  className="bg-white border-gray-300 text-gray-900"
                />
                <Button onClick={addCamera} className="bg-green-500 hover:bg-green-600 text-white">
                  <Plus className="w-4 h-4 mr-2" />
                  Add Camera
                </Button>
              </div>
            </div>

            {/* Saved Cameras */}
            <div>
              <h3 className="font-semibold mb-3 text-gray-900">Saved Cameras ({savedCameras.length})</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {savedCameras.map((camera) => (
                  <div key={camera.id} className="p-4 bg-white rounded-lg border border-gray-200 hover:border-cyan-400 hover:shadow-md transition-all">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <h4 className="font-semibold text-gray-900">{camera.name}</h4>
                        <p className="text-xs text-gray-500">{camera.type === 'device' ? '📹 Device Camera' : '📡 CCTV'}</p>
                        <p className="text-xs text-gray-400 mt-1">UID: {camera.uid}</p>
                      </div>
                      {camera.type !== 'device' && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => removeCamera(camera.id)}
                          className="text-red-500 hover:text-red-600 hover:bg-red-50"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      )}
                    </div>
                    
                    <Button
                      onClick={() => startStream(camera)}
                      disabled={activeStreams.some(s => s.cameraId === camera.id)}
                      className="w-full bg-cyan-500 hover:bg-cyan-600 text-white disabled:bg-gray-300 disabled:text-gray-500"
                    >
                      {activeStreams.some(s => s.cameraId === camera.id) ? (
                        <>
                          <Eye className="w-4 h-4 mr-2" />
                          Streaming
                        </>
                      ) : (
                        <>
                          <PlayCircle className="w-4 h-4 mr-2" />
                          Start Stream
                        </>
                      )}
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </Card>

        {/* ==================== LIVE STREAMS ==================== */}
        {activeStreams.length > 0 && (
          <Card className="bg-white border border-gray-200 shadow-sm">
            <div className="p-6">
              <h2 className="text-xl font-semibold mb-4 flex items-center gap-2 text-gray-900">
                <Monitor className="w-5 h-5 text-cyan-500" />
                Live Streams ({activeStreams.length})
              </h2>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {activeStreams.map((stream) => {
                  const stats = streamStats[stream.id] || {};
                  const error = streamErrors[stream.id];
                  
                  return (
                    <div key={stream.id} className="bg-white rounded-lg border border-gray-200 overflow-hidden shadow-sm">
                      {/* Stream Header */}
                      <div className="p-4 bg-gray-50 flex justify-between items-center border-b border-gray-200">
                        <div>
                          <h3 className="font-semibold flex items-center gap-2 text-gray-900">
                            {stream.cameraName}
                            <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></span>
                          </h3>
                          <p className="text-xs text-gray-500">UID: {stream.cameraUID}</p>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => stopStream(stream.cameraId)}
                          className="text-red-500 hover:text-red-600 hover:bg-red-50"
                        >
                          <X className="w-5 h-5" />
                        </Button>
                      </div>

                      {/* Video Feed */}
                      <div className="relative bg-black aspect-video">
                        {error ? (
                          <div className="absolute inset-0 flex items-center justify-center text-red-500">
                            <div className="text-center">
                              <XCircle className="w-12 h-12 mx-auto mb-2" />
                              <p className="text-white">{error}</p>
                            </div>
                          </div>
                        ) : (
                          <>
                            <img
                              ref={el => streamImgRefs.current[stream.id] = el}
                              src={`${API_BASE}/live/stream?camera_index=${stream.cameraUID}&t=${Date.now()}`}
                              alt={stream.cameraName}
                              className="w-full h-full object-contain"
                              onError={(e) => {
                                // Don't show error if stream was intentionally stopped
                                if (activeStreams.some(s => s.id === stream.id)) {
                                  console.error('Stream load error for', stream.id);
                                  setStreamErrors(prev => ({
                                    ...prev,
                                    [stream.id]: 'Failed to load stream'
                                  }));
                                }
                              }}
                            />
                            
                            {/* Stats Overlay (like in video) */}
                            {stats && Object.keys(stats).length > 0 && (
                              <div className="absolute top-12 left-2 bg-black/70 text-white text-xs p-2 rounded space-y-0.5 font-mono">
                                <div>FPS: {typeof stats.fps === 'number' ? stats.fps.toFixed(1) : '0.0'}</div>
                                <div>People: {stats.people_detected || stats.live_persons?.length || 0}</div>
                                <div>Objects: {stats.objects_detected || stats.objects?.length || 0}</div>
                                <div>Tracked: {stats.live_persons?.length || 0}</div>
                              </div>
                            )}
                          </>
                        )}
                        
                        {/* Live Badge */}
                        <div className="absolute top-2 left-2 px-2 py-1 bg-red-500 rounded flex items-center gap-1">
                          <div className="w-2 h-2 bg-white rounded-full animate-pulse" />
                          <span className="text-xs font-semibold text-white">LIVE</span>
                        </div>
                      </div>

                      {/* Statistics */}
                      <div className="p-4 grid grid-cols-3 gap-4 border-t border-gray-200 bg-gray-50">
                        <div className="text-center">
                          <Users className="w-5 h-5 mx-auto text-cyan-500 mb-1" />
                          <p className="text-2xl font-bold text-gray-900">
                            {stats.people_detected || stats.live_persons?.length || 0}
                          </p>
                          <p className="text-xs text-gray-500">People</p>
                        </div>
                        <div className="text-center">
                          <Activity className="w-5 h-5 mx-auto text-green-500 mb-1" />
                          <p className="text-2xl font-bold text-gray-900">
                            {typeof stats.fps === 'number' ? stats.fps.toFixed(1) : '0.0'}
                          </p>
                          <p className="text-xs text-gray-500">FPS</p>
                        </div>
                        <div className="text-center">
                          <Clock className="w-5 h-5 mx-auto text-purple-500 mb-1" />
                          <p className="text-2xl font-bold text-gray-900">
                            {stats.objects_detected || stats.objects?.length || 0}
                          </p>
                          <p className="text-xs text-gray-500">Objects</p>
                        </div>
                      </div>

                      {/* Person Details */}
                      {stats.live_persons && stats.live_persons.length > 0 && (
                        <div className="px-4 pb-4 bg-white">
                          <h4 className="text-sm font-semibold mb-2 text-gray-700">Tracked Persons:</h4>
                          <div className="space-y-2 max-h-40 overflow-y-auto">
                            {stats.live_persons.map((person) => (
                              <div key={person.id} className="text-xs bg-gray-50 p-2 rounded border border-gray-200">
                                <div className="flex justify-between mb-1">
                                  <span className="font-semibold text-cyan-600">Person #{person.id}</span>
                                  <span className="text-gray-500">{person.duration}s</span>
                                </div>
                                <div className="text-gray-600 space-y-0.5">
                                  <div>Activity: <span className="text-gray-900 font-medium">{person.activity}</span></div>
                                  {person.clothing && (
                                    <div>Clothing: <span className="text-gray-900 font-medium">{person.clothing}</span></div>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </Card>
        )}
      </div>
    </div>
  );
};

export default UserDashboard;