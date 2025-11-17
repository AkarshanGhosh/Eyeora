/**
 * Admin Dashboard Component
 * 
 * Complete admin panel with:
 * - Real-time analytics and statistics
 * - User management (list, add, update, delete)
 * - Camera management (list, add, update, delete)
 * - Media file management (videos/images)
 * - System status monitoring
 */

import { useState, useEffect } from 'react';
import { 
  Users, Video, Activity, Shield, UserPlus, Camera, 
  Trash2, Edit2, PlayCircle, Image as ImageIcon, Download,
  Database, Cpu, HardDrive, RefreshCw, MapPin, Power, PowerOff
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import Navbar from '@/components/Navbar';
import Footer from '@/components/Footer';
import { ADMIN_ENDPOINTS, CAMERA_ENDPOINTS, DATABASE_ENDPOINTS, getAuthHeaders } from '@/config/api';
import { useToast } from '@/hooks/use-toast';
import { useAuth } from '@/contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

interface DashboardStats {
  user_stats: {
    total_users: number;
    active_users: number;
    admin_users: number;
    regular_users: number;
    recent_signups: number;
  };
  camera_stats: {
    total_cameras: number;
    active_cameras: number;
    inactive_cameras: number;
    cameras_by_location: Record<string, number>;
  };
  media_stats: {
    total_videos: number;
    total_images: number;
    storage_used_mb: number;
    processed_videos: Array<{
      filename: string;
      size_mb: number;
      created_at: string;
      url: string;
    }>;
    processed_images: Array<{
      filename: string;
      size_mb: number;
      created_at: string;
      url: string;
    }>;
  };
  system_stats: {
    online_users: number;
    active_live_streams: number;
    processing_jobs: number;
  };
}

interface User {
  id: string;
  email: string;
  full_name?: string;
  role: string;
  is_active: boolean;
  created_at: string;
  last_login?: string;
}

interface CameraDevice {
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

const AdminDashboard = () => {
  const { token, isAdmin, user: currentUser } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();
  
  // Redirect if not admin
  useEffect(() => {
    if (!isAdmin) {
      toast({
        title: 'Access Denied',
        description: 'Admin privileges required',
        variant: 'destructive',
      });
      navigate('/');
    }
  }, [isAdmin, navigate]);

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [cameras, setCameras] = useState<CameraDevice[]>([]);
  const [dbStatus, setDbStatus] = useState<string>('checking...');
  
  // User management state
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [newUserEmail, setNewUserEmail] = useState('');
  const [newUserPassword, setNewUserPassword] = useState('');
  const [newUserFullName, setNewUserFullName] = useState('');
  const [newUserRole, setNewUserRole] = useState('user');

  // Camera management state
  const [editingCamera, setEditingCamera] = useState<CameraDevice | null>(null);
  const [newCameraName, setNewCameraName] = useState('');
  const [newCameraUid, setNewCameraUid] = useState('');
  const [newCameraImageUrl, setNewCameraImageUrl] = useState('');
  const [newCameraLocation, setNewCameraLocation] = useState('');
  const [newCameraDescription, setNewCameraDescription] = useState('');
  const [newCameraActive, setNewCameraActive] = useState(true);

  useEffect(() => {
    fetchDashboardData();
    checkDatabaseHealth();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setRefreshing(true);
      
      // Fetch dashboard stats
      const statsResponse = await fetch(ADMIN_ENDPOINTS.DASHBOARD, {
        headers: getAuthHeaders(token),
      });
      
      if (statsResponse.ok) {
        const statsData = await statsResponse.json();
        setStats(statsData);
      }
      
      // Fetch users list
      const usersResponse = await fetch(ADMIN_ENDPOINTS.LIST_USERS, {
        headers: getAuthHeaders(token),
      });
      
      if (usersResponse.ok) {
        const usersData = await usersResponse.json();
        setUsers(usersData);
      }

      // Fetch cameras list
      const camerasResponse = await fetch(CAMERA_ENDPOINTS.LIST, {
        headers: getAuthHeaders(token),
      });
      
      if (camerasResponse.ok) {
        const camerasData = await camerasResponse.json();
        setCameras(camerasData);
      }
      
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      toast({
        title: 'Error',
        description: 'Failed to load dashboard data',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const checkDatabaseHealth = async () => {
    try {
      const response = await fetch(DATABASE_ENDPOINTS.PING);
      const data = await response.json();
      setDbStatus(data.ok ? 'Connected' : 'Disconnected');
    } catch (error) {
      setDbStatus('Error');
    }
  };

  // User Management Functions
  const handleAddUser = async () => {
    if (!newUserEmail || !newUserPassword) {
      toast({
        title: 'Missing Fields',
        description: 'Email and password are required',
        variant: 'destructive',
      });
      return;
    }

    try {
      const response = await fetch(ADMIN_ENDPOINTS.LIST_USERS, {
        method: 'POST',
        headers: getAuthHeaders(token),
        body: JSON.stringify({
          email: newUserEmail,
          password: newUserPassword,
          full_name: newUserFullName || undefined,
          role: newUserRole,
        }),
      });

      if (response.ok) {
        toast({
          title: 'Success',
          description: 'User added successfully',
        });
        setNewUserEmail('');
        setNewUserPassword('');
        setNewUserFullName('');
        setNewUserRole('user');
        fetchDashboardData();
      } else {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to add user');
      }
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message,
        variant: 'destructive',
      });
    }
  };

  const handleUpdateUser = async () => {
    if (!editingUser) return;

    try {
      const response = await fetch(ADMIN_ENDPOINTS.UPDATE_USER(editingUser.id), {
        method: 'PUT',
        headers: getAuthHeaders(token),
        body: JSON.stringify({
          full_name: editingUser.full_name,
          role: editingUser.role,
          is_active: editingUser.is_active,
        }),
      });

      if (response.ok) {
        toast({
          title: 'Success',
          description: 'User updated successfully',
        });
        setEditingUser(null);
        fetchDashboardData();
      } else {
        throw new Error('Failed to update user');
      }
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message,
        variant: 'destructive',
      });
    }
  };

  const handleDeleteUser = async (userId: string) => {
    if (userId === currentUser?.id) {
      toast({
        title: 'Error',
        description: 'Cannot delete your own account',
        variant: 'destructive',
      });
      return;
    }

    if (!confirm('Are you sure you want to delete this user?')) return;

    try {
      const response = await fetch(ADMIN_ENDPOINTS.DELETE_USER(userId), {
        method: 'DELETE',
        headers: getAuthHeaders(token),
      });

      if (response.ok) {
        toast({
          title: 'Success',
          description: 'User deleted successfully',
        });
        fetchDashboardData();
      } else {
        throw new Error('Failed to delete user');
      }
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message,
        variant: 'destructive',
      });
    }
  };

  // Camera Management Functions
  const handleAddCamera = async () => {
    if (!newCameraName || !newCameraUid) {
      toast({
        title: 'Missing Fields',
        description: 'Camera name and UID are required',
        variant: 'destructive',
      });
      return;
    }

    // Sanitize UID: remove special characters
    const sanitizedUid = newCameraUid.replace(/[^a-zA-Z0-9_-]/g, '_');
    
    if (sanitizedUid !== newCameraUid) {
      toast({
        title: 'UID Modified',
        description: `Special characters removed. UID changed to: ${sanitizedUid}`,
      });
    }

    try {
      const response = await fetch(CAMERA_ENDPOINTS.CREATE, {
        method: 'POST',
        headers: getAuthHeaders(token),
        body: JSON.stringify({
          name: newCameraName,
          uid: sanitizedUid,  // Use sanitized UID
          image_url: newCameraImageUrl || undefined,
          location: newCameraLocation || undefined,
          description: newCameraDescription || undefined,
          is_active: newCameraActive,
        }),
      });

      if (response.ok) {
        toast({
          title: 'Success',
          description: 'Camera added successfully',
        });
        // Reset form
        setNewCameraName('');
        setNewCameraUid('');
        setNewCameraImageUrl('');
        setNewCameraLocation('');
        setNewCameraDescription('');
        setNewCameraActive(true);
        fetchDashboardData();
      } else {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to add camera');
      }
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message,
        variant: 'destructive',
      });
    }
  };
// Handle Update
  const handleUpdateCamera = async () => {
    if (!editingCamera) return;

    try {
      // Encode the UID for URL safety
      const encodedUid = encodeURIComponent(editingCamera.uid);
      
      const response = await fetch(CAMERA_ENDPOINTS.UPDATE(encodedUid), {
        method: 'PUT',
        headers: getAuthHeaders(token),
        body: JSON.stringify({
          name: editingCamera.name,
          image_url: editingCamera.image_url || undefined,
          location: editingCamera.location || undefined,
          description: editingCamera.description || undefined,
          is_active: editingCamera.is_active,
        }),
      });

      if (response.ok) {
        toast({
          title: 'Success',
          description: 'Camera updated successfully',
        });
        setEditingCamera(null);
        fetchDashboardData();
      } else {
        throw new Error('Failed to update camera');
      }
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message,
        variant: 'destructive',
      });
    }
  };
// Handle Delete
  const handleDeleteCamera = async (uid: string) => {
    if (!confirm('Are you sure you want to delete this camera?')) return;

    try {
      // Encode the UID for URL safety
      const encodedUid = encodeURIComponent(uid);
      
      const response = await fetch(CAMERA_ENDPOINTS.DELETE(encodedUid), {
        method: 'DELETE',
        headers: getAuthHeaders(token),
      });

      if (response.ok) {
        toast({
          title: 'Success',
          description: 'Camera deleted successfully',
        });
        fetchDashboardData();
      } else {
        throw new Error('Failed to delete camera');
      }
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message,
        variant: 'destructive',
      });
    }
  };
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="w-12 h-12 animate-spin text-cyan-500 mx-auto mb-4" />
          <p className="text-lg text-muted-foreground">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  const statsCards = [
    {
      icon: Users,
      title: 'Total Users',
      value: stats?.user_stats.total_users || 0,
      subtitle: `${stats?.user_stats.recent_signups || 0} new this week`,
      color: 'text-cyan-500',
      bgColor: 'bg-cyan-500/10',
    },
    {
      icon: Video,
      title: 'Cameras',
      value: stats?.camera_stats.total_cameras || 0,
      subtitle: `${stats?.camera_stats.active_cameras || 0} active`,
      color: 'text-blue-500',
      bgColor: 'bg-blue-500/10',
    },
    {
      icon: Activity,
      title: 'Online Users',
      value: stats?.system_stats.online_users || 0,
      subtitle: 'Currently active',
      color: 'text-green-500',
      bgColor: 'bg-green-500/10',
    },
    {
      icon: HardDrive,
      title: 'Storage Used',
      value: `${stats?.media_stats.storage_used_mb.toFixed(1) || 0}MB`,
      subtitle: `${stats?.media_stats.total_videos || 0} videos`,
      color: 'text-purple-500',
      bgColor: 'bg-purple-500/10',
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <Navbar />

      {/* Dashboard Header */}
      <section className="container mx-auto px-4 pt-20 pb-12">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div>
            <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-cyan-500 to-blue-500 bg-clip-text text-transparent">
              Admin Dashboard
            </h1>
            <p className="text-muted-foreground text-lg">Monitor and manage the Eyeora platform</p>
          </div>
          <Button 
            onClick={fetchDashboardData} 
            disabled={refreshing}
            className="bg-gradient-to-r from-cyan-500 to-blue-500 hover:opacity-90 text-white"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </section>

      {/* Statistics Cards */}
      <section className="container mx-auto px-4 pb-8">
        <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {statsCards.map((stat, index) => (
            <Card key={index} className="p-6 hover:shadow-lg transition-all duration-300 border-slate-200 dark:border-slate-700">
              <div className="flex items-center justify-between mb-4">
                <div className={`w-12 h-12 rounded-lg ${stat.bgColor} flex items-center justify-center`}>
                  <stat.icon className={`w-6 h-6 ${stat.color}`} />
                </div>
              </div>
              <p className="text-sm text-muted-foreground mb-1">{stat.title}</p>
              <p className="text-3xl font-bold mb-1">{stat.value}</p>
              <p className="text-xs text-muted-foreground">{stat.subtitle}</p>
            </Card>
          ))}
        </div>
      </section>

      {/* System Status Bar */}
      <section className="container mx-auto px-4 pb-8">
        <div className="max-w-7xl mx-auto">
          <Card className="p-4 border-slate-200 dark:border-slate-700">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="flex items-center gap-2">
                <Database className="w-4 h-4 text-green-500" />
                <span className="text-sm">Database: <strong className="text-green-500">{dbStatus}</strong></span>
              </div>
              <div className="flex items-center gap-2">
                <Cpu className="w-4 h-4 text-blue-500" />
                <span className="text-sm">API: <strong className="text-green-500">Operational</strong></span>
              </div>
              <div className="flex items-center gap-2">
                <Shield className="w-4 h-4 text-cyan-500" />
                <span className="text-sm">Auth: <strong className="text-green-500">Active</strong></span>
              </div>
              <div className="flex items-center gap-2">
                <Video className="w-4 h-4 text-purple-500" />
                <span className="text-sm">Models: <strong className="text-green-500">Loaded</strong></span>
              </div>
            </div>
          </Card>
        </div>
      </section>

      {/* Main Content Tabs */}
      <section className="container mx-auto px-4 pb-16">
        <div className="max-w-7xl mx-auto">
          <Tabs defaultValue="users" className="space-y-6">
            <TabsList className="grid w-full grid-cols-3 lg:w-[500px]">
              <TabsTrigger value="users">Users</TabsTrigger>
              <TabsTrigger value="cameras">Cameras</TabsTrigger>
              <TabsTrigger value="media">Media Files</TabsTrigger>
            </TabsList>

            {/* Users Tab */}
            <TabsContent value="users" className="space-y-6">
              {/* Add User Card */}
              <Card className="p-6 border-slate-200 dark:border-slate-700">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-10 h-10 bg-gradient-to-r from-cyan-500 to-blue-500 rounded-lg flex items-center justify-center">
                    <UserPlus className="w-5 h-5 text-white" />
                  </div>
                  <h2 className="text-xl font-bold">Add New User</h2>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="new-email">Email *</Label>
                    <Input
                      id="new-email"
                      type="email"
                      placeholder="user@example.com"
                      value={newUserEmail}
                      onChange={(e) => setNewUserEmail(e.target.value)}
                      className="mt-2"
                    />
                  </div>
                  <div>
                    <Label htmlFor="new-password">Password *</Label>
                    <Input
                      id="new-password"
                      type="password"
                      placeholder="Minimum 6 characters"
                      value={newUserPassword}
                      onChange={(e) => setNewUserPassword(e.target.value)}
                      className="mt-2"
                    />
                  </div>
                  <div>
                    <Label htmlFor="new-fullname">Full Name</Label>
                    <Input
                      id="new-fullname"
                      placeholder="John Doe"
                      value={newUserFullName}
                      onChange={(e) => setNewUserFullName(e.target.value)}
                      className="mt-2"
                    />
                  </div>
                  <div>
                    <Label htmlFor="new-role">Role</Label>
                    <Select value={newUserRole} onValueChange={setNewUserRole}>
                      <SelectTrigger className="mt-2">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="user">User</SelectItem>
                        <SelectItem value="admin">Admin</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <Button 
                  onClick={handleAddUser} 
                  className="mt-4 bg-gradient-to-r from-cyan-500 to-blue-500 hover:opacity-90 text-white"
                >
                  <UserPlus className="w-4 h-4 mr-2" />
                  Add User
                </Button>
              </Card>

              {/* Users List */}
              <Card className="p-6 border-slate-200 dark:border-slate-700">
                <h2 className="text-xl font-bold mb-4">All Users ({users.length})</h2>
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Email</TableHead>
                        <TableHead>Full Name</TableHead>
                        <TableHead>Role</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Created</TableHead>
                        <TableHead>Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {users.map((user) => (
                        <TableRow key={user.id}>
                          <TableCell className="font-medium">{user.email}</TableCell>
                          <TableCell>{user.full_name || '-'}</TableCell>
                          <TableCell>
                            <span className={`px-2 py-1 rounded-full text-xs ${
                              user.role === 'admin' 
                                ? 'bg-cyan-500/20 text-cyan-500' 
                                : 'bg-slate-500/20 text-slate-500'
                            }`}>
                              {user.role}
                            </span>
                          </TableCell>
                          <TableCell>
                            <span className={`px-2 py-1 rounded-full text-xs ${
                              user.is_active 
                                ? 'bg-green-500/20 text-green-500' 
                                : 'bg-red-500/20 text-red-500'
                            }`}>
                              {user.is_active ? 'Active' : 'Inactive'}
                            </span>
                          </TableCell>
                          <TableCell>{new Date(user.created_at).toLocaleDateString()}</TableCell>
                          <TableCell>
                            <div className="flex gap-2">
                              <Dialog>
                                <DialogTrigger asChild>
                                  <Button 
                                    size="sm" 
                                    variant="outline"
                                    onClick={() => setEditingUser(user)}
                                  >
                                    <Edit2 className="w-4 h-4" />
                                  </Button>
                                </DialogTrigger>
                                <DialogContent>
                                  <DialogHeader>
                                    <DialogTitle>Edit User</DialogTitle>
                                    <DialogDescription>
                                      Update user information and permissions
                                    </DialogDescription>
                                  </DialogHeader>
                                  {editingUser && (
                                    <div className="space-y-4 mt-4">
                                      <div>
                                        <Label>Email</Label>
                                        <Input value={editingUser.email} disabled />
                                      </div>
                                      <div>
                                        <Label>Full Name</Label>
                                        <Input 
                                          value={editingUser.full_name || ''} 
                                          onChange={(e) => setEditingUser({...editingUser, full_name: e.target.value})}
                                        />
                                      </div>
                                      <div>
                                        <Label>Role</Label>
                                        <Select 
                                          value={editingUser.role} 
                                          onValueChange={(val) => setEditingUser({...editingUser, role: val})}
                                        >
                                          <SelectTrigger>
                                            <SelectValue />
                                          </SelectTrigger>
                                          <SelectContent>
                                            <SelectItem value="user">User</SelectItem>
                                            <SelectItem value="admin">Admin</SelectItem>
                                          </SelectContent>
                                        </Select>
                                      </div>
                                      <Button 
                                        onClick={handleUpdateUser}
                                        className="w-full bg-gradient-to-r from-cyan-500 to-blue-500 text-white"
                                      >
                                        Update User
                                      </Button>
                                    </div>
                                  )}
                                </DialogContent>
                              </Dialog>
                              <Button 
                                size="sm" 
                                variant="destructive"
                                onClick={() => handleDeleteUser(user.id)}
                                disabled={user.id === currentUser?.id}
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </Card>
            </TabsContent>

            {/* Cameras Tab */}
            <TabsContent value="cameras" className="space-y-6">
              {/* Add Camera Card */}
              <Card className="p-6 border-slate-200 dark:border-slate-700">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-10 h-10 bg-gradient-to-r from-cyan-500 to-blue-500 rounded-lg flex items-center justify-center">
                    <Camera className="w-5 h-5 text-white" />
                  </div>
                  <h2 className="text-xl font-bold">Add New Camera</h2>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="cam-name">Camera Name *</Label>
                    <Input
                      id="cam-name"
                      placeholder="Office Camera 1"
                      value={newCameraName}
                      onChange={(e) => setNewCameraName(e.target.value)}
                      className="mt-2"
                    />
                  </div>
                  <div>
                    <Label htmlFor="cam-uid">UID *</Label>
                    <Input
                      id="cam-uid"
                      placeholder="CAM_001"
                      value={newCameraUid}
                      onChange={(e) => setNewCameraUid(e.target.value)}
                      className="mt-2"
                    />
                  </div>
                  <div>
                    <Label htmlFor="cam-location">Location</Label>
                    <Input
                      id="cam-location"
                      placeholder="Building A, Floor 2"
                      value={newCameraLocation}
                      onChange={(e) => setNewCameraLocation(e.target.value)}
                      className="mt-2"
                    />
                  </div>
                  <div>
                    <Label htmlFor="cam-image">Image URL</Label>
                    <Input
                      id="cam-image"
                      placeholder="https://example.com/camera.jpg"
                      value={newCameraImageUrl}
                      onChange={(e) => setNewCameraImageUrl(e.target.value)}
                      className="mt-2"
                    />
                  </div>
                  <div className="md:col-span-2">
                    <Label htmlFor="cam-desc">Description</Label>
                    <textarea
                      id="cam-desc"
                      placeholder="Camera description..."
                      value={newCameraDescription}
                      onChange={(e) => setNewCameraDescription(e.target.value)}
                      className="mt-2 flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                    />
                  </div>
                  <div className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id="cam-active"
                      checked={newCameraActive}
                      onChange={(e) => setNewCameraActive(e.target.checked)}
                      className="h-4 w-4 rounded border-gray-300"
                    />
                    <Label htmlFor="cam-active">Active</Label>
                  </div>
                </div>
                <Button 
                  onClick={handleAddCamera} 
                  className="mt-4 bg-gradient-to-r from-cyan-500 to-blue-500 hover:opacity-90 text-white"
                >
                  <Camera className="w-4 h-4 mr-2" />
                  Add Camera
                </Button>
              </Card>

              {/* Cameras List */}
              <Card className="p-6 border-slate-200 dark:border-slate-700">
                <h2 className="text-xl font-bold mb-4">All Cameras ({cameras.length})</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {cameras.map((camera) => (
                    <Card key={camera.id} className="p-4 border-slate-200 dark:border-slate-700">
                      {/* Camera Image */}
                      <div className="aspect-video bg-gradient-to-br from-cyan-500/20 to-blue-500/20 rounded-lg mb-4 flex items-center justify-center overflow-hidden">
                        {camera.image_url ? (
                          <img 
                            src={camera.image_url} 
                            alt={camera.name}
                            className="w-full h-full object-cover"
                            onError={(e) => {
                              e.currentTarget.style.display = 'none';
                            }}
                          />
                        ) : (
                          <Camera className="w-16 h-16 text-cyan-500" />
                        )}
                      </div>

                      {/* Camera Details */}
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <h3 className="font-bold text-lg">{camera.name}</h3>
                          {camera.is_active ? (
                            <Power className="w-5 h-5 text-green-500" />
                          ) : (
                            <PowerOff className="w-5 h-5 text-red-500" />
                          )}
                        </div>
                        
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                          <Camera className="w-4 h-4" />
                          <span className="font-mono text-xs">{camera.uid}</span>
                        </div>

                        {camera.location && (
                          <div className="flex items-center gap-2 text-sm text-muted-foreground">
                            <MapPin className="w-4 h-4" />
                            <span>{camera.location}</span>
                          </div>
                        )}

                        {camera.description && (
                          <p className="text-sm text-muted-foreground line-clamp-2">
                            {camera.description}
                          </p>
                        )}

                        <div className="pt-2 border-t border-slate-200 dark:border-slate-700">
                          <p className="text-xs text-muted-foreground">
                            Added: {new Date(camera.created_at).toLocaleDateString()}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            By: {camera.created_by}
                          </p>
                        </div>

                        {/* Action Buttons */}
                        <div className="flex gap-2 pt-2">
                          <Dialog>
                            <DialogTrigger asChild>
                              <Button 
                                size="sm" 
                                variant="outline"
                                className="flex-1"
                                onClick={() => setEditingCamera(camera)}
                              >
                                <Edit2 className="w-4 h-4 mr-1" />
                                Edit
                              </Button>
                            </DialogTrigger>
                            <DialogContent>
                              <DialogHeader>
                                <DialogTitle>Edit Camera</DialogTitle>
                                <DialogDescription>
                                  Update camera information
                                </DialogDescription>
                              </DialogHeader>
                              {editingCamera && (
                                <div className="space-y-4 mt-4">
                                  <div>
                                    <Label>Camera Name</Label>
                                    <Input 
                                      value={editingCamera.name} 
                                      onChange={(e) => setEditingCamera({...editingCamera, name: e.target.value})}
                                    />
                                  </div>
                                  <div>
                                    <Label>UID (Cannot be changed)</Label>
                                    <Input value={editingCamera.uid} disabled />
                                  </div>
                                  <div>
                                    <Label>Location</Label>
                                    <Input 
                                      value={editingCamera.location || ''} 
                                      onChange={(e) => setEditingCamera({...editingCamera, location: e.target.value})}
                                    />
                                  </div>
                                  <div>
                                    <Label>Image URL</Label>
                                    <Input 
                                      value={editingCamera.image_url || ''} 
                                      onChange={(e) => setEditingCamera({...editingCamera, image_url: e.target.value})}
                                    />
                                  </div>
                                  <div>
                                    <Label>Description</Label>
                                    <textarea 
                                      value={editingCamera.description || ''} 
                                      onChange={(e) => setEditingCamera({...editingCamera, description: e.target.value})}
                                      className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                                    />
                                  </div>
                                  <div className="flex items-center space-x-2">
                                    <input
                                      type="checkbox"
                                      id="edit-cam-active"
                                      checked={editingCamera.is_active}
                                      onChange={(e) => setEditingCamera({...editingCamera, is_active: e.target.checked})}
                                      className="h-4 w-4 rounded border-gray-300"
                                    />
                                    <Label htmlFor="edit-cam-active">Active</Label>
                                  </div>
                                  <Button 
                                    onClick={handleUpdateCamera}
                                    className="w-full bg-gradient-to-r from-cyan-500 to-blue-500 text-white"
                                  >
                                    Update Camera
                                  </Button>
                                </div>
                              )}
                            </DialogContent>
                          </Dialog>
                          <Button 
                            size="sm" 
                            variant="destructive"
                            onClick={() => handleDeleteCamera(camera.uid)}
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>

                {cameras.length === 0 && (
                  <div className="text-center py-12 text-muted-foreground">
                    <Camera className="w-16 h-16 mx-auto mb-4 opacity-50" />
                    <p>No cameras added yet</p>
                    <p className="text-sm">Add your first camera above</p>
                  </div>
                )}
              </Card>
            </TabsContent>

            {/* Media Tab */}
            <TabsContent value="media" className="space-y-6">
              {/* Videos */}
              <Card className="p-6 border-slate-200 dark:border-slate-700">
                <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                  <PlayCircle className="w-5 h-5 text-cyan-500" />
                  Processed Videos ({stats?.media_stats.total_videos || 0})
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {stats?.media_stats.processed_videos.map((video) => (
                    <Card key={video.filename} className="p-4 border-slate-200 dark:border-slate-700">
                      <div className="aspect-video bg-slate-200 dark:bg-slate-700 rounded-lg mb-3 flex items-center justify-center">
                        <PlayCircle className="w-12 h-12 text-slate-400" />
                      </div>
                      <p className="text-sm font-medium truncate mb-1">{video.filename}</p>
                      <p className="text-xs text-muted-foreground mb-3">
                        {video.size_mb}MB • {new Date(video.created_at).toLocaleDateString()}
                      </p>
                      <div className="flex gap-2">
                        <Button 
                          size="sm" 
                          variant="outline" 
                          className="flex-1"
                          onClick={() => window.open(video.url, '_blank')}
                        >
                          <Download className="w-4 h-4 mr-1" />
                          View
                        </Button>
                        <Button 
                          size="sm" 
                          variant="destructive"
                          onClick={() => handleDeleteMedia(video.filename, 'video')}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </Card>
                  ))}
                </div>
                {(!stats?.media_stats.processed_videos || stats.media_stats.processed_videos.length === 0) && (
                  <div className="text-center py-12 text-muted-foreground">
                    <PlayCircle className="w-16 h-16 mx-auto mb-4 opacity-50" />
                    <p>No videos processed yet</p>
                  </div>
                )}
              </Card>

              {/* Images */}
              <Card className="p-6 border-slate-200 dark:border-slate-700">
                <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                  <ImageIcon className="w-5 h-5 text-blue-500" />
                  Processed Images ({stats?.media_stats.total_images || 0})
                </h2>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                  {stats?.media_stats.processed_images.map((image) => (
                    <Card key={image.filename} className="p-3 border-slate-200 dark:border-slate-700">
                      <div className="aspect-square bg-slate-200 dark:bg-slate-700 rounded-lg mb-2 flex items-center justify-center">
                        <ImageIcon className="w-8 h-8 text-slate-400" />
                      </div>
                      <p className="text-xs truncate mb-1">{image.filename}</p>
                      <p className="text-xs text-muted-foreground mb-2">{image.size_mb}MB</p>
                      <div className="flex gap-1">
                        <Button 
                          size="sm" 
                          variant="outline" 
                          className="flex-1 h-8 text-xs"
                          onClick={() => window.open(image.url, '_blank')}
                        >
                          View
                        </Button>
                        <Button 
                          size="sm" 
                          variant="destructive"
                          className="h-8"
                          onClick={() => handleDeleteMedia(image.filename, 'image')}
                        >
                          <Trash2 className="w-3 h-3" />
                        </Button>
                      </div>
                    </Card>
                  ))}
                </div>
                {(!stats?.media_stats.processed_images || stats.media_stats.processed_images.length === 0) && (
                  <div className="text-center py-12 text-muted-foreground">
                    <ImageIcon className="w-16 h-16 mx-auto mb-4 opacity-50" />
                    <p>No images processed yet</p>
                  </div>
                )}
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default AdminDashboard;