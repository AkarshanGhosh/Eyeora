/**
 * User Dashboard Component
 * 
 * Dashboard for regular users to:
 * - Upload videos for analysis
 * - Access device camera
 * - Add CCTV cameras
 * - View account information
 */

import { useState } from 'react';
import { Video, Upload, Camera, Settings, PlayCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import Navbar from '@/components/Navbar';
import Footer from '@/components/Footer';
import { VIDEO_PROCESSING_ENDPOINTS, LIVE_CAMERA_ENDPOINTS } from '@/config/api';
import { useToast } from '@/hooks/use-toast';

const UserDashboard = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [cameraId, setCameraId] = useState('');
  const { toast } = useToast();

  // Handle video upload
  const handleVideoUpload = async () => {
    if (!selectedFile) {
      toast({
        title: 'No File Selected',
        description: 'Please select a video file first',
        variant: 'destructive',
      });
      return;
    }

    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await fetch(VIDEO_PROCESSING_ENDPOINTS.UPLOAD_VIDEO, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (response.ok) {
        toast({
          title: 'Upload Successful',
          description: `Job ID: ${data.job_id}`,
        });
        setSelectedFile(null);
      } else {
        toast({
          title: 'Upload Failed',
          description: data.message || 'Unable to upload video',
          variant: 'destructive',
        });
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Unable to connect to server',
        variant: 'destructive',
      });
    } finally {
      setIsUploading(false);
    }
  };

  // Handle device camera access
  const handleDeviceCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      toast({
        title: 'Camera Accessed',
        description: 'Device camera is now active',
      });
      // Handle stream (display in video element, etc.)
      console.log('Camera stream:', stream);
    } catch (error) {
      toast({
        title: 'Camera Access Denied',
        description: 'Unable to access device camera',
        variant: 'destructive',
      });
    }
  };

  // Start CCTV camera by ID
  const handleCCTVCamera = async () => {
    if (!cameraId) {
      toast({
        title: 'No Camera ID',
        description: 'Please enter a camera ID',
        variant: 'destructive',
      });
      return;
    }

    try {
      const response = await fetch(LIVE_CAMERA_ENDPOINTS.START_CAMERA, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ camera_id: cameraId }),
      });

      if (response.ok) {
        toast({
          title: 'Camera Started',
          description: `CCTV camera ${cameraId} is now active`,
        });
      } else {
        toast({
          title: 'Failed to Start Camera',
          description: 'Unable to connect to CCTV camera',
          variant: 'destructive',
        });
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Unable to connect to server',
        variant: 'destructive',
      });
    }
  };

  // Dashboard options
  const dashboardOptions = [
    {
      icon: Upload,
      title: 'Upload Video',
      description: 'Upload a video file for AI analysis and detection',
      action: 'upload',
    },
    {
      icon: Camera,
      title: 'Use Device Camera',
      description: 'Access your laptop or phone camera for live detection',
      action: 'device',
    },
    {
      icon: Video,
      title: 'Add CCTV Camera',
      description: 'Connect a security camera using its unique ID',
      action: 'cctv',
    },
    {
      icon: Settings,
      title: 'Account Settings',
      description: 'Manage your account information and preferences',
      action: 'settings',
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-hero">
      <Navbar />

      {/* Dashboard Header */}
      <section className="container mx-auto px-4 pt-20 pb-12">
        <div className="max-w-6xl mx-auto">
          <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
            User Dashboard
          </h1>
          <p className="text-muted-foreground text-lg">Welcome back! Choose an option to get started.</p>
        </div>
      </section>

      {/* Dashboard Options Grid */}
      <section className="container mx-auto px-4 pb-16">
        <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-6">
          {dashboardOptions.map((option, index) => (
            <Card
              key={index}
              className="p-6 hover:shadow-elegant hover:border-primary/50 transition-all duration-300 cursor-pointer group"
            >
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-gradient-primary rounded-lg flex items-center justify-center group-hover:scale-110 transition-transform">
                  <option.icon className="w-6 h-6 text-primary-foreground" />
                </div>
                <div className="flex-1">
                  <h3 className="text-xl font-semibold mb-1">{option.title}</h3>
                  <p className="text-muted-foreground text-sm">{option.description}</p>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </section>

      {/* Video Upload Section */}
      <section className="container mx-auto px-4 pb-16">
        <div className="max-w-2xl mx-auto">
          <Card className="p-8">
            <h2 className="text-2xl font-bold mb-6">Upload Video for Analysis</h2>
            <div className="space-y-4">
              <div>
                <Label htmlFor="video-file">Select Video File</Label>
                <Input
                  id="video-file"
                  type="file"
                  accept="video/*"
                  onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                  className="mt-2"
                />
              </div>
              <Button
                onClick={handleVideoUpload}
                disabled={!selectedFile || isUploading}
                className="w-full bg-gradient-primary hover:opacity-90"
              >
                {isUploading ? 'Uploading...' : 'Upload & Analyze'}
              </Button>
            </div>
          </Card>
        </div>
      </section>

      {/* Device Camera Section */}
      <section className="container mx-auto px-4 pb-16">
        <div className="max-w-2xl mx-auto">
          <Card className="p-8">
            <h2 className="text-2xl font-bold mb-6">Access Device Camera</h2>
            <p className="text-muted-foreground mb-4">
              Use your laptop or mobile camera for real-time object detection
            </p>
            <Button onClick={handleDeviceCamera} className="w-full bg-gradient-primary hover:opacity-90">
              <PlayCircle className="mr-2 w-5 h-5" />
              Start Device Camera
            </Button>
          </Card>
        </div>
      </section>

      {/* CCTV Camera Section */}
      <section className="container mx-auto px-4 pb-16">
        <div className="max-w-2xl mx-auto">
          <Card className="p-8">
            <h2 className="text-2xl font-bold mb-6">Connect CCTV Camera</h2>
            <div className="space-y-4">
              <div>
                <Label htmlFor="camera-id">Camera Unique ID (UID)</Label>
                <Input
                  id="camera-id"
                  placeholder="Enter camera UID"
                  value={cameraId}
                  onChange={(e) => setCameraId(e.target.value)}
                  className="mt-2"
                />
              </div>
              <Button onClick={handleCCTVCamera} className="w-full bg-gradient-primary hover:opacity-90">
                Connect Camera
              </Button>
            </div>
          </Card>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default UserDashboard;
