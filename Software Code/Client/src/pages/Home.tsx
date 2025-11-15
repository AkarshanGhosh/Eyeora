/**
 * Home Page Component
 * 
 * Landing page for Eyero platform
 * Features hero section, key features, and call-to-action
 */

import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Video, Shield, Activity, Brain, Bell, BarChart3, ArrowRight } from 'lucide-react';
import Navbar from '@/components/Navbar';
import Footer from '@/components/Footer';

const Home = () => {
  // Key features of the platform
  const features = [
    {
      icon: Brain,
      title: 'AI-Powered Detection',
      description: 'Advanced YOLO-based object detection for real-time activity recognition and anomaly detection.',
    },
    {
      icon: Video,
      title: 'Live Streaming',
      description: 'Stream live video feeds from anywhere in the world with secure camera-specific UIDs.',
    },
    {
      icon: Activity,
      title: 'Behavior Analytics',
      description: 'Track customer behavior, foot traffic, and engagement patterns in retail environments.',
    },
    {
      icon: Shield,
      title: 'Security Monitoring',
      description: 'Instant alerts for security concerns like robbery, unauthorized access, and emergencies.',
    },
    {
      icon: Bell,
      title: 'Real-Time Alerts',
      description: 'Get instant notifications for critical events like falls, intrusions, or fire emergencies.',
    },
    {
      icon: BarChart3,
      title: 'Comprehensive Reports',
      description: 'Daily CSV/XML reports with detailed analytics and insights for informed decision-making.',
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-hero">
      <Navbar />

      {/* Hero Section */}
      <section className="container mx-auto px-4 pt-20 pb-32">
        <div className="max-w-4xl mx-auto text-center animate-fade-in">
          <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold mb-6 bg-gradient-to-r from-primary via-accent to-primary bg-clip-text text-transparent leading-tight">
            Next-Gen AI CCTV Platform
          </h1>
          <p className="text-xl md:text-2xl text-muted-foreground mb-8 max-w-2xl mx-auto">
            Transform your security cameras into intelligent systems with real-time object detection, activity
            recognition, and powerful analytics.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Link to="/signup">
              <Button size="lg" className="bg-gradient-primary hover:opacity-90 shadow-glow text-lg px-8 h-12">
                Get Started Free
                <ArrowRight className="ml-2 w-5 h-5" />
              </Button>
            </Link>
            <Link to="/products">
              <Button size="lg" variant="outline" className="text-lg px-8 h-12 border-2">
                View Products
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="container mx-auto px-4 py-20">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">Powerful Features</h2>
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
            Everything you need to turn your CCTV cameras into intelligent monitoring systems
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <div
              key={index}
              className="bg-card rounded-xl p-6 border border-border hover:border-primary/50 hover:shadow-elegant transition-all duration-300 group animate-fade-in-up"
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              <div className="w-12 h-12 bg-gradient-primary rounded-lg flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300">
                <feature.icon className="w-6 h-6 text-primary-foreground" />
              </div>
              <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
              <p className="text-muted-foreground">{feature.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA Section */}
      <section className="container mx-auto px-4 py-20">
        <div className="bg-gradient-primary rounded-2xl p-12 text-center shadow-glow">
          <h2 className="text-3xl md:text-4xl font-bold text-primary-foreground mb-4">
            Ready to Transform Your Security?
          </h2>
          <p className="text-primary-foreground/90 text-lg mb-8 max-w-2xl mx-auto">
            Join hundreds of businesses using Eyero to enhance their security and gain valuable insights.
          </p>
          <Link to="/signup">
            <Button
              size="lg"
              variant="secondary"
              className="bg-background text-foreground hover:bg-background/90 text-lg px-8 h-12"
            >
              Start Your Free Trial
            </Button>
          </Link>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default Home;
