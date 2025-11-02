"use client";

import { useState, useEffect } from "react";
import useUser from "@/utils/useUser";
import {
  ArrowRight,
  Upload,
  Brain,
  FileText,
  Users,
  MessageSquare,
  BarChart3,
} from "lucide-react";

export default function OnboardingPage() {
  const { data: user, loading } = useUser();
  const [currentSlide, setCurrentSlide] = useState(0);

  useEffect(() => {
    // Redirect authenticated users to workspace
    if (user && !loading) {
      window.location.href = "/workspace";
    }
  }, [user, loading]);

  const slides = [
    {
      title: "Welcome to Dealysis",
      subtitle: "AI-Powered Investment Memo Generator",
      description:
        "Transform your due diligence documents into professional investment memos in minutes",
      icon: <Brain size={48} className="text-white" />,
      image: "/api/placeholder/600/400",
    },
    {
      title: "Upload Your Documents",
      subtitle: "Drag & Drop Due Diligence Materials",
      description:
        "Upload pitch decks, transcripts, financial documents, and market research. Support for PDF, DOCX, and TXT files.",
      icon: <Upload size={48} className="text-white" />,
      features: [
        "Pitch Decks",
        "Meeting Transcripts",
        "Financial Models",
        "Market Research",
        "Example Memos",
      ],
    },
    {
      title: "AI Analysis & Generation",
      subtitle: "Intelligent Document Processing",
      description:
        "Our AI analyzes your documents and generates a comprehensive investment memo with all standard sections.",
      icon: <BarChart3 size={48} className="text-white" />,
      features: [
        "Executive Summary",
        "Market Analysis",
        "Financial Overview",
        "Risk Assessment",
        "Investment Recommendation",
      ],
    },
    {
      title: "Edit & Collaborate",
      subtitle: "Interactive Memo Refinement",
      description:
        "Chat with AI to refine sections, add more documents, and export your final memo ready for IC presentation.",
      icon: <MessageSquare size={48} className="text-white" />,
      features: [
        "AI Chat Editing",
        "Add More Documents",
        "Real-time Updates",
        "Export Options",
        "Team Collaboration",
      ],
    },
  ];

  const nextSlide = () => {
    setCurrentSlide((prev) => (prev + 1) % slides.length);
  };

  const prevSlide = () => {
    setCurrentSlide((prev) => (prev - 1 + slides.length) % slides.length);
  };

  const goToSlide = (index) => {
    setCurrentSlide(index);
  };

  // Show loading state while checking auth
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#0A0B0D] via-[#1A1B23] to-[#2A1B3D] flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#6366F1] mx-auto mb-4"></div>
          <p className="text-white">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <>
      <link
        href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Instrument+Serif:ital,wght@0,400;1,400&display=swap"
        rel="stylesheet"
      />

      <div className="min-h-screen bg-gradient-to-br from-[#0A0B0D] via-[#1A1B23] to-[#2A1B3D]">
        {/* Header */}
        <header className="relative z-10 px-6 py-6">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <img
                src="https://ucarecdn.com/a197b497-5194-4168-87d3-5bc3a0bdc81a/-/format/auto/"
                alt="Dealysis Logo"
                className="w-8 h-8"
                onError={(e) => {
                  e.target.style.display = "none";
                  e.target.nextSibling.style.display = "flex";
                }}
              />
              <div
                className="w-8 h-8 bg-gradient-to-r from-[#6366F1] to-[#8B5CF6] rounded-lg flex items-center justify-center"
                style={{ display: "none" }}
              >
                <Brain size={18} className="text-white" />
              </div>
              <h1
                className="text-2xl font-bold text-white"
                style={{ fontFamily: "Inter, sans-serif" }}
              >
                Dealysis
              </h1>
            </div>
            <a
              href="/workspace"
              className="px-6 py-2 bg-gradient-to-r from-[#6366F1] to-[#8B5CF6] text-white font-medium rounded-lg hover:from-[#5B61F0] hover:to-[#7C3AED] transition-all duration-200"
              style={{ fontFamily: "Inter, sans-serif" }}
            >
              {user ? "Go to Workspace" : "Get Started"}
            </a>
          </div>
        </header>

        {/* Main Content */}
        <div className="max-w-7xl mx-auto px-6 py-12">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center min-h-[70vh]">
            {/* Left Side - Content */}
            <div className="space-y-8">
              <div className="space-y-6">
                <div className="w-16 h-16 bg-gradient-to-r from-[#6366F1] to-[#8B5CF6] rounded-2xl flex items-center justify-center">
                  {slides[currentSlide].icon}
                </div>

                <div className="space-y-4">
                  <h1
                    className="text-5xl lg:text-6xl font-bold text-white leading-tight"
                    style={{ fontFamily: "Instrument Serif, serif" }}
                  >
                    {slides[currentSlide].title}
                  </h1>
                  <h2
                    className="text-xl text-[#A1A1AA] font-medium"
                    style={{ fontFamily: "Inter, sans-serif" }}
                  >
                    {slides[currentSlide].subtitle}
                  </h2>
                  <p
                    className="text-lg text-[#D4D4D8] leading-relaxed max-w-lg"
                    style={{ fontFamily: "Inter, sans-serif" }}
                  >
                    {slides[currentSlide].description}
                  </p>
                </div>

                {slides[currentSlide].features && (
                  <div className="space-y-3">
                    {slides[currentSlide].features.map((feature, index) => (
                      <div key={index} className="flex items-center space-x-3">
                        <div className="w-2 h-2 bg-gradient-to-r from-[#6366F1] to-[#8B5CF6] rounded-full"></div>
                        <span
                          className="text-[#E4E4E7]"
                          style={{ fontFamily: "Inter, sans-serif" }}
                        >
                          {feature}
                        </span>
                      </div>
                    ))}
                  </div>
                )}

                <div className="flex items-center space-x-4 pt-6">
                  <a
                    href="/workspace"
                    className="px-8 py-4 bg-gradient-to-r from-[#6366F1] to-[#8B5CF6] text-white font-semibold rounded-xl hover:from-[#5B61F0] hover:to-[#7C3AED] transition-all duration-200 flex items-center space-x-2"
                    style={{ fontFamily: "Inter, sans-serif" }}
                  >
                    <span>Get Started</span>
                    <ArrowRight size={20} />
                  </a>

                  {currentSlide < slides.length - 1 && (
                    <button
                      onClick={nextSlide}
                      className="px-6 py-4 border border-[#374151] text-[#D4D4D8] font-medium rounded-xl hover:border-[#6366F1] hover:text-white transition-all duration-200"
                      style={{ fontFamily: "Inter, sans-serif" }}
                    >
                      Next
                    </button>
                  )}
                </div>
              </div>
            </div>

            {/* Right Side - Visual */}
            <div className="relative">
              <div className="bg-gradient-to-r from-[#1F2937] to-[#374151] rounded-3xl p-8 shadow-2xl border border-[#374151]">
                <div className="space-y-6">
                  {/* Mock Interface */}
                  <div className="flex items-center space-x-3 pb-4 border-b border-[#4B5563]">
                    <div className="w-3 h-3 bg-[#EF4444] rounded-full"></div>
                    <div className="w-3 h-3 bg-[#F59E0B] rounded-full"></div>
                    <div className="w-3 h-3 bg-[#10B981] rounded-full"></div>
                    <span className="text-[#9CA3AF] text-sm ml-4">
                      Dealysis Workspace
                    </span>
                  </div>

                  {currentSlide === 0 && (
                    <div className="space-y-4">
                      <div className="h-8 bg-gradient-to-r from-[#6366F1] to-[#8B5CF6] rounded-lg w-3/4"></div>
                      <div className="space-y-2">
                        <div className="h-4 bg-[#4B5563] rounded w-full"></div>
                        <div className="h-4 bg-[#4B5563] rounded w-5/6"></div>
                      </div>
                    </div>
                  )}

                  {currentSlide === 1 && (
                    <div className="space-y-4">
                      <div className="border-2 border-dashed border-[#6366F1] rounded-xl p-6 text-center">
                        <Upload
                          size={24}
                          className="text-[#6366F1] mx-auto mb-2"
                        />
                        <p className="text-[#D4D4D8] text-sm">
                          Drop files here
                        </p>
                      </div>
                      <div className="space-y-2">
                        {[
                          "pitch_deck.pdf",
                          "transcript.txt",
                          "financials.xlsx",
                        ].map((file, i) => (
                          <div
                            key={i}
                            className="flex items-center space-x-2 p-2 bg-[#374151] rounded"
                          >
                            <FileText size={16} className="text-[#6366F1]" />
                            <span className="text-[#D4D4D8] text-sm">
                              {file}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {currentSlide === 2 && (
                    <div className="space-y-4">
                      <div className="flex items-center space-x-2 mb-4">
                        <div className="w-4 h-4 border-2 border-[#6366F1] border-t-transparent rounded-full animate-spin"></div>
                        <span className="text-[#D4D4D8] text-sm">
                          Analyzing documents...
                        </span>
                      </div>
                      <div className="space-y-2">
                        <div className="h-4 bg-[#6366F1] rounded w-full opacity-30"></div>
                        <div className="h-4 bg-[#6366F1] rounded w-4/5 opacity-50"></div>
                        <div className="h-4 bg-[#6366F1] rounded w-3/4 opacity-70"></div>
                        <div className="h-4 bg-[#6366F1] rounded w-1/2 opacity-90"></div>
                      </div>
                    </div>
                  )}

                  {currentSlide === 3 && (
                    <div className="space-y-4">
                      <div className="bg-[#374151] rounded-lg p-3">
                        <div className="flex items-start space-x-2">
                          <div className="w-6 h-6 bg-[#6366F1] rounded-full flex items-center justify-center">
                            <Users size={12} className="text-white" />
                          </div>
                          <div className="flex-1">
                            <p className="text-[#D4D4D8] text-sm">
                              Make the team section more concise
                            </p>
                          </div>
                        </div>
                      </div>
                      <div className="bg-[#1F2937] rounded-lg p-3">
                        <div className="flex items-start space-x-2">
                          <div className="w-6 h-6 bg-[#8B5CF6] rounded-full flex items-center justify-center">
                            <Brain size={12} className="text-white" />
                          </div>
                          <div className="flex-1">
                            <p className="text-[#D4D4D8] text-sm">
                              I'll condense the team section to highlight key
                              experience...
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Slide Navigation */}
          <div className="flex justify-center items-center space-x-4 mt-12">
            <button
              onClick={prevSlide}
              className="p-2 text-[#9CA3AF] hover:text-white transition-colors"
              disabled={currentSlide === 0}
            >
              <ArrowRight size={20} className="rotate-180" />
            </button>

            <div className="flex space-x-2">
              {slides.map((_, index) => (
                <button
                  key={index}
                  onClick={() => goToSlide(index)}
                  className={`w-3 h-3 rounded-full transition-all duration-200 ${
                    index === currentSlide
                      ? "bg-gradient-to-r from-[#6366F1] to-[#8B5CF6]"
                      : "bg-[#374151] hover:bg-[#4B5563]"
                  }`}
                />
              ))}
            </div>

            <button
              onClick={nextSlide}
              className="p-2 text-[#9CA3AF] hover:text-white transition-colors"
              disabled={currentSlide === slides.length - 1}
            >
              <ArrowRight size={20} />
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
