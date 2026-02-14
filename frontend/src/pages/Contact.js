import React, { useState } from 'react';
import axios from 'axios';
import { Mail, User, MessageSquare, Send, CheckCircle } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Contact = () => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    message: ''
  });
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await axios.post(`${API}/contact`, formData);
      toast.success('Message sent successfully!');
      setSubmitted(true);
      setFormData({ name: '', email: '', message: '' });
      
      setTimeout(() => {
        setSubmitted(false);
      }, 5000);
    } catch (error) {
      console.error('Error sending message:', error);
      toast.error('Failed to send message. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen py-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-16">
          <h1 
            className="text-4xl sm:text-5xl font-bold mb-4"
            style={{ fontFamily: "'Chivo', sans-serif" }}
            data-testid="contact-title"
          >
            Get in Touch
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Have questions or feedback? We'd love to hear from you
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
          {/* Contact Form */}
          <div>
            <div className="rounded-xl border bg-card shadow-sm p-8">
              <h2 
                className="text-2xl font-bold mb-6"
                style={{ fontFamily: "'Chivo', sans-serif" }}
              >
                Send us a Message
              </h2>

              {submitted ? (
                <div className="text-center py-12" data-testid="success-message">
                  <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-emerald-500/10 mb-4">
                    <CheckCircle className="h-8 w-8 text-emerald-500" />
                  </div>
                  <h3 className="text-xl font-semibold mb-2">Message Sent!</h3>
                  <p className="text-muted-foreground">
                    Thank you for contacting us. We'll get back to you soon.
                  </p>
                </div>
              ) : (
                <form onSubmit={handleSubmit} className="space-y-6">
                  <div>
                    <label htmlFor="name" className="block text-sm font-medium mb-2">
                      Name
                    </label>
                    <div className="relative">
                      <User className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                      <input
                        type="text"
                        id="name"
                        name="name"
                        value={formData.name}
                        onChange={handleChange}
                        required
                        className="flex h-12 w-full rounded-md border border-input bg-background pl-10 pr-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
                        placeholder="Your name"
                        data-testid="contact-name-input"
                      />
                    </div>
                  </div>

                  <div>
                    <label htmlFor="email" className="block text-sm font-medium mb-2">
                      Email
                    </label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                      <input
                        type="email"
                        id="email"
                        name="email"
                        value={formData.email}
                        onChange={handleChange}
                        required
                        className="flex h-12 w-full rounded-md border border-input bg-background pl-10 pr-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
                        placeholder="your.email@example.com"
                        data-testid="contact-email-input"
                      />
                    </div>
                  </div>

                  <div>
                    <label htmlFor="message" className="block text-sm font-medium mb-2">
                      Message
                    </label>
                    <div className="relative">
                      <MessageSquare className="absolute left-3 top-3 h-5 w-5 text-muted-foreground" />
                      <textarea
                        id="message"
                        name="message"
                        value={formData.message}
                        onChange={handleChange}
                        required
                        rows={6}
                        className="flex w-full rounded-md border border-input bg-background pl-10 pr-3 py-3 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
                        placeholder="Your message..."
                        data-testid="contact-message-input"
                      />
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full bg-primary text-primary-foreground hover:bg-primary/90 h-12 px-6 py-2 rounded-full font-medium transition-all shadow-lg disabled:opacity-50 flex items-center justify-center gap-2"
                    data-testid="contact-submit-btn"
                  >
                    {loading ? (
                      'Sending...'
                    ) : (
                      <>
                        <Send className="h-4 w-4" />
                        Send Message
                      </>
                    )}
                  </button>
                </form>
              )}
            </div>
          </div>

          {/* Contact Info */}
          <div>
            <div className="rounded-xl border bg-card shadow-sm p-8 mb-6">
              <h2 
                className="text-2xl font-bold mb-6"
                style={{ fontFamily: "'Chivo', sans-serif" }}
              >
                Contact Information
              </h2>
              <div className="space-y-6">
                <div className="flex items-start gap-4">
                  <div className="p-3 rounded-full bg-primary/10">
                    <Mail className="h-6 w-6 text-primary" />
                  </div>
                  <div>
                    <h3 className="font-semibold mb-1">Email</h3>
                    <p className="text-muted-foreground">contact@stockanalyzer.com</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="rounded-xl border bg-card shadow-sm p-8">
              <h2 
                className="text-2xl font-bold mb-4"
                style={{ fontFamily: "'Chivo', sans-serif" }}
              >
                FAQ
              </h2>
              <div className="space-y-4">
                <div>
                  <h3 className="font-semibold mb-2">How accurate are the predictions?</h3>
                  <p className="text-sm text-muted-foreground">
                    Our AI uses linear regression on historical data. While predictions provide useful insights, they should not be the sole basis for investment decisions.
                  </p>
                </div>
                <div>
                  <h3 className="font-semibold mb-2">Is the data real-time?</h3>
                  <p className="text-sm text-muted-foreground">
                    Yes, we use Alpha Vantage API to provide real-time stock market data with minimal delays.
                  </p>
                </div>
                <div>
                  <h3 className="font-semibold mb-2">Can I use this for trading?</h3>
                  <p className="text-sm text-muted-foreground">
                    This is an educational tool. Always do thorough research and consult financial advisors before making investment decisions.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Contact;
