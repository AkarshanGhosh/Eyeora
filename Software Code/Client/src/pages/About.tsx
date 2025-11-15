/**
 * About Us Page Component
 * 
 * Detailed information about the Eyero project, vision, and technology
 */

import { Target, Users, Zap, Globe } from 'lucide-react';
import Navbar from '@/components/Navbar';
import Footer from '@/components/Footer';

const About = () => {
  // Core values/mission points
  const missionPoints = [
    {
      icon: Target,
      title: 'Our Mission',
      description:
        'To revolutionize surveillance technology by making AI-powered monitoring accessible to businesses of all sizes.',
    },
    {
      icon: Users,
      title: 'Who We Serve',
      description:
        'Retail shops, hospitals, security firms, and enterprises seeking intelligent monitoring solutions.',
    },
    {
      icon: Zap,
      title: 'Our Technology',
      description:
        'Built on YOLO (You Only Look Once) for real-time object detection and advanced computer vision models.',
    },
    {
      icon: Globe,
      title: 'Global Access',
      description:
        'Access your camera feeds and analytics from anywhere in the world with secure cloud connectivity.',
    },
  ];

  // Use cases
  const useCases = [
    {
      title: 'Retail Analytics',
      points: [
        'Count customers entering your shop',
        'Track purchase vs. window shopping behavior',
        'Analyze peak hours and customer flow patterns',
        'Monitor product engagement and interest zones',
      ],
    },
    {
      title: 'Security Monitoring',
      points: [
        'Real-time robbery and theft detection',
        'Fire and emergency alert systems',
        'Unauthorized access detection',
        'Suspicious activity identification',
      ],
    },
    {
      title: 'Healthcare Solutions',
      points: [
        'Monitor ward occupancy status',
        'Detect patient falls instantly',
        'Track staff movement and response times',
        'Ensure patient safety and compliance',
      ],
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-hero">
      <Navbar />

      {/* Hero Section */}
      <section className="container mx-auto px-4 pt-20 pb-16">
        <div className="max-w-4xl mx-auto text-center animate-fade-in">
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-6 bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
            About Eyero
          </h1>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
            Transforming traditional CCTV into intelligent monitoring systems with the power of artificial intelligence
          </p>
        </div>
      </section>

      {/* Project Overview */}
      <section className="container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto">
          <div className="bg-card rounded-2xl p-8 md:p-12 border border-border shadow-elegant">
            <h2 className="text-3xl font-bold mb-6">Our Vision</h2>
            <p className="text-muted-foreground text-lg leading-relaxed mb-6">
              Eyero is an AI-powered CCTV platform designed to bring intelligence to surveillance systems. We've built
              a solution capable of real-time object detection, activity recognition, and comprehensive analytics for
              retail shops, hospitals, and security-sensitive areas.
            </p>
            <p className="text-muted-foreground text-lg leading-relaxed mb-6">
              Our system uses camera-specific unique identifiers (UIDs) for secure access and streams live video feeds
              to a web-based SaaS platform. Advanced computer vision models, specifically YOLO (You Only Look Once),
              are integrated to detect human activities, monitor customer behavior, and identify anomalies such as
              patient falls or unauthorized intrusions.
            </p>
            <p className="text-muted-foreground text-lg leading-relaxed">
              The platform provides shop owners, healthcare institutions, and enterprises with real-time insights
              accessible remotely from anywhere in the world. Our goal is to make advanced AI surveillance affordable,
              accessible, and actionable for businesses of all sizes.
            </p>
          </div>
        </div>
      </section>

      {/* Mission & Values */}
      <section className="container mx-auto px-4 py-16">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {missionPoints.map((point, index) => (
            <div
              key={index}
              className="bg-card rounded-xl p-6 border border-border hover:border-primary/50 hover:shadow-elegant transition-all duration-300 animate-fade-in-up"
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              <div className="w-12 h-12 bg-gradient-primary rounded-lg flex items-center justify-center mb-4">
                <point.icon className="w-6 h-6 text-primary-foreground" />
              </div>
              <h3 className="text-xl font-semibold mb-2">{point.title}</h3>
              <p className="text-muted-foreground text-sm">{point.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Use Cases Section */}
      <section id="use-cases" className="container mx-auto px-4 py-16">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">Real-World Applications</h2>
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
            See how Eyero is transforming industries with intelligent monitoring
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {useCases.map((useCase, index) => (
            <div
              key={index}
              className="bg-card rounded-xl p-8 border border-border hover:shadow-elegant transition-all duration-300"
            >
              <h3 className="text-2xl font-bold mb-4 text-primary">{useCase.title}</h3>
              <ul className="space-y-3">
                {useCase.points.map((point, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-primary mt-2 flex-shrink-0" />
                    <span className="text-muted-foreground">{point}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </section>

      {/* Technology Stack */}
      <section className="container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto">
          <div className="bg-card rounded-2xl p-8 md:p-12 border border-border shadow-elegant">
            <h2 className="text-3xl font-bold mb-6">How It Works</h2>
            <div className="space-y-6">
              <div>
                <h3 className="text-xl font-semibold mb-2 text-primary">1. Camera Recording</h3>
                <p className="text-muted-foreground">
                  ESP32-CAM or standard CCTV cameras record live feeds and transmit data to our backend via secure APIs
                  using unique camera identifiers.
                </p>
              </div>
              <div>
                <h3 className="text-xl font-semibold mb-2 text-primary">2. AI Processing</h3>
                <p className="text-muted-foreground">
                  Our Python-based backend runs trained YOLO models to detect objects, recognize activities, and
                  identify anomalies in real-time.
                </p>
              </div>
              <div>
                <h3 className="text-xl font-semibold mb-2 text-primary">3. Real-Time Display</h3>
                <p className="text-muted-foreground">
                  The frontend displays live feeds, object detection overlays, and analytics. Users receive instant
                  alerts for security concerns.
                </p>
              </div>
              <div>
                <h3 className="text-xl font-semibold mb-2 text-primary">4. Data Export</h3>
                <p className="text-muted-foreground">
                  Daily analytics are compiled into CSV/XML files for record-keeping, compliance, and business
                  intelligence purposes.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default About;
