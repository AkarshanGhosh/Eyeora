/**
 * API Configuration File
 * 
 * This file contains all API endpoints for the Eyeora CCTV platform.
 * Base URL can be easily updated here for different environments.
 */

// Base API URL - Use localhost instead of 127.0.0.1 for better CORS compatibility
export const API_BASE_URL = 'http://localhost:8000';

/**
 * Authentication APIs
 */
export const AUTH_ENDPOINTS = {
  // Register new user
  REGISTER: `${API_BASE_URL}/auth/register`,
  
  // Login (form data)
  LOGIN: `${API_BASE_URL}/auth/login`,
  
  // Login (JSON format)
  LOGIN_JSON: `${API_BASE_URL}/auth/login_json`,
  
  // Get current user information
  GET_CURRENT_USER: `${API_BASE_URL}/auth/me`,
  
  // Logout
  LOGOUT: `${API_BASE_URL}/auth/logout`,
};

/**
 * Admin APIs - All require admin authentication
 */
export const ADMIN_ENDPOINTS = {
  // Dashboard Analytics
  DASHBOARD: `${API_BASE_URL}/admin/dashboard`,
  
  // Statistics
  USER_STATS: `${API_BASE_URL}/admin/stats/users`,
  CAMERA_STATS: `${API_BASE_URL}/admin/stats/cameras`,
  MEDIA_STATS: `${API_BASE_URL}/admin/stats/media`,
  
  // User Management
  LIST_USERS: `${API_BASE_URL}/admin/users`,
  GET_USER: (userId: string) => `${API_BASE_URL}/admin/users/${userId}`,
  UPDATE_USER: (userId: string) => `${API_BASE_URL}/admin/users/${userId}`,
  DELETE_USER: (userId: string) => `${API_BASE_URL}/admin/users/${userId}`,
  
  // Media Management
  LIST_VIDEOS: `${API_BASE_URL}/admin/media/videos`,
  LIST_IMAGES: `${API_BASE_URL}/admin/media/images`,
  DELETE_VIDEO: (filename: string) => `${API_BASE_URL}/admin/media/videos/${filename}`,
  DELETE_IMAGE: (filename: string) => `${API_BASE_URL}/admin/media/images/${filename}`,
};

/**
 * Camera Management APIs - Admin only
 */
export const CAMERA_ENDPOINTS = {
  // List all cameras
  LIST: `${API_BASE_URL}/cameras`,
  
  // Create new camera
  CREATE: `${API_BASE_URL}/cameras`,
  
  // Get camera by UID
  GET: (uid: string) => `${API_BASE_URL}/cameras/${uid}`,
  
  // Update camera
  UPDATE: (uid: string) => `${API_BASE_URL}/cameras/${uid}`,
  
  // Delete camera
  DELETE: (uid: string) => `${API_BASE_URL}/cameras/${uid}`,
};

/**
 * Live Camera Control APIs
 */
export const LIVE_CAMERA_ENDPOINTS = {
  // Start the camera feed
  START_CAMERA: `${API_BASE_URL}/live/camera/start`,
  
  // Stop the camera feed
  STOP_CAMERA: `${API_BASE_URL}/live/camera/stop`,
  
  // Get camera status
  CAMERA_STATUS: `${API_BASE_URL}/live/camera/status`,
  
  // Get camera statistics
  STATISTICS: `${API_BASE_URL}/live/statistics`,
  
  // Toggle display features (pose, objects, etc.)
  TOGGLE_DISPLAY: (feature: string) => `${API_BASE_URL}/live/display/toggle/${feature}`,
  
  // Get all detected persons
  GET_PERSONS: `${API_BASE_URL}/live/persons`,
  
  // Get specific person details
  GET_PERSON_DETAILS: (personId: string) => `${API_BASE_URL}/live/persons/${personId}`,
  
  // Get detected objects
  GET_OBJECTS: `${API_BASE_URL}/live/objects`,
  
  // Get snapshot (base64 image)
  SNAPSHOT: `${API_BASE_URL}/live/snapshot`,
  
  // Live system health
  HEALTH: `${API_BASE_URL}/live/health`,
};

/**
 * Live Streaming APIs
 */
export const STREAMING_ENDPOINTS = {
  // MJPEG stream (for img tag)
  MJPEG_STREAM: `${API_BASE_URL}/live/stream`,
  
  // WebSocket for live statistics
  WS_STATISTICS: `ws://localhost:8000/live/ws/statistics`,
  
  // WebSocket for live frames (base64)
  WS_FRAMES: `ws://localhost:8000/live/ws/frames`,
};

/**
 * Image Detection APIs
 */
export const IMAGE_DETECTION_ENDPOINTS = {
  // Detect people in uploaded image
  DETECT_IMAGE: `${API_BASE_URL}/detect/image`,
};

/**
 * Video Processing APIs (Upload & Analytics)
 */
export const VIDEO_PROCESSING_ENDPOINTS = {
  // Upload video file
  UPLOAD_VIDEO: `${API_BASE_URL}/video/upload`,
  
  // Start processing uploaded video
  START_PROCESSING: (jobId: string) => `${API_BASE_URL}/video/process/${jobId}`,
  
  // Get processing status
  GET_STATUS: (jobId: string) => `${API_BASE_URL}/video/status/${jobId}`,
  
  // Get processing results
  GET_RESULTS: (jobId: string) => `${API_BASE_URL}/video/results/${jobId}`,
  
  // Download processed video
  DOWNLOAD_VIDEO: (jobId: string) => `${API_BASE_URL}/video/download/video/${jobId}`,
  
  // Download CSV analytics
  DOWNLOAD_CSV: (jobId: string) => `${API_BASE_URL}/video/download/csv/${jobId}`,
  
  // List all processing jobs
  LIST_JOBS: `${API_BASE_URL}/video/jobs`,
  
  // Delete job and all associated files
  DELETE_JOB: (jobId: string) => `${API_BASE_URL}/video/jobs/${jobId}`,
  
  // Video processing health check
  HEALTH: `${API_BASE_URL}/video/health`,
};

/**
 * Static File Access APIs
 */
export const STATIC_FILE_ENDPOINTS = {
  // Uploaded images
  UPLOADED_IMAGE: (filename: string) => `${API_BASE_URL}/uploads/images/${filename}`,
  
  // Uploaded videos
  UPLOADED_VIDEO: (filename: string) => `${API_BASE_URL}/uploads/videos/${filename}`,
  
  // Processed images
  PROCESSED_IMAGE: (filename: string) => `${API_BASE_URL}/processed/images/${filename}`,
  
  // Processed videos
  PROCESSED_VIDEO: (filename: string) => `${API_BASE_URL}/processed/videos/${filename}`,
  
  // Analytics CSV files
  CSV_FILE: (filename: string) => `${API_BASE_URL}/data/csv/${filename}`,
};

/**
 * Legacy Detection APIs
 */
export const LEGACY_DETECTION_ENDPOINTS = {
  // Video detection (legacy)
  DETECT_VIDEO: `${API_BASE_URL}/detect/video`,
};

/**
 * Analytics APIs
 */
export const ANALYTICS_ENDPOINTS = {
  // Get summary analytics
  SUMMARY: `${API_BASE_URL}/analytics/summary`,
  
  // Get alert list
  ALERTS: `${API_BASE_URL}/analytics/alerts`,
};

/**
 * System & Network APIs
 */
export const SYSTEM_ENDPOINTS = {
  // System status
  STATUS: `${API_BASE_URL}/status`,
  
  // General health check
  HEALTH: `${API_BASE_URL}/health`,
  
  // Network info
  NETWORK_INFO: `${API_BASE_URL}/ip`,
};

/**
 * Database APIs
 */
export const DATABASE_ENDPOINTS = {
  // Database ping/health check
  PING: `${API_BASE_URL}/db/ping`,
};

/**
 * Frontend & Static Pages
 */
export const FRONTEND_ENDPOINTS = {
  // Root dashboard
  ROOT: `${API_BASE_URL}/`,
  
  // CSS file
  CSS: `${API_BASE_URL}/styles.css`,
  
  // JavaScript file
  JS: `${API_BASE_URL}/script.js`,
  
  // WiFi config page
  WIFI_CONFIG: `${API_BASE_URL}/config`,
  
  // WiFi connect submit
  WIFI_CONNECT: `${API_BASE_URL}/connect`,
};

/**
 * Legacy Live Stream
 */
export const LEGACY_STREAM_ENDPOINTS = {
  // Direct CV2 video feed
  VIDEO_FEED: `${API_BASE_URL}/video_feed`,
};

/**
 * Helper function to add authentication header
 */
export const getAuthHeaders = (token: string | null) => {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  return headers;
};

/**
 * Helper function for multipart/form-data requests
 */
export const getAuthHeadersMultipart = (token: string | null) => {
  const headers: Record<string, string> = {};
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  return headers;
};