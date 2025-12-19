'use client';

import Link from 'next/link';
import { ArrowRight, Activity, MessageSquare, Users, Shield, Zap, Globe, Key, Phone, Copy } from 'lucide-react';

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Navigation */}
      <nav className="fixed top-0 w-full bg-white/80 backdrop-blur-md border-b border-gray-200 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
              <Activity className="w-6 h-6 text-white" />
            </div>
            <span className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              MedAssist
            </span>
          </div>
          <Link 
            href="/login"
            className="px-6 py-2.5 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:shadow-lg hover:scale-105 transition-all duration-200 font-medium"
          >
            Admin Login
          </Link>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-6">
        <div className="max-w-7xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-100 rounded-full text-blue-700 text-sm font-medium mb-8">
            <Zap className="w-4 h-4" />
            AI-Powered Healthcare Platform
          </div>
          
          <h1 className="text-6xl md:text-7xl font-bold text-gray-900 mb-6 leading-tight">
            Healthcare Made
            <br />
            <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              Simple & Accessible
            </span>
          </h1>
          
          <p className="text-xl text-gray-600 max-w-3xl mx-auto mb-12 leading-relaxed">
            Connect patients with clinics through AI-powered WhatsApp chatbot. 
            Intelligent triage, multi-language support, and real-time patient management.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link 
              href="/login"
              className="group px-8 py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl hover:shadow-2xl hover:scale-105 transition-all duration-200 font-semibold text-lg flex items-center justify-center gap-2"
            >
              Get Started
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </Link>
            <a 
              href="https://drive.google.com/file/d/1RRJcZTuI-Z3EdVwEbxcsh_BW9gxDE27W/view?usp=sharing"
              target="_blank"
              rel="noopener noreferrer"
              className="px-8 py-4 bg-white text-gray-700 rounded-xl border-2 border-gray-200 hover:border-blue-600 hover:shadow-xl transition-all duration-200 font-semibold text-lg"
            >
              Watch Demo
            </a>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-8 max-w-3xl mx-auto mt-20">
            <div className="text-center">
              <div className="text-4xl font-bold text-gray-900 mb-2">98%</div>
              <div className="text-gray-600">Accuracy</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-gray-900 mb-2">&lt;2s</div>
              <div className="text-gray-600">Response Time</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-gray-900 mb-2">24/7</div>
              <div className="text-gray-600">Availability</div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 px-6 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
              Powerful Features for Modern Healthcare
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Everything you need to manage patient care efficiently
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <div className="group p-8 rounded-2xl border-2 border-gray-100 hover:border-blue-600 hover:shadow-xl transition-all duration-300">
              <div className="w-14 h-14 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <MessageSquare className="w-7 h-7 text-white" />
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-4">
                WhatsApp Integration
              </h3>
              <p className="text-gray-600 leading-relaxed">
                Patients interact via WhatsApp - no app installation required. 
                Seamless, familiar, and accessible to everyone.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="group p-8 rounded-2xl border-2 border-gray-100 hover:border-purple-600 hover:shadow-xl transition-all duration-300">
              <div className="w-14 h-14 bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <Activity className="w-7 h-7 text-white" />
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-4">
                AI Triage System
              </h3>
              <p className="text-gray-600 leading-relaxed">
                Intelligent symptom analysis with 4-level priority scoring. 
                Critical cases flagged instantly for immediate attention.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="group p-8 rounded-2xl border-2 border-gray-100 hover:border-green-600 hover:shadow-xl transition-all duration-300">
              <div className="w-14 h-14 bg-gradient-to-br from-green-500 to-green-600 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <Globe className="w-7 h-7 text-white" />
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-4">
                Multi-Language Support
              </h3>
              <p className="text-gray-600 leading-relaxed">
                Communicate in English, Yoruba, Igbo, Hausa, and more. 
                Breaking language barriers in healthcare.
              </p>
            </div>

            {/* Feature 4 */}
            <div className="group p-8 rounded-2xl border-2 border-gray-100 hover:border-orange-600 hover:shadow-xl transition-all duration-300">
              <div className="w-14 h-14 bg-gradient-to-br from-orange-500 to-orange-600 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <Users className="w-7 h-7 text-white" />
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-4">
                Patient Management
              </h3>
              <p className="text-gray-600 leading-relaxed">
                Real-time dashboard with patient queue, chat history, and 
                comprehensive triage reports.
              </p>
            </div>

            {/* Feature 5 */}
            <div className="group p-8 rounded-2xl border-2 border-gray-100 hover:border-red-600 hover:shadow-xl transition-all duration-300">
              <div className="w-14 h-14 bg-gradient-to-br from-red-500 to-red-600 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <Shield className="w-7 h-7 text-white" />
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-4">
                Multi-Tenant Security
              </h3>
              <p className="text-gray-600 leading-relaxed">
                Complete data isolation between clinics. HIPAA-compliant 
                encryption and secure authentication.
              </p>
            </div>

            {/* Feature 6 */}
            <div className="group p-8 rounded-2xl border-2 border-gray-100 hover:border-indigo-600 hover:shadow-xl transition-all duration-300">
              <div className="w-14 h-14 bg-gradient-to-br from-indigo-500 to-indigo-600 rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <Zap className="w-7 h-7 text-white" />
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-4">
                Real-Time Updates
              </h3>
              <p className="text-gray-600 leading-relaxed">
                Live patient queue updates, instant notifications for critical 
                cases, and automated alerts.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Demo & Testing Section */}
      <section className="py-20 px-6 bg-gradient-to-br from-blue-50 to-purple-50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-purple-100 rounded-full text-purple-700 text-sm font-medium mb-4">
              <Key className="w-4 h-4" />
              Demo Access
            </div>
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
              Try It Now
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Test the platform with demo accounts or interact with our WhatsApp bot
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8 max-w-6xl mx-auto">
            {/* Admin Login Credentials */}
            <div className="bg-white rounded-2xl p-8 shadow-xl border border-gray-200">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-12 h-12 bg-gradient-to-br from-blue-600 to-purple-600 rounded-xl flex items-center justify-center">
                  <Key className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 className="text-2xl font-bold text-gray-900">Admin Dashboard</h3>
                  <p className="text-gray-600">Test with any clinic account</p>
                </div>
              </div>

              <div className="space-y-4">
                {/* Clinic 1 */}
                <div className="p-4 bg-blue-50 rounded-xl border border-blue-200">
                  <div className="font-semibold text-blue-900 mb-2">City Health Clinic</div>
                  <div className="space-y-1 text-sm">
                    <div className="flex items-center gap-2">
                      <span className="text-gray-600 w-16">Email:</span>
                      <code className="flex-1 bg-white px-2 py-1 rounded text-blue-600">admin@cityhealthclinic.com</code>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-gray-600 w-16">Password:</span>
                      <code className="flex-1 bg-white px-2 py-1 rounded text-blue-600">admin1234</code>
                    </div>
                  </div>
                </div>

                {/* Clinic 2 */}
                <div className="p-4 bg-green-50 rounded-xl border border-green-200">
                  <div className="font-semibold text-green-900 mb-2">Green Cross Clinic</div>
                  <div className="space-y-1 text-sm">
                    <div className="flex items-center gap-2">
                      <span className="text-gray-600 w-16">Email:</span>
                      <code className="flex-1 bg-white px-2 py-1 rounded text-green-600">admin@greencross.com</code>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-gray-600 w-16">Password:</span>
                      <code className="flex-1 bg-white px-2 py-1 rounded text-green-600">admin5679</code>
                    </div>
                  </div>
                </div>

                {/* Clinic 3 */}
                <div className="p-4 bg-purple-50 rounded-xl border border-purple-200">
                  <div className="font-semibold text-purple-900 mb-2">Sunrise Clinic</div>
                  <div className="space-y-1 text-sm">
                    <div className="flex items-center gap-2">
                      <span className="text-gray-600 w-16">Email:</span>
                      <code className="flex-1 bg-white px-2 py-1 rounded text-purple-600">admin@sunriseclinic.com</code>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-gray-600 w-16">Password:</span>
                      <code className="flex-1 bg-white px-2 py-1 rounded text-purple-600">admin7712</code>
                    </div>
                  </div>
                </div>
              </div>

              <Link 
                href="/login"
                className="mt-6 w-full flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl hover:shadow-lg hover:scale-105 transition-all duration-200 font-semibold"
              >
                Login to Dashboard
                <ArrowRight className="w-5 h-5" />
              </Link>
            </div>

            {/* WhatsApp Bot */}
            <div className="bg-white rounded-2xl p-8 shadow-xl border border-gray-200">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-green-600 rounded-xl flex items-center justify-center">
                  <Phone className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 className="text-2xl font-bold text-gray-900">WhatsApp Bot</h3>
                  <p className="text-gray-600">Try the patient experience</p>
                </div>
              </div>

              <div className="space-y-6">
                <div>
                  <div className="text-sm font-semibold text-gray-700 mb-2">Step 1: Add Bot Number</div>
                  <div className="flex items-center gap-2 p-4 bg-green-50 rounded-xl border border-green-200">
                    <Phone className="w-5 h-5 text-green-600" />
                    <a 
                      href="https://wa.me/14155238886"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex-1 text-lg font-mono font-bold text-green-600 hover:text-green-700"
                    >
                      +1 (415) 523-8886
                    </a>
                    <button 
                      onClick={() => navigator.clipboard.writeText('+14155238886')}
                      className="p-2 hover:bg-green-100 rounded-lg transition-colors"
                      title="Copy number"
                    >
                      <Copy className="w-4 h-4 text-green-600" />
                    </button>
                  </div>
                </div>

                <div>
                  <div className="text-sm font-semibold text-gray-700 mb-2">Step 2: Send Join Code</div>
                  <div className="p-4 bg-green-50 rounded-xl border border-green-200">
                    <div className="text-sm text-gray-600 mb-2">Send this message to activate the bot:</div>
                    <code className="block p-3 bg-white rounded-lg text-green-600 font-mono font-bold text-lg">
                      join various-mill
                    </code>
                  </div>
                </div>

                <div>
                  <div className="text-sm font-semibold text-gray-700 mb-2">Step 3: Start Chatting</div>
                  <div className="p-4 bg-green-50 rounded-xl border border-green-200">
                    <div className="text-sm text-gray-600 mb-3">Try these examples:</div>
                    <ul className="space-y-2 text-sm">
                      <li className="flex items-start gap-2">
                        <span className="text-green-600 font-bold">•</span>
                        <span className="text-gray-700">"I have a headache and fever"</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-green-600 font-bold">•</span>
                        <span className="text-gray-700">"Book an appointment for tomorrow"</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-green-600 font-bold">•</span>
                        <span className="text-gray-700">"I need to refill my medication"</span>
                      </li>
                    </ul>
                  </div>
                </div>
              </div>

              <a 
                href="https://wa.me/14155238886?text=join%20various-mill"
                target="_blank"
                rel="noopener noreferrer"
                className="mt-6 w-full flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-green-500 to-green-600 text-white rounded-xl hover:shadow-lg hover:scale-105 transition-all duration-200 font-semibold"
              >
                <MessageSquare className="w-5 h-5" />
                Open in WhatsApp
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-6">
        <div className="max-w-5xl mx-auto bg-gradient-to-br from-blue-600 to-purple-600 rounded-3xl p-12 md:p-16 text-center text-white shadow-2xl">
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            Ready to Transform Your Clinic?
          </h2>
          <p className="text-xl text-blue-100 mb-10 max-w-2xl mx-auto">
            Join modern healthcare providers using MedAssist to deliver 
            better, faster patient care.
          </p>
          <Link 
            href="/login"
            className="inline-flex items-center gap-2 px-8 py-4 bg-white text-blue-600 rounded-xl hover:shadow-2xl hover:scale-105 transition-all duration-200 font-semibold text-lg"
          >
            Start Free Trial
            <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-6 bg-gray-50 border-t border-gray-200">
        <div className="max-w-7xl mx-auto text-center text-gray-600">
          <div className="flex items-center justify-center gap-2 mb-4">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
              <Activity className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold text-gray-900">MedAssist</span>
          </div>
          <p className="mb-4">
            AI-Powered Healthcare Platform for Modern Clinics
          </p>
          <p className="text-sm">
            © 2025 MedAssist. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}
