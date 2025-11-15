/**
 * Admin Dashboard Component
 * 
 * Dashboard for administrators to:
 * - View total number of users
 * - See online camera count
 * - Add or remove users
 * - Monitor system statistics
 */

import { useState, useEffect } from 'react';
import { Users, Video, UserPlus, UserMinus, Activity, Shield } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import Navbar from '@/components/Navbar';
import Footer from '@/components/Footer';
import { LIVE_CAMERA_ENDPOINTS, SYSTEM_ENDPOINTS } from '@/config/api';
import { useToast } from '@/hooks/use-toast';

const AdminDashboard = () => {
  const [totalUsers, setTotalUsers] = useState(0);
  const [onlineCameras, setOnlineCameras] = useState(0);
  const [newUserEmail, setNewUserEmail] = useState('');
  const [removeUserEmail, setRemoveUserEmail] = useState('');
  const { toast } = useToast();

  // Fetch statistics on component mount
  useEffect(() => {
    fetchStatistics();
  }, []);

  const fetchStatistics = async () => {
    try {
      // Fetch camera statistics
      const cameraResponse = await fetch(LIVE_CAMERA_ENDPOINTS.STATISTICS);
      if (cameraResponse.ok) {
        const cameraData = await cameraResponse.json();
        setOnlineCameras(cameraData.online_cameras || 0);
      }

      // Simulate fetching user count (replace with actual API)
      setTotalUsers(42); // Placeholder
    } catch (error) {
      console.error('Error fetching statistics:', error);
    }
  };

  // Handle adding a user
  const handleAddUser = () => {
    if (!newUserEmail) {
      toast({
        title: 'Invalid Email',
        description: 'Please enter a valid email address',
        variant: 'destructive',
      });
      return;
    }

    // Simulate adding user (replace with actual API call)
    toast({
      title: 'User Added',
      description: `${newUserEmail} has been added to the system`,
    });
    setNewUserEmail('');
    setTotalUsers((prev) => prev + 1);
  };

  // Handle removing a user
  const handleRemoveUser = () => {
    if (!removeUserEmail) {
      toast({
        title: 'Invalid Email',
        description: 'Please enter a valid email address',
        variant: 'destructive',
      });
      return;
    }

    // Simulate removing user (replace with actual API call)
    toast({
      title: 'User Removed',
      description: `${removeUserEmail} has been removed from the system`,
    });
    setRemoveUserEmail('');
    setTotalUsers((prev) => Math.max(0, prev - 1));
  };

  // Statistics cards data
  const statsCards = [
    {
      icon: Users,
      title: 'Total Users',
      value: totalUsers,
      color: 'text-primary',
      bgColor: 'bg-primary/10',
    },
    {
      icon: Video,
      title: 'Cameras Online',
      value: onlineCameras,
      color: 'text-accent',
      bgColor: 'bg-accent/10',
    },
    {
      icon: Activity,
      title: 'Active Sessions',
      value: '12',
      color: 'text-green-500',
      bgColor: 'bg-green-500/10',
    },
    {
      icon: Shield,
      title: 'Security Alerts',
      value: '3',
      color: 'text-destructive',
      bgColor: 'bg-destructive/10',
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-hero">
      <Navbar />

      {/* Dashboard Header */}
      <section className="container mx-auto px-4 pt-20 pb-12">
        <div className="max-w-6xl mx-auto">
          <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
            Admin Dashboard
          </h1>
          <p className="text-muted-foreground text-lg">Monitor and manage the Eyeora platform</p>
        </div>
      </section>

      {/* Statistics Cards */}
      <section className="container mx-auto px-4 pb-16">
        <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {statsCards.map((stat, index) => (
            <Card key={index} className="p-6 hover:shadow-elegant transition-all duration-300">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground mb-1">{stat.title}</p>
                  <p className="text-3xl font-bold">{stat.value}</p>
                </div>
                <div className={`w-12 h-12 rounded-lg ${stat.bgColor} flex items-center justify-center`}>
                  <stat.icon className={`w-6 h-6 ${stat.color}`} />
                </div>
              </div>
            </Card>
          ))}
        </div>
      </section>

      {/* User Management Section */}
      <section className="container mx-auto px-4 pb-16">
        <div className="max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Add User Card */}
          <Card className="p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-gradient-primary rounded-lg flex items-center justify-center">
                <UserPlus className="w-5 h-5 text-primary-foreground" />
              </div>
              <h2 className="text-xl font-bold">Add User</h2>
            </div>
            <div className="space-y-4">
              <div>
                <Label htmlFor="add-user-email">User Email</Label>
                <Input
                  id="add-user-email"
                  type="email"
                  placeholder="user@example.com"
                  value={newUserEmail}
                  onChange={(e) => setNewUserEmail(e.target.value)}
                  className="mt-2"
                />
              </div>
              <Button onClick={handleAddUser} className="w-full bg-gradient-primary hover:opacity-90">
                Add User
              </Button>
            </div>
          </Card>

          {/* Remove User Card */}
          <Card className="p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-destructive/20 rounded-lg flex items-center justify-center">
                <UserMinus className="w-5 h-5 text-destructive" />
              </div>
              <h2 className="text-xl font-bold">Remove User</h2>
            </div>
            <div className="space-y-4">
              <div>
                <Label htmlFor="remove-user-email">User Email</Label>
                <Input
                  id="remove-user-email"
                  type="email"
                  placeholder="user@example.com"
                  value={removeUserEmail}
                  onChange={(e) => setRemoveUserEmail(e.target.value)}
                  className="mt-2"
                />
              </div>
              <Button
                onClick={handleRemoveUser}
                variant="destructive"
                className="w-full"
              >
                Remove User
              </Button>
            </div>
          </Card>
        </div>
      </section>

      {/* System Status Section */}
      <section className="container mx-auto px-4 pb-16">
        <div className="max-w-4xl mx-auto">
          <Card className="p-8">
            <h2 className="text-2xl font-bold mb-6">System Status</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex items-center justify-between p-4 bg-secondary/50 rounded-lg">
                <span className="font-medium">API Status</span>
                <span className="text-green-500 font-semibold">Operational</span>
              </div>
              <div className="flex items-center justify-between p-4 bg-secondary/50 rounded-lg">
                <span className="font-medium">Database</span>
                <span className="text-green-500 font-semibold">Connected</span>
              </div>
              <div className="flex items-center justify-between p-4 bg-secondary/50 rounded-lg">
                <span className="font-medium">Storage</span>
                <span className="text-green-500 font-semibold">Available</span>
              </div>
              <div className="flex items-center justify-between p-4 bg-secondary/50 rounded-lg">
                <span className="font-medium">AI Models</span>
                <span className="text-green-500 font-semibold">Loaded</span>
              </div>
            </div>
          </Card>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default AdminDashboard;
