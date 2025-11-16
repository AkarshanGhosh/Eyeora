/**
 * Products Page Component
 * 
 * Displays Eyeora cameras from database
 * - Fetches cameras from backend API
 * - Shows "Coming Soon" if no products available
 * - Only admins can add cameras (via Admin Dashboard)
 */

import { useState, useEffect } from 'react';
import { Camera, Wifi, Shield, MapPin, AlertCircle, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Link } from 'react-router-dom';
import Navbar from '@/components/Navbar';
import Footer from '@/components/Footer';
import { CAMERA_ENDPOINTS } from '@/config/api';
import { useToast } from '@/hooks/use-toast';

interface CameraProduct {
  id: string;
  name: string;
  uid: string;
  image_url?: string;
  location?: string;
  description?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  created_by: string;
}

const Products = () => {
  const [cameras, setCameras] = useState<CameraProduct[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { toast } = useToast();

  useEffect(() => {
    fetchCameras();
  }, []);

  const fetchCameras = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(CAMERA_ENDPOINTS.LIST);
      
      if (response.ok) {
        const data = await response.json();
        // Filter to show only active cameras
        const activeCameras = data.filter((cam: CameraProduct) => cam.is_active);
        setCameras(activeCameras);
      } else if (response.status === 401 || response.status === 403) {
        // No authentication required for viewing, but API might require it
        // Show empty state if no public access
        setCameras([]);
      } else {
        throw new Error('Failed to fetch cameras');
      }
    } catch (err: any) {
      console.error('Error fetching cameras:', err);
      setError(err.message);
      // Don't show error toast, just show empty state
      setCameras([]);
    } finally {
      setLoading(false);
    }
  };

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
        <Navbar />
        <div className="container mx-auto px-4 py-32 flex flex-col items-center justify-center">
          <Loader2 className="w-12 h-12 animate-spin text-cyan-500 mb-4" />
          <p className="text-lg text-muted-foreground">Loading products...</p>
        </div>
        <Footer />
      </div>
    );
  }

  // Empty state - No cameras available
  if (cameras.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
        <Navbar />

        {/* Hero Section */}
        <section className="container mx-auto px-4 pt-20 pb-16">
          <div className="max-w-4xl mx-auto text-center animate-fade-in">
            <div className="inline-block px-4 py-2 bg-gradient-to-r from-cyan-500/10 to-blue-500/10 border border-cyan-500/20 rounded-full mb-4">
              <span className="text-sm font-semibold bg-gradient-to-r from-cyan-500 to-blue-500 bg-clip-text text-transparent">
                Coming Soon
              </span>
            </div>
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-6 bg-gradient-to-r from-cyan-500 to-blue-500 bg-clip-text text-transparent">
              Eyeora AI Cameras
            </h1>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto mb-8">
              We're preparing something amazing for you. Our AI-powered surveillance cameras will be available soon.
            </p>
          </div>
        </section>

        {/* Coming Soon Card */}
        <section className="container mx-auto px-4 pb-16">
          <div className="max-w-2xl mx-auto">
            <Card className="p-12 text-center border-slate-200 dark:border-slate-700">
              <div className="w-20 h-20 bg-gradient-to-r from-cyan-500/10 to-blue-500/10 rounded-full flex items-center justify-center mx-auto mb-6">
                <Camera className="w-10 h-10 text-cyan-500" />
              </div>
              <h2 className="text-2xl font-bold mb-4">No Products Available Yet</h2>
              <p className="text-muted-foreground mb-8 max-w-md mx-auto">
                We're working hard to bring you the best AI-powered CCTV cameras. 
                Stay tuned for exciting announcements!
              </p>
              
              {/* Feature Preview */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
                <div className="p-4 bg-secondary/50 rounded-lg">
                  <Camera className="w-6 h-6 text-cyan-500 mx-auto mb-2" />
                  <p className="text-sm font-medium">4K Quality</p>
                </div>
                <div className="p-4 bg-secondary/50 rounded-lg">
                  <Shield className="w-6 h-6 text-blue-500 mx-auto mb-2" />
                  <p className="text-sm font-medium">AI Detection</p>
                </div>
                <div className="p-4 bg-secondary/50 rounded-lg">
                  <Wifi className="w-6 h-6 text-green-500 mx-auto mb-2" />
                  <p className="text-sm font-medium">Cloud Connect</p>
                </div>
              </div>

              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Link to="/contact">
                  <Button className="bg-gradient-to-r from-cyan-500 to-blue-500 hover:opacity-90 text-white">
                    Contact Us for Updates
                  </Button>
                </Link>
                <Link to="/about">
                  <Button variant="outline">
                    Learn More About Eyeora
                  </Button>
                </Link>
              </div>
            </Card>
          </div>
        </section>

        <Footer />
      </div>
    );
  }

  // Main Products Display - When cameras are available
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <Navbar />

      {/* Hero Section */}
      <section className="container mx-auto px-4 pt-20 pb-16">
        <div className="max-w-6xl mx-auto text-center animate-fade-in">
          <div className="inline-block px-4 py-2 bg-gradient-to-r from-cyan-500/10 to-blue-500/10 border border-cyan-500/20 rounded-full mb-4">
            <span className="text-sm font-semibold bg-gradient-to-r from-cyan-500 to-blue-500 bg-clip-text text-transparent">
              AI-Powered Surveillance
            </span>
          </div>
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-6 bg-gradient-to-r from-cyan-500 to-blue-500 bg-clip-text text-transparent">
            Our Camera Products
          </h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Discover our range of intelligent AI-powered CCTV cameras designed for modern security needs.
          </p>
        </div>
      </section>

      {/* Camera Products Grid */}
      <section className="container mx-auto px-4 pb-16">
        <div className="max-w-6xl mx-auto">
          <div className="flex justify-between items-center mb-8">
            <h2 className="text-2xl font-bold">Available Cameras ({cameras.length})</h2>
            <Button
              variant="outline"
              onClick={fetchCameras}
              className="gap-2"
            >
              <Loader2 className="w-4 h-4" />
              Refresh
            </Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {cameras.map((camera) => (
              <Card
                key={camera.id}
                className="overflow-hidden hover:shadow-lg transition-all duration-300 border-slate-200 dark:border-slate-700"
              >
                {/* Camera Image */}
                <div className="aspect-video bg-gradient-to-br from-cyan-500/20 to-blue-500/20 flex items-center justify-center relative">
                  {camera.image_url ? (
                    <img
                      src={camera.image_url}
                      alt={camera.name}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        // Fallback to icon if image fails to load
                        e.currentTarget.style.display = 'none';
                      }}
                    />
                  ) : (
                    <Camera className="w-20 h-20 text-cyan-500" />
                  )}
                  <Badge className="absolute top-3 right-3 bg-green-500 text-white">
                    Active
                  </Badge>
                </div>

                {/* Camera Details */}
                <div className="p-6">
                  <h3 className="text-xl font-bold mb-2">{camera.name}</h3>
                  
                  <div className="flex items-center gap-2 text-sm text-muted-foreground mb-3">
                    <Camera className="w-4 h-4" />
                    <span className="font-mono text-xs">UID: {camera.uid}</span>
                  </div>

                  {camera.location && (
                    <div className="flex items-center gap-2 text-sm text-muted-foreground mb-3">
                      <MapPin className="w-4 h-4" />
                      <span>{camera.location}</span>
                    </div>
                  )}

                  {camera.description && (
                    <p className="text-sm text-muted-foreground mb-4 line-clamp-2">
                      {camera.description}
                    </p>
                  )}

                  {/* Features */}
                  <div className="flex flex-wrap gap-2 mb-4">
                    <Badge variant="outline" className="text-xs">
                      <Shield className="w-3 h-3 mr-1" />
                      AI Detection
                    </Badge>
                    <Badge variant="outline" className="text-xs">
                      <Wifi className="w-3 h-3 mr-1" />
                      Cloud Connected
                    </Badge>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex gap-2">
                    <Link to="/contact" className="flex-1">
                      <Button className="w-full bg-gradient-to-r from-cyan-500 to-blue-500 hover:opacity-90 text-white">
                        Inquire Now
                      </Button>
                    </Link>
                    <Link to="/user-dashboard">
                      <Button variant="outline">
                        View Details
                      </Button>
                    </Link>
                  </div>

                  {/* Metadata */}
                  <div className="mt-4 pt-4 border-t border-slate-200 dark:border-slate-700">
                    <p className="text-xs text-muted-foreground">
                      Added: {new Date(camera.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Why Choose Eyeora Section */}
      <section className="container mx-auto px-4 pb-16">
        <div className="max-w-4xl mx-auto">
          <Card className="p-12 bg-gradient-to-br from-cyan-500/10 to-blue-500/10 border-cyan-500/20 text-center">
            <h2 className="text-3xl font-bold mb-4">Why Choose Eyeora?</h2>
            <p className="text-muted-foreground text-lg mb-8 max-w-2xl mx-auto">
              Industry-leading AI technology meets enterprise-grade security for comprehensive surveillance solutions.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <div className="text-center">
                <div className="w-12 h-12 bg-cyan-500/10 rounded-full flex items-center justify-center mx-auto mb-3">
                  <Shield className="w-6 h-6 text-cyan-500" />
                </div>
                <h3 className="font-bold mb-2">Advanced AI</h3>
                <p className="text-sm text-muted-foreground">
                  98% accuracy in person detection and behavior analysis
                </p>
              </div>
              <div className="text-center">
                <div className="w-12 h-12 bg-blue-500/10 rounded-full flex items-center justify-center mx-auto mb-3">
                  <Wifi className="w-6 h-6 text-blue-500" />
                </div>
                <h3 className="font-bold mb-2">Cloud Ready</h3>
                <p className="text-sm text-muted-foreground">
                  Secure cloud storage with local backup options
                </p>
              </div>
              <div className="text-center">
                <div className="w-12 h-12 bg-green-500/10 rounded-full flex items-center justify-center mx-auto mb-3">
                  <Camera className="w-6 h-6 text-green-500" />
                </div>
                <h3 className="font-bold mb-2">4K Quality</h3>
                <p className="text-sm text-muted-foreground">
                  Crystal clear video with night vision up to 30m
                </p>
              </div>
            </div>
            <div className="flex gap-4 justify-center">
              <Link to="/contact">
                <Button className="bg-gradient-to-r from-cyan-500 to-blue-500 hover:opacity-90 text-white">
                  Contact Sales
                </Button>
              </Link>
              <Link to="/about">
                <Button variant="outline">
                  Learn More
                </Button>
              </Link>
            </div>
          </Card>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default Products;