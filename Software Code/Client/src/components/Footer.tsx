/**
 * Footer Component
 * 
 * Modern, stylish footer with social links and copyright information
 * Links to LinkedIn, GitHub, and Email for Akarshan Ghosh & Eyeora
 */

import { Mail, Linkedin, Github } from 'lucide-react';

const Footer = () => {
  // Social media links configuration
  const socialLinks = [
    {
      name: 'LinkedIn',
      icon: Linkedin,
      url: 'https://linkedin.com/in/akarshan-ghosh/',
      color: 'hover:text-[#0077B5]',
    },
    {
      name: 'GitHub',
      icon: Github,
      url: 'https://github.com/AkarshanGhosh',
      color: 'hover:text-foreground',
    },
    {
      name: 'Email',
      icon: Mail,
      url: 'mailto:akarshanghosh28@gmail.com',
      color: 'hover:text-accent',
    },
  ];

  // Quick links sections
  const quickLinks = [
    {
      title: 'Product',
      links: [
        { name: 'Features', path: '/products' },
        { name: 'Pricing', path: '/products#pricing' },
        { name: 'Use Cases', path: '/about#use-cases' },
      ],
    },
    {
      title: 'Company',
      links: [
        { name: 'About Us', path: '/about' },
        { name: 'Contact', path: '/contact' },
        { name: 'Careers', path: '/contact' },
      ],
    },
    {
      title: 'Support',
      links: [
        { name: 'Documentation', path: '/products' },
        { name: 'Help Center', path: '/contact' },
        { name: 'Status', path: '/' },
      ],
    },
  ];

  return (
    <footer className="bg-card border-t border-border">
      <div className="container mx-auto px-4 py-12">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-8 mb-8">
          {/* Brand Section */}
          <div className="lg:col-span-2">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-10 h-10 bg-gradient-primary rounded-lg flex items-center justify-center shadow-glow">
                {/* Enter your favicon here */}
                <span className="text-xl font-bold text-primary-foreground">E</span>
              </div>
              <span className="text-xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
                Eyeora
              </span>
            </div>
            <p className="text-muted-foreground text-sm mb-4 max-w-sm">
              AI-powered CCTV platform for real-time object detection, activity recognition, and analytics.
              Empowering security and insights worldwide.
            </p>
            {/* Social Links */}
            <div className="flex gap-3">
              {socialLinks.map((social) => (
                <a
                  key={social.name}
                  href={social.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={`w-10 h-10 rounded-lg bg-secondary/50 hover:bg-secondary flex items-center justify-center transition-all duration-300 ${social.color}`}
                  aria-label={social.name}
                >
                  <social.icon className="w-5 h-5" />
                </a>
              ))}
            </div>
          </div>

          {/* Quick Links Sections */}
          {quickLinks.map((section) => (
            <div key={section.title}>
              <h3 className="font-semibold text-foreground mb-4">{section.title}</h3>
              <ul className="space-y-2">
                {section.links.map((link) => (
                  <li key={link.name}>
                    <a
                      href={link.path}
                      className="text-sm text-muted-foreground hover:text-primary transition-colors duration-200"
                    >
                      {link.name}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom Section */}
        <div className="pt-8 border-t border-border">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            {/* Copyright */}
            <p className="text-sm text-muted-foreground text-center md:text-left">
              © {new Date().getFullYear()} Eyeora. Created by{' '}
              <a
                href="https://linkedin.com/in/akarshan-ghosh/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary hover:text-accent transition-colors duration-200 font-medium"
              >
                Akarshan Ghosh
              </a>
              . All rights reserved.
            </p>

            {/* Legal Links */}
            <div className="flex gap-6">
              <a
                href="/privacy"
                className="text-sm text-muted-foreground hover:text-primary transition-colors duration-200"
              >
                Privacy Policy
              </a>
              <a
                href="/terms"
                className="text-sm text-muted-foreground hover:text-primary transition-colors duration-200"
              >
                Terms of Service
              </a>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
