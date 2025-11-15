/**
 * Products Page Component
 * 
 * Displays Eyero product offerings, features, and pricing
 */

import { Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Link } from 'react-router-dom';
import Navbar from '@/components/Navbar';
import Footer from '@/components/Footer';

const Products = () => {
  // Pricing tiers
  const pricingPlans = [
    {
      name: 'Starter',
      price: '$29',
      period: '/month',
      description: 'Perfect for small retail shops and single locations',
      features: [
        'Up to 3 cameras',
        'Real-time object detection',
        'Basic analytics dashboard',
        'Daily CSV reports',
        'Email alerts',
        '720p video quality',
        'Community support',
      ],
      popular: false,
    },
    {
      name: 'Professional',
      price: '$79',
      period: '/month',
      description: 'Ideal for multi-location businesses and hospitals',
      features: [
        'Up to 15 cameras',
        'Advanced AI detection',
        'Comprehensive analytics',
        'Real-time & historical data',
        'SMS + Email alerts',
        '1080p video quality',
        'Priority support',
        'Custom reporting',
      ],
      popular: true,
    },
    {
      name: 'Enterprise',
      price: 'Custom',
      period: '',
      description: 'For large organizations with advanced needs',
      features: [
        'Unlimited cameras',
        'Custom AI model training',
        'White-label solution',
        'Dedicated infrastructure',
        'Multi-channel alerts',
        '4K video quality',
        '24/7 premium support',
        'API access',
        'On-premise deployment option',
      ],
      popular: false,
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-hero">
      <Navbar />

      {/* Hero Section */}
      <section className="container mx-auto px-4 pt-20 pb-16">
        <div className="max-w-4xl mx-auto text-center animate-fade-in">
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-6 bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
            Choose Your Plan
          </h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Flexible pricing for businesses of all sizes. Start free, upgrade as you grow.
          </p>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="container mx-auto px-4 py-16">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
          {pricingPlans.map((plan, index) => (
            <div
              key={index}
              className={`bg-card rounded-2xl p-8 border-2 transition-all duration-300 hover:shadow-elegant ${
                plan.popular
                  ? 'border-primary shadow-glow scale-105'
                  : 'border-border hover:border-primary/50'
              } animate-fade-in-up`}
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              {plan.popular && (
                <div className="bg-gradient-primary text-primary-foreground text-sm font-semibold px-3 py-1 rounded-full inline-block mb-4">
                  Most Popular
                </div>
              )}
              <h3 className="text-2xl font-bold mb-2">{plan.name}</h3>
              <div className="mb-4">
                <span className="text-4xl font-bold">{plan.price}</span>
                <span className="text-muted-foreground">{plan.period}</span>
              </div>
              <p className="text-muted-foreground mb-6">{plan.description}</p>

              <ul className="space-y-3 mb-8">
                {plan.features.map((feature, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <Check className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
                    <span className="text-sm">{feature}</span>
                  </li>
                ))}
              </ul>

              <Link to="/signup">
                <Button
                  className={`w-full ${
                    plan.popular
                      ? 'bg-gradient-primary hover:opacity-90 shadow-elegant'
                      : 'bg-secondary hover:bg-secondary/80'
                  }`}
                >
                  {plan.name === 'Enterprise' ? 'Contact Sales' : 'Get Started'}
                </Button>
              </Link>
            </div>
          ))}
        </div>
      </section>

      {/* Features Comparison */}
      <section className="container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">All Plans Include</h2>
            <p className="text-muted-foreground text-lg">Core features available in every subscription</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {[
              'Real-time video streaming',
              'Object detection & tracking',
              'Activity recognition',
              'Anomaly detection',
              'Cloud storage',
              'Mobile app access',
              'Secure camera UIDs',
              'Daily analytics reports',
            ].map((feature, index) => (
              <div key={index} className="flex items-center gap-3 bg-card p-4 rounded-lg border border-border">
                <Check className="w-5 h-5 text-primary flex-shrink-0" />
                <span>{feature}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default Products;
