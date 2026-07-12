"use client";

import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  BookOpen,
  MessageSquare,
  Sparkles,
  TrendingUp,
  Clock,
  FileText,
  CheckCircle,
  HelpCircle,
  Calendar,
  LogOut,
  Folder,
  Plus,
  Trash2,
  UploadCloud,
  Loader2,
  ChevronRight,
  RefreshCw,
  Award,
  Play,
  Square,
  User,
  Check,
  Flame,
  Volume2,
  Lock,
  ArrowRight,
  Paperclip,
  Settings,
  X
} from "lucide-react";
import api from "@/lib/api";

type Tab = "dashboard" | "materials" | "chat" | "flashcards" | "quiz" | "planner";

export default function Home() {
  // Auth state
  const [token, setToken] = useState<string | null>(null);
  const [isLogin, setIsLogin] = useState(true);
  const [authEmail, setAuthEmail] = useState("");
  const [authPassword, setAuthPassword] = useState("");
  const [authName, setAuthName] = useState("");
  const [authError, setAuthError] = useState("");
  const [authLoading, setAuthLoading] = useState(false);
  const [otpCode, setOtpCode] = useState("");
  const [showOtpModal, setShowOtpModal] = useState(false);

  // App core state
  const [activeTab, setActiveTab] = useState<Tab>("dashboard");
  const [userProfile, setUserProfile] = useState<any>(null);
  const [analytics, setAnalytics] = useState<any>({
    streak_days: 0,
    time_studied_minutes: 0.0,
    files_uploaded: 0,
    ai_conversations: 0,
    flashcards_total: 0,
    flashcards_mastered: 0,
    quiz_count: 0,
    quiz_average_percent: 0,
    weak_subjects: [],
    strong_subjects: [],
    weekly_progress: [],
    recent_activity: []
  });

  // Materials state
  const [subjects, setSubjects] = useState<any[]>([]);
  const [files, setFiles] = useState<any[]>([]);
  const [newSubjName, setNewSubjName] = useState("");
  const [newSubjColor, setNewSubjColor] = useState("#6366f1");
  const [selectedSubjId, setSelectedSubjId] = useState<number | null>(null);
  const [uploading, setUploading] = useState(false);

  // Chat state
  const [conversations, setConversations] = useState<any[]>([]);
  const [activeConvId, setActiveConvId] = useState<number | null>(null);
  const [chatMessages, setChatMessages] = useState<any[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [restrictToDocs, setRestrictToDocs] = useState(true);
  const [chatSelectedSubjId, setChatSelectedSubjId] = useState<number | null>(null);
  const [chatSelectedFileId, setChatSelectedFileId] = useState<number | null>(null);
  const [chatSubjectFilter, setChatSubjectFilter] = useState<number | null>(null);
  const [chatUploadStatus, setChatUploadStatus] = useState<string>("");
  const chatBottomRef = useRef<HTMLDivElement>(null);

  // Flashcards state
  const [flashcards, setFlashcards] = useState<any[]>([]);
  const [activeCardIdx, setActiveCardIdx] = useState(0);
  const [showFlashcardAnswer, setShowFlashcardAnswer] = useState(false);
  const [cardFilterSubj, setCardFilterSubj] = useState<number | null>(null);
  const [fcSelectedSubjId, setFcSelectedSubjId] = useState<number | null>(null);
  const [fcSelectedFileId, setFcSelectedFileId] = useState<number | null>(null);

  // Quiz state
  const [quizList, setQuizList] = useState<any[]>([]);
  const [activeQuiz, setActiveQuiz] = useState<any>(null);
  const [activeQuizAnswers, setActiveQuizAnswers] = useState<Record<number, string>>({});
  const [quizTimer, setQuizTimer] = useState(0);
  const [quizTimerInterval, setQuizTimerInterval] = useState<any>(null);
  const [quizResults, setQuizResults] = useState<any>(null);
  const [generatingQuiz, setGeneratingQuiz] = useState(false);
  const [quizGenTitle, setQuizGenTitle] = useState("AI Practice Quiz");
  const [quizGenSubj, setQuizGenSubj] = useState<number | null>(null);
  const [quizGenFile, setQuizGenFile] = useState<number | null>(null);
  const [quizGenSize, setQuizGenSize] = useState(5);
  const [quizGenDifficulty, setQuizGenDifficulty] = useState("medium");

  // Planner state
  const [studyPlan, setStudyPlan] = useState<any>(null);
  const [activeSession, setActiveSession] = useState<any>(null);
  const [sessionDuration, setSessionDuration] = useState(0);
  const [sessionTimer, setSessionTimer] = useState<any>(null);
  const [planGenDays, setPlanGenDays] = useState(7);
  const [planGenHours, setPlanGenHours] = useState(2);
  const [planGenSubjects, setPlanGenSubjects] = useState<number[]>([]);
  const [generatingPlan, setGeneratingPlan] = useState(false);

  // Settings modal state
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [settingsName, setSettingsName] = useState("");
  const [settingsPassword, setSettingsPassword] = useState("");
  const [settingsError, setSettingsError] = useState("");
  const [settingsSuccess, setSettingsSuccess] = useState("");
  const [settingsLoading, setSettingsLoading] = useState(false);
  const [googleClientId, setGoogleClientId] = useState("your-google-client-id.apps.googleusercontent.com");
  const [googleClientSecret, setGoogleClientSecret] = useState("••••••••••••••••••••");
  const [enableGoogleAuth, setEnableGoogleAuth] = useState(true);

  // Dashboard graph range state
  const [graphRange, setGraphRange] = useState<"daily" | "weekly" | "monthly">("weekly");

  // Load Auth
  useEffect(() => {
    if (typeof window !== "undefined") {
      const savedToken = localStorage.getItem("token");
      if (savedToken) {
        setToken(savedToken);
      }
    }
  }, []);

  // Fetch Google Client ID and initialize Google Identity SDK
  useEffect(() => {
    const initGoogleAuth = async () => {
      try {
        const config = await api.getAuthConfig();
        if (config && config.google_client_id) {
          setGoogleClientId(config.google_client_id);
          
          // Setup polling interval to wait for Google SDK script to load
          const checkGoogleSDK = setInterval(() => {
            if (typeof window !== "undefined" && (window as any).google) {
              clearInterval(checkGoogleSDK);
              
              (window as any).google.accounts.id.initialize({
                client_id: config.google_client_id,
                callback: async (response: any) => {
                  setAuthError("");
                  setAuthLoading(true);
                  try {
                    const res = await api.loginGoogle(response.credential);
                    localStorage.setItem("token", res.access_token);
                    setToken(res.access_token);
                  } catch (err: any) {
                    setAuthError(err.message || "Google Login failed");
                  } finally {
                    setAuthLoading(false);
                  }
                }
              });
              
              // Render standard google sign-in button inside hidden container to support programatic click trigger
              const hiddenContainer = document.getElementById("google-signin-button-hidden");
              if (hiddenContainer) {
                (window as any).google.accounts.id.renderButton(
                  hiddenContainer,
                  { theme: "outline", size: "large" }
                );
              }
            }
          }, 500);
          
          // Clear interval fallback if Google SDK fails to load in 10s
          setTimeout(() => clearInterval(checkGoogleSDK), 10000);
        }
      } catch (e) {
        console.error("Failed to load Google Auth configuration:", e);
      }
    };
    initGoogleAuth();
  }, []);


  // Fetch app data when token is valid
  useEffect(() => {
    if (token) {
      loadProfile();
      loadDashboardAnalytics();
      loadSubjects();
      loadFiles();
      loadConversations();
      loadFlashcards();
      loadQuizzes();
      loadStudyPlan();
    }
  }, [token]);

  // Scroll chat bottom
  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages]);

  // Track study session timer
  useEffect(() => {
    if (activeSession) {
      const timer = setInterval(() => {
        setSessionDuration((prev) => prev + 1);
      }, 1000);
      setSessionTimer(timer);
      return () => clearInterval(timer);
    } else {
      if (sessionTimer) {
        clearInterval(sessionTimer);
        setSessionTimer(null);
      }
      setSessionDuration(0);
    }
  }, [activeSession]);

  // Poll file processing status periodically when a file is processing
  useEffect(() => {
    const hasProcessing = files.some((f) => f.status === "processing");
    if (!hasProcessing) return;

    const interval = setInterval(() => {
      loadFiles();
      loadDashboardAnalytics();
    }, 3000);

    return () => clearInterval(interval);
  }, [files]);

  // Auto-select subject and file in flashcard tab if only 1 exists
  useEffect(() => {
    if (subjects.length > 0 && !fcSelectedSubjId) {
      if (subjects.length === 1) {
        setFcSelectedSubjId(subjects[0].id);
      }
    }
  }, [subjects, fcSelectedSubjId]);

  useEffect(() => {
    if (files.length > 0 && !fcSelectedFileId) {
      const filtered = files.filter((f) => !fcSelectedSubjId || f.subject_id === fcSelectedSubjId);
      if (filtered.length === 1) {
        setFcSelectedFileId(filtered[0].id);
      }
    }
  }, [files, fcSelectedSubjId, fcSelectedFileId]);


  const handleLogout = () => {
    localStorage.removeItem("token");
    setToken(null);
    setUserProfile(null);
    setActiveTab("dashboard");
  };


  // --- Auth Handlers ---
  const handleAuthSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthError("");
    setAuthLoading(true);

    try {
      if (isLogin) {
        const res = await api.login({ email: authEmail, password: authPassword });
        localStorage.setItem("token", res.access_token);
        setToken(res.access_token);
      } else {
        await api.register({
          email: authEmail,
          password: authPassword,
          full_name: authName
        });
        setShowOtpModal(true);
      }
    } catch (err: any) {
      setAuthError(err.message || "Authentication failed");
    } finally {
      setAuthLoading(false);
    }
  };

  const handleOtpVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthError("");
    setAuthLoading(true);

    try {
      await api.verifyOTP({
        email: authEmail,
        code: otpCode,
        purpose: "verify_email"
      });
      setShowOtpModal(false);
      setIsLogin(true);
      // Auto log in after registration
      const loginRes = await api.login({ email: authEmail, password: authPassword });
      localStorage.setItem("token", loginRes.access_token);
      setToken(loginRes.access_token);
    } catch (err: any) {
      setAuthError(err.message || "OTP verification failed");
    } finally {
      setAuthLoading(false);
    }
  };

  const handleGoogleMockLogin = async () => {
    setAuthError("");
    setAuthLoading(true);
    try {
      const mockToken = `mock-google-token-${authEmail || "student@academy.com"}`;
      const res = await api.loginGoogle(mockToken);
      localStorage.setItem("token", res.access_token);
      setToken(res.access_token);
    } catch (err: any) {
      setAuthError(err.message || "Google Login failed");
    } finally {
      setAuthLoading(false);
    }
  };

  const handleGoogleLogin = () => {
    if (googleClientId && googleClientId !== "your-google-client-id.apps.googleusercontent.com" && googleClientId !== "") {
      const hiddenBtn = document.querySelector("#google-signin-button-hidden [role='button']") as HTMLElement;
      if (hiddenBtn) {
        hiddenBtn.click();
      } else {
        if (typeof window !== "undefined" && (window as any).google) {
          (window as any).google.accounts.id.prompt();
        } else {
          setAuthError("Google Sign-In SDK is still loading. Please try again in a moment.");
        }
      }
    } else {
      handleGoogleMockLogin();
    }
  };


  // --- Loader functions ---
  const loadProfile = async () => {
    try {
      const profile = await api.getProfile();
      setUserProfile(profile);
      setSettingsName(profile.full_name || "");
    } catch (e) {
      handleLogout();
    }
  };

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setSettingsError("");
    setSettingsSuccess("");
    setSettingsLoading(true);

    try {
      const payload: any = { full_name: settingsName };
      if (settingsPassword.trim()) {
        payload.password = settingsPassword;
      }
      const updated = await api.updateProfile(payload);
      setUserProfile(updated);
      setSettingsSuccess("Profile settings successfully updated!");
      setSettingsPassword("");
    } catch (err: any) {
      setSettingsError(err.message || "Failed to update profile settings.");
    } finally {
      setSettingsLoading(false);
    }
  };



  const loadDashboardAnalytics = async () => {
    try {
      const data = await api.getAnalytics();
      setAnalytics(data);
    } catch (e) {}
  };

  const loadSubjects = async () => {
    try {
      const list = await api.getSubjects();
      setSubjects(list);
    } catch (e) {}
  };

  const loadFiles = async () => {
    try {
      const list = await api.getFiles();
      setFiles(list);
    } catch (e) {}
  };

  const loadConversations = async () => {
    try {
      const list = await api.getConversations();
      setConversations(list);
      if (list.length > 0 && !activeConvId) {
        selectConversation(list[0].id);
      }
    } catch (e) {}
  };

  const loadFlashcards = async () => {
    try {
      const list = await api.getFlashcards(cardFilterSubj || undefined);
      setFlashcards(list);
      setActiveCardIdx(0);
      setShowFlashcardAnswer(false);
    } catch (e) {}
  };

  const loadQuizzes = async () => {
    try {
      const list = await api.getQuizzes();
      setQuizList(list);
    } catch (e) {}
  };

  const loadStudyPlan = async () => {
    try {
      const plan = await api.getActiveStudyPlan();
      setStudyPlan(plan);
    } catch (e) {}
  };

  // --- Action Handlers ---
  const handleAddSubject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newSubjName) return;
    try {
      await api.createSubject({ name: newSubjName, color: newSubjColor });
      setNewSubjName("");
      loadSubjects();
    } catch (e) {}
  };

  const handleDeleteSubject = async (id: number) => {
    try {
      await api.deleteSubject(id);
      loadSubjects();
      loadFiles();
    } catch (e) {}
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const uploadedFiles = e.target.files;
    if (!uploadedFiles || uploadedFiles.length === 0) return;
    
    setUploading(true);
    const fileToUpload = uploadedFiles[0];
    const formData = new FormData();
    formData.append("file", fileToUpload);
    if (selectedSubjId) {
      formData.append("subject_id", selectedSubjId.toString());
    }

    try {
      await api.uploadFile(formData);
      loadFiles();
      // Reload analytics in a bit to show update status
      setTimeout(loadFiles, 3000);
      setTimeout(loadDashboardAnalytics, 4000);
    } catch (err: any) {
      alert(err.message || "Failed to upload file");
    } finally {
      setUploading(false);
    }
  };

  const handleChatFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const uploadedFiles = e.target.files;
    if (!uploadedFiles || uploadedFiles.length === 0) return;
    
    const fileToUpload = uploadedFiles[0];
    setChatUploadStatus(`Uploading '${fileToUpload.name}'...`);
    
    const formData = new FormData();
    formData.append("file", fileToUpload);
    if (chatSelectedSubjId) {
      formData.append("subject_id", chatSelectedSubjId.toString());
    }
    
    try {
      const fileOut = await api.uploadFile(formData);
      setFiles((prev) => [...prev, fileOut]);
      loadFiles();
      loadDashboardAnalytics();
      
      // Poll file processing state
      setChatUploadStatus(`Processing '${fileToUpload.name}'...`);
      let isProcessed = false;
      for (let i = 0; i < 15; i++) {
        await new Promise((resolve) => setTimeout(resolve, 2000));
        const updatedFiles = await api.getFiles();
        const check = updatedFiles.find((f: any) => f.id === fileOut.id);
        if (check && check.status === "processed") {
          isProcessed = true;
          break;
        } else if (check && check.status === "failed") {
          throw new Error(check.error_message || "OCR / Text Extraction failed.");
        }
      }
      
      if (!isProcessed) {
        setChatUploadStatus("Processing timeout. Attachment added.");
        return;
      }
      
      setChatUploadStatus("Generating Summary...");
      
      // Auto create a discussion if none active
      let convId = activeConvId;
      if (!convId) {
        const newConv = await api.createConversation(`Summary: ${fileToUpload.name}`, chatSelectedSubjId || undefined);
        await loadConversations();
        convId = newConv.id;
        setActiveConvId(newConv.id);
      }
      if (!convId) {
        throw new Error("Failed to initialize conversation thread.");
      }
      
      // Submit summary query
      setChatUploadStatus("");
      setChatLoading(true);
      
      const summaryPrompt = `Please read and provide a structured, detailed study summary of this document: ${fileToUpload.name}. Break down key concepts and terms.`;
      
      const tempUserMsg = {
        id: Date.now(),
        sender: "user",
        content: `Provide a detailed summary of the uploaded document: ${fileToUpload.name}`,
        created_at: new Date().toISOString(),
        citations: []
      };
      setChatMessages((prev) => [...prev, tempUserMsg]);
      
      const res = await api.sendMessage(convId, {
        message: summaryPrompt,
        restrict_to_materials: true,
        file_ids: [fileOut.id],
        stream: false
      });
      setChatMessages((prev) => [...prev, res]);
      loadDashboardAnalytics();
    } catch (err: any) {
      alert(err.message || "Failed to upload or summarize document");
      setChatUploadStatus("");
    } finally {
      setChatLoading(false);
    }
  };

  const handleDeleteFile = async (id: number) => {
    try {
      await api.deleteFile(id);
      loadFiles();
      loadDashboardAnalytics();
    } catch (e) {}
  };

  // Chat Actions
  const selectConversation = async (id: number) => {
    setActiveConvId(id);
    setChatLoading(true);
    try {
      const history = await api.getMessages(id);
      setChatMessages(history);
    } catch (e) {} finally {
      setChatLoading(false);
    }
  };

  const handleCreateConv = async () => {
    try {
      const newConv = await api.createConversation("Study Chat Session", selectedSubjId || undefined);
      loadConversations();
      selectConversation(newConv.id);
    } catch (e) {}
  };

  const handleDeleteConv = async (id: number) => {
    try {
      await api.deleteConversation(id);
      if (activeConvId === id) {
        setActiveConvId(null);
        setChatMessages([]);
      }
      loadConversations();
    } catch (e) {}
  };

  const handleSendChatMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim() || !activeConvId) return;

    const userMessageText = chatInput;
    setChatInput("");
    setChatLoading(true);

    // Optimistically push User message
    const tempUserMsg = {
      id: Date.now(),
      sender: "user",
      content: userMessageText,
      created_at: new Date().toISOString(),
      citations: []
    };
    setChatMessages((prev) => [...prev, tempUserMsg]);

    try {
      const res = await api.sendMessage(activeConvId, {
        message: userMessageText,
        restrict_to_materials: restrictToDocs,
        file_ids: chatSelectedFileId ? [chatSelectedFileId] : undefined,
        stream: false
      });
      setChatMessages((prev) => [...prev, res]);
      loadDashboardAnalytics();
    } catch (err: any) {
      setChatMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          sender: "assistant",
          content: `Error: ${err.message || "Failed to get AI response"}`,
          created_at: new Date().toISOString(),
          citations: []
        }
      ]);
    } finally {
      setChatLoading(false);
    }
  };

  // Flashcards SM-2 rating
  const handleReviewFlashcard = async (rating: number) => {
    const filteredFlashcards = flashcards.filter(card => 
      !fcSelectedSubjId || card.subject_id === fcSelectedSubjId
    );
    if (filteredFlashcards.length === 0) return;
    const activeCard = filteredFlashcards[Math.min(activeCardIdx, filteredFlashcards.length - 1)];
    try {
      await api.reviewFlashcard(activeCard.id, rating);
      setShowFlashcardAnswer(false);
      if (activeCardIdx < filteredFlashcards.length - 1) {
        setActiveCardIdx((prev) => prev + 1);
      } else {
        alert("Awesome! You completed all pending flashcards for this round.");
        loadFlashcards();
        loadDashboardAnalytics();
        setActiveCardIdx(0);
      }
    } catch (e) {}
  };


  // Quiz creation and submit
  const handleGenerateQuiz = async (e: React.FormEvent) => {
    e.preventDefault();
    setGeneratingQuiz(true);
    try {
      const reqData: any = {
        title: quizGenTitle,
        difficulty: quizGenDifficulty,
        num_questions: quizGenSize,
        question_types: ["mcq", "true_false"]
      };
      if (quizGenSubj) {
        reqData.subject_id = quizGenSubj;
      }
      if (quizGenFile) {
        reqData.file_ids = [quizGenFile];
      }
      
      const resQuiz = await api.generateQuiz(reqData);
      loadQuizzes();
      startQuiz(resQuiz);
    } catch (err: any) {
      alert(err.message || "Failed to generate AI Quiz. Please make sure you uploaded study files.");
    } finally {
      setGeneratingQuiz(false);
    }
  };

  const startQuiz = (quiz: any) => {
    setActiveQuiz(quiz);
    setActiveQuizAnswers({});
    setQuizResults(null);
    setQuizTimer(0);
    const interval = setInterval(() => {
      setQuizTimer((prev) => prev + 1);
    }, 1000);
    setQuizTimerInterval(interval);
  };

  const handleQuizAnswerSelect = (questionId: number, option: string) => {
    setActiveQuizAnswers((prev) => ({
      ...prev,
      [questionId]: option
    }));
  };

  const handleQuizSubmit = async () => {
    if (!activeQuiz) return;
    clearInterval(quizTimerInterval);
    setQuizTimerInterval(null);

    const answersList = Object.entries(activeQuizAnswers).map(([qId, ans]) => ({
      question_id: parseInt(qId),
      user_answer: ans
    }));

    try {
      const res = await api.submitQuiz(activeQuiz.id, answersList, quizTimer);
      setQuizResults(res);
      loadQuizzes();
      loadDashboardAnalytics();
    } catch (e) {
      alert("Failed to submit quiz.");
    }
  };

  // Planner actions
  const handleGenerateStudyPlan = async (e: React.FormEvent) => {
    e.preventDefault();
    setGeneratingPlan(true);
    try {
      const chosenSubjIds = planGenSubjects.length > 0 ? planGenSubjects : subjects.map((s) => s.id);
      if (chosenSubjIds.length === 0) {
        alert("Please create at least one subject folder first.");
        return;
      }
      
      const today = new Date();
      const end = new Date();
      end.setDate(today.getDate() + planGenDays);

      await api.generateStudyPlan({
        title: "Dynamic Study Strategy Plan",
        start_date: today.toISOString(),
        end_date: end.toISOString(),
        daily_hours: planGenHours,
        subjects: chosenSubjIds
      });
      loadStudyPlan();
    } catch (e) {
      alert("Failed to generate plan.");
    } finally {
      setGeneratingPlan(false);
    }
  };

  const handleStartStudySession = async (subjId?: number) => {
    try {
      const session = await api.startStudySession(subjId, "Focused dashboard study session");
      setActiveSession(session);
    } catch (e) {}
  };

  const handleEndStudySession = async () => {
    if (!activeSession) return;
    try {
      await api.endStudySession(activeSession.id, "Session complete");
      setActiveSession(null);
      loadDashboardAnalytics();
    } catch (e) {}
  };

  const formatTimer = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  // --- Auth Render View ---
  if (!token) {
    return (
      <div className="relative min-h-screen flex items-center justify-center bg-radial from-slate-900 via-indigo-950 to-black overflow-hidden font-sans">
        {/* Animated background highlights */}
        <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-indigo-500/20 rounded-full blur-[120px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-violet-600/20 rounded-full blur-[120px]" />

        <div className="relative w-full max-w-md p-8 bg-slate-900/60 backdrop-blur-xl border border-slate-800 rounded-2xl shadow-2xl">
          {/* Brand header */}
          <div className="text-center mb-8">
            <div className="inline-flex p-3 bg-gradient-to-tr from-indigo-500 to-violet-600 rounded-xl shadow-lg shadow-indigo-500/30 mb-3">
              <Sparkles className="h-7 w-7 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-white tracking-tight">AI Study Assistant</h1>
            <p className="text-sm text-slate-400 mt-1">Your AI-Powered Study Engine</p>
          </div>

          <AnimatePresence mode="wait">
            {!showOtpModal ? (
              <motion.form
                key="auth-form"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                onSubmit={handleAuthSubmit}
                className="space-y-4"
              >
                {!isLogin && (
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">Full Name</label>
                    <input
                      type="text"
                      required
                      value={authName}
                      onChange={(e) => setAuthName(e.target.value)}
                      placeholder="Jane Doe"
                      className="w-full px-4 py-2.5 bg-slate-950/70 border border-slate-800 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
                    />
                  </div>
                )}

                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">Email Address</label>
                  <input
                    type="email"
                    required
                    value={authEmail}
                    onChange={(e) => setAuthEmail(e.target.value)}
                    placeholder="student@university.edu"
                    className="w-full px-4 py-2.5 bg-slate-950/70 border border-slate-800 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">Password</label>
                  <input
                    type="password"
                    required
                    value={authPassword}
                    onChange={(e) => setAuthPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full px-4 py-2.5 bg-slate-950/70 border border-slate-800 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
                  />
                </div>

                {authError && (
                  <p className="text-xs font-semibold text-rose-400 bg-rose-500/10 p-2.5 rounded border border-rose-500/20">{authError}</p>
                )}

                <button
                  type="submit"
                  disabled={authLoading}
                  className="w-full flex items-center justify-center py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white font-medium rounded-lg transition-colors cursor-pointer shadow-lg shadow-indigo-600/20"
                >
                  {authLoading ? <Loader2 className="h-5 w-5 animate-spin" /> : isLogin ? "Sign In" : "Register"}
                </button>

                <div className="relative my-6 text-center">
                  <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-slate-800"></div></div>
                  <span className="relative bg-slate-900/60 px-3 text-xs text-slate-500">Or continue with scaffolding</span>
                </div>

                <div id="google-signin-button-hidden" className="hidden"></div>
                <button
                  type="button"
                  onClick={handleGoogleLogin}
                  disabled={authLoading}
                  className="w-full flex items-center justify-center gap-2 py-2 bg-slate-950/70 border border-slate-800 hover:border-indigo-500 text-slate-300 hover:text-white rounded-lg transition-all cursor-pointer"
                >
                  <Lock className="h-4 w-4" />
                  OAuth / Google Demo Access
                </button>


                <p className="text-center text-xs text-slate-400 mt-4">
                  {isLogin ? "New to the platform?" : "Already have an account?"}{" "}
                  <button
                    type="button"
                    onClick={() => { setIsLogin(!isLogin); setAuthError(""); }}
                    className="text-indigo-400 hover:underline font-medium ml-1"
                  >
                    {isLogin ? "Create account" : "Sign In"}
                  </button>
                </p>
              </motion.form>
            ) : (
              <motion.form
                key="otp-form"
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                onSubmit={handleOtpVerify}
                className="space-y-4"
              >
                <div className="text-center bg-indigo-500/10 border border-indigo-500/20 p-4 rounded-lg mb-4">
                  <Flame className="h-6 w-6 text-indigo-400 mx-auto mb-2" />
                  <p className="text-xs text-slate-300">An OTP code has been generated. For this SaaS scaffolding execution, check the terminal backend logs output for the OTP digits.</p>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">Enter 6-Digit OTP Code</label>
                  <input
                    type="text"
                    required
                    value={otpCode}
                    onChange={(e) => setOtpCode(e.target.value)}
                    placeholder="123456"
                    className="w-full px-4 py-2.5 bg-slate-950/70 border border-slate-800 rounded-lg text-white placeholder-slate-500 text-center tracking-widest font-mono text-lg focus:outline-none focus:border-indigo-500"
                  />
                </div>

                {authError && (
                  <p className="text-xs font-semibold text-rose-400 bg-rose-500/10 p-2.5 rounded border border-rose-500/20">{authError}</p>
                )}

                <button
                  type="submit"
                  disabled={authLoading}
                  className="w-full flex items-center justify-center py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white font-medium rounded-lg transition-colors cursor-pointer"
                >
                  {authLoading ? <Loader2 className="h-5 w-5 animate-spin" /> : "Verify Code"}
                </button>
              </motion.form>
            )}
          </AnimatePresence>
        </div>
      </div>
    );
  }

  // --- Dashboard Tab View ---
  const renderDashboard = () => {
    return (
      <div className="space-y-6">
        {/* Welcome row */}
        <div className="flex flex-col md:flex-row md:items-center justify-between p-6 bg-gradient-to-tr from-indigo-900 to-indigo-950 border border-indigo-500/20 rounded-2xl shadow-xl">
          <div className="space-y-1">
            <h2 className="text-2xl font-bold text-white">Welcome back, {userProfile?.full_name || "Scholar"}!</h2>
            <p className="text-sm text-indigo-200">Consistency pays off. Check out your analytics and upcoming study planner.</p>
          </div>
          <div className="mt-4 md:mt-0 flex items-center gap-4 bg-indigo-950/40 px-4 py-2 border border-indigo-500/10 rounded-xl">
            <div className="flex items-center gap-2">
              <Flame className="h-5 w-5 text-orange-500 fill-orange-500" />
              <span className="text-sm font-bold text-white">{analytics.streak_days} Day Streak</span>
            </div>
            <div className="w-px h-6 bg-indigo-500/20" />
            <div className="flex items-center gap-2">
              <Clock className="h-5 w-5 text-indigo-400" />
              <span className="text-sm font-bold text-white">{analytics.time_studied_minutes}m Studied</span>
            </div>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-slate-900/60 p-4 border border-slate-800 rounded-xl flex items-center gap-4">
            <div className="p-3 bg-indigo-500/10 text-indigo-400 rounded-lg"><FileText className="h-6 w-6" /></div>
            <div>
              <p className="text-xs text-slate-400 font-medium">Uploaded Files</p>
              <p className="text-xl font-bold text-white">{analytics.files_uploaded}</p>
            </div>
          </div>
          <div className="bg-slate-900/60 p-4 border border-slate-800 rounded-xl flex items-center gap-4">
            <div className="p-3 bg-violet-500/10 text-violet-400 rounded-lg"><MessageSquare className="h-6 w-6" /></div>
            <div>
              <p className="text-xs text-slate-400 font-medium">AI Discussions</p>
              <p className="text-xl font-bold text-white">{analytics.ai_conversations}</p>
            </div>
          </div>
          <div className="bg-slate-900/60 p-4 border border-slate-800 rounded-xl flex items-center gap-4">
            <div className="p-3 bg-emerald-500/10 text-emerald-400 rounded-lg"><Award className="h-6 w-6" /></div>
            <div>
              <p className="text-xs text-slate-400 font-medium">Mastered Cards</p>
              <p className="text-xl font-bold text-white">{analytics.flashcards_mastered} / {analytics.flashcards_total}</p>
            </div>
          </div>
          <div className="bg-slate-900/60 p-4 border border-slate-800 rounded-xl flex items-center gap-4">
            <div className="p-3 bg-rose-500/10 text-rose-400 rounded-lg"><TrendingUp className="h-6 w-6" /></div>
            <div>
              <p className="text-xs text-slate-400 font-medium">Avg Quiz Percent</p>
              <p className="text-xl font-bold text-white">{analytics.quiz_average_percent}%</p>
            </div>
          </div>
        </div>

        {/* Content rows */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Progress Chart & Strength */}
          <div className="lg:col-span-2 space-y-6">
            {/* Custom SVG Progress Chart with Daily/Weekly/Monthly filter */}
            <div className="bg-slate-900/60 p-5 border border-slate-800 rounded-xl space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
                  {graphRange === "daily" ? "Daily Progress" : graphRange === "monthly" ? "Monthly Progress" : "Weekly Progress"} (Minutes studied)
                </h3>
                <div className="flex bg-slate-950 p-1 border border-slate-800 rounded-lg shrink-0">
                  {(["daily", "weekly", "monthly"] as const).map((range) => (
                    <button
                      key={range}
                      type="button"
                      onClick={() => setGraphRange(range)}
                      className={`px-3 py-1 text-[10px] font-bold rounded-md uppercase tracking-wider transition-colors cursor-pointer ${
                        graphRange === range 
                          ? "bg-indigo-600 text-white" 
                          : "text-slate-500 hover:text-slate-300"
                      }`}
                    >
                      {range}
                    </button>
                  ))}
                </div>
              </div>
              
              <div className="h-48 flex items-end justify-between px-4 pb-2 border-b border-slate-800">
                {(() => {
                  const chartData = graphRange === "daily" 
                    ? (analytics.daily_progress || []) 
                    : graphRange === "monthly" 
                    ? (analytics.monthly_progress || []) 
                    : (analytics.weekly_progress || []);
                  
                  if (chartData.length === 0) {
                    return <div className="w-full text-center text-xs text-slate-500 pb-10">No study sessions recorded yet. Start a session to track progress!</div>;
                  }

                  const maxMinutes = Math.max(...chartData.map((d: any) => d.minutes), 60);
                  return chartData.map((day: any, idx: number) => {
                    const heightPct = (day.minutes / maxMinutes) * 100;
                    return (
                      <div key={idx} className="flex flex-col items-center gap-2 flex-1">
                        <div className="text-[9px] font-semibold text-indigo-400">{day.minutes}m</div>
                        <div 
                          style={{ height: `${Math.max(4, heightPct)}%` }} 
                          className="w-6 sm:w-8 bg-gradient-to-t from-indigo-600 to-violet-500 rounded-t-sm shadow-lg shadow-indigo-500/10 transition-all duration-500 hover:from-indigo-400 hover:to-violet-400"
                        />
                        <div className="text-[10px] text-slate-500 font-medium truncate max-w-12">{day.day}</div>
                      </div>
                    );
                  });
                })()}
              </div>
            </div>

            {/* Strengths & Weaknesses */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-slate-900/60 p-5 border border-slate-800 rounded-xl space-y-3">
                <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wide flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-emerald-500" /> Key Strengths
                </h4>
                <div className="space-y-2">
                  {analytics.strong_subjects.length > 0 ? (
                    analytics.strong_subjects.map((sub: string, idx: number) => (
                      <div key={idx} className="p-2.5 bg-emerald-500/5 border border-emerald-500/10 rounded-lg animate-fade-in">
                        <span className="px-1.5 py-0.5 bg-emerald-500/10 text-emerald-400 rounded text-[9px] font-bold uppercase">{sub}</span>
                        <p className="text-[10px] text-slate-400 mt-1.5 leading-relaxed">Strong understanding. Keep using spaced-repetition flashcards to maintain long-term retention.</p>
                      </div>
                    ))
                  ) : (
                    <p className="text-xs text-slate-500 leading-relaxed">No key strengths identified yet. Complete and pass custom quizzes (score &ge; 70%) to highlight subjects.</p>
                  )}
                </div>
              </div>
              <div className="bg-slate-900/60 p-5 border border-slate-800 rounded-xl space-y-3">
                <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wide flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-rose-500" /> Needs Improvement
                </h4>
                <div className="space-y-2">
                  {analytics.weak_subjects.length > 0 ? (
                    analytics.weak_subjects.map((sub: string, idx: number) => (
                      <div key={idx} className="p-2.5 bg-rose-500/5 border border-rose-500/10 rounded-lg animate-fade-in">
                        <span className="px-1.5 py-0.5 bg-rose-500/10 text-rose-400 rounded text-[9px] font-bold uppercase">{sub}</span>
                        <p className="text-[10px] text-slate-400 mt-1.5 leading-relaxed">Lower quiz performance. Try asking the AI Chatbot to explain hard definitions, or generate custom quizzes for this subject.</p>
                      </div>
                    ))
                  ) : (
                    <p className="text-xs text-slate-500 leading-relaxed">No improvement spots detected yet. If you struggle with quiz questions, they will be logged here with reviews.</p>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Activity & Quick Action */}
          <div className="space-y-6">
            <div className="bg-slate-900/60 p-5 border border-slate-800 rounded-xl space-y-4">
              <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">Recent Activity</h3>
              <div className="space-y-4">
                {analytics.recent_activity.length > 0 ? (
                  analytics.recent_activity.map((act: any, idx: number) => (
                    <div key={idx} className="flex gap-3">
                      <div className={`w-1.5 h-1.5 rounded-full mt-2 shrink-0 ${act.type === "upload" ? "bg-indigo-400" : "bg-violet-400"}`} />
                      <div className="space-y-0.5">
                        <p className="text-xs text-slate-300 font-medium">{act.message}</p>
                        <p className="text-[10px] text-slate-500">{new Date(act.time).toLocaleDateString()}</p>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-slate-500">No recent activity logs available. Get started by uploading a file.</p>
                )}
              </div>
            </div>

            {/* Quick Session Start */}
            <div className="bg-gradient-to-tr from-violet-950 to-indigo-950 p-5 border border-indigo-500/20 rounded-xl text-center space-y-4">
              <h3 className="text-sm font-bold text-white">Log Live Study Time</h3>
              <p className="text-xs text-indigo-200">Start the system timer while studying to build your consecutive day streak.</p>
              
              {!activeSession ? (
                <button
                  onClick={() => handleStartStudySession()}
                  className="w-full flex items-center justify-center gap-2 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold cursor-pointer transition-colors shadow-lg shadow-indigo-500/20"
                >
                  <Play className="h-4 w-4" /> Start Study Timer
                </button>
              ) : (
                <div className="space-y-3">
                  <div className="text-2xl font-mono font-bold text-white tracking-widest">{formatTimer(sessionDuration)}</div>
                  <button
                    onClick={handleEndStudySession}
                    className="w-full flex items-center justify-center gap-2 py-2 bg-rose-600 hover:bg-rose-500 text-white rounded-lg text-xs font-semibold cursor-pointer transition-colors"
                  >
                    <Square className="h-4 w-4" /> End & Log Session
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  };

  // --- Materials Tab View ---
  const renderMaterials = () => {
    // If selectedSubjId is set, render the detail page for that subject folder
    if (selectedSubjId) {
      const sub = subjects.find(s => s.id === selectedSubjId);
      const subFiles = files.filter(f => f.subject_id === selectedSubjId);
      return (
        <div className="space-y-6">
          {/* Header toolbar */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={() => setSelectedSubjId(null)}
                className="px-3.5 py-1.5 bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded-lg text-xs font-semibold text-slate-300 transition-colors cursor-pointer"
              >
                &larr; Back to Subjects
              </button>
              <div>
                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                  <Folder style={{ color: sub?.color || "#6366f1" }} className="h-5 w-5 fill-current" />
                  {sub?.name || "Subject Materials"}
                </h2>
                <p className="text-xs text-slate-400 mt-1">{sub?.description || "Manage study files and chapters inside this subject."}</p>
              </div>
            </div>

            {/* Upload Button scoping to subject */}
            <div className="flex items-center gap-3">
              <label className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold cursor-pointer transition-colors shadow-lg shadow-indigo-500/10">
                {uploading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <UploadCloud className="h-4 w-4" />
                )}
                {uploading ? "Ingesting Chapter..." : "Upload Chapter / Note"}
                <input type="file" onChange={handleFileUpload} disabled={uploading} className="hidden" />
              </label>
            </div>
          </div>

          {/* Subject Chapters/Documents list */}
          <div className="bg-slate-900/60 p-5 border border-slate-800 rounded-xl space-y-4">
            <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2">
              <FileText className="h-4 w-4 text-indigo-400" /> Chapters & Notes List
            </h3>
            
            {subFiles.length === 0 ? (
              <div className="text-center py-12 border border-dashed border-slate-800 rounded-xl space-y-3">
                <FileText className="h-10 w-10 text-slate-700 mx-auto animate-pulse" />
                <p className="text-xs text-slate-500 max-w-xs mx-auto leading-relaxed">No chapters or lecture notes uploaded to this folder yet. Click upload above to populate this subject.</p>
              </div>
            ) : (
              <div className="divide-y divide-slate-800">
                {subFiles.map((file: any) => (
                  <div key={file.id} className="py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div className="flex items-center gap-3 min-w-0">
                      <div className="p-2.5 bg-slate-950 border border-slate-800 rounded-lg shrink-0">
                        <FileText className="h-5 w-5 text-indigo-400" />
                      </div>
                      <div className="min-w-0">
                        <p className="text-sm font-semibold text-white truncate max-w-md">{file.name}</p>
                        <div className="flex flex-wrap items-center gap-3 text-[10px] text-slate-500 mt-1 font-medium">
                          <span>{(file.file_size / (1024 * 1024)).toFixed(2)} MB</span>
                          <span>•</span>
                          <span className={`px-1.5 py-0.5 rounded text-[8px] font-bold ${
                            file.status === "processed" 
                              ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" 
                              : file.status === "failed" 
                              ? "bg-rose-500/10 text-rose-400 border border-rose-500/20" 
                              : "bg-orange-500/10 text-orange-400 border border-orange-500/20"
                          }`}>
                            {file.status.toUpperCase()}
                          </span>
                          {file.error_message && (
                            <span className="text-rose-400 italic">Error: {file.error_message}</span>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-2 shrink-0">
                      <button
                        type="button"
                        onClick={() => {
                          setChatSelectedSubjId(selectedSubjId);
                          setChatSelectedFileId(file.id);
                          setRestrictToDocs(true);
                          setActiveTab("chat");
                          handleCreateConv();
                        }}
                        disabled={file.status !== "processed"}
                        className="px-2.5 py-1.5 bg-indigo-600/10 border border-indigo-500/20 text-indigo-300 hover:bg-indigo-600/20 rounded text-[11px] font-bold cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                      >
                        Ask AI
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          setFcSelectedSubjId(selectedSubjId);
                          setFcSelectedFileId(file.id);
                          setActiveTab("flashcards");
                        }}
                        disabled={file.status !== "processed"}
                        className="px-2.5 py-1.5 bg-emerald-600/10 border border-emerald-500/20 text-emerald-300 hover:bg-emerald-600/20 rounded text-[11px] font-bold cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                      >
                        Flashcards
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          setQuizGenSubj(selectedSubjId);
                          setQuizGenFile(file.id);
                          setActiveTab("quiz");
                        }}
                        disabled={file.status !== "processed"}
                        className="px-2.5 py-1.5 bg-violet-600/10 border border-violet-500/20 text-violet-300 hover:bg-violet-600/20 rounded text-[11px] font-bold cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                      >
                        Take Quiz
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDeleteFile(file.id)}
                        className="p-1.5 hover:bg-rose-500/10 border border-transparent hover:border-rose-500/20 text-slate-500 hover:text-rose-400 rounded-lg transition-colors cursor-pointer"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      );
    }

    return (
      <div className="space-y-6">
        {/* Header toolbar */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <h2 className="text-xl font-bold text-white">Study Materials</h2>
            <p className="text-sm text-slate-400">Organize slides, lecture files, and handwritten notes into subjects.</p>
          </div>
          {/* Upload Button */}
          <div className="flex items-center gap-3">
            <label className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold cursor-pointer transition-colors shadow-lg shadow-indigo-500/10">
              {uploading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <UploadCloud className="h-4 w-4" />
              )}
              {uploading ? "Ingesting..." : "Upload Material"}
              <input type="file" onChange={handleFileUpload} disabled={uploading} className="hidden" />
            </label>
          </div>
        </div>

        {/* Subjects list row */}
        <div className="bg-slate-900/60 p-5 border border-slate-800 rounded-xl space-y-4">
          <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2">
            <Folder className="h-4 w-4 text-indigo-400" /> Subject Folders (Click to open)
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
            {/* Create folder */}
            <form onSubmit={handleAddSubject} className="flex flex-col justify-between p-4 border border-slate-800 border-dashed rounded-lg space-y-3">
              <input
                type="text"
                required
                value={newSubjName}
                onChange={(e) => setNewSubjName(e.target.value)}
                placeholder="New Subject..."
                className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded text-xs text-white placeholder-slate-500 focus:outline-none"
              />
              <div className="flex items-center justify-between">
                <input
                  type="color"
                  value={newSubjColor}
                  onChange={(e) => setNewSubjColor(e.target.value)}
                  className="w-7 h-7 rounded border border-slate-800 cursor-pointer bg-transparent"
                />
                <button type="submit" className="flex items-center gap-1 px-3 py-1.5 bg-indigo-600 text-white text-xs font-semibold rounded cursor-pointer hover:bg-indigo-500">
                  <Plus className="h-3 w-3" /> Add
                </button>
              </div>
            </form>

            {/* Folder list */}
            {subjects.map((sub: any) => {
              const fileCount = files.filter((f) => f.subject_id === sub.id).length;
              return (
                <div
                  key={sub.id}
                  onClick={() => setSelectedSubjId(sub.id)}
                  style={{ borderLeftColor: sub.color, borderLeftWidth: "4px" }}
                  className="p-4 bg-slate-950 border border-slate-800 rounded-lg cursor-pointer transition-all flex flex-col justify-between relative group hover:border-slate-700 hover:ring-2 hover:ring-indigo-500/20"
                >
                  <button
                    type="button"
                    onClick={(e) => { e.stopPropagation(); handleDeleteSubject(sub.id); }}
                    className="absolute top-2 right-2 text-slate-500 hover:text-rose-400 opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                  <p className="text-sm font-bold text-white leading-tight mt-1">{sub.name}</p>
                  <p className="text-xs text-slate-500 mt-4 font-medium">{fileCount} Materials</p>
                </div>
              );
            })}
          </div>
        </div>

        {/* Files list */}
        <div className="bg-slate-900/60 p-5 border border-slate-800 rounded-xl space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-2">
              <FileText className="h-4 w-4 text-indigo-400" /> All Study Materials
            </h3>
          </div>

          <div className="divide-y divide-slate-800">
            {files.map((file: any) => (
              <div key={file.id} className="py-3.5 flex items-center justify-between gap-4">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="p-2 bg-slate-950 border border-slate-800 rounded text-indigo-400 shrink-0">
                    <FileText className="h-5 w-5" />
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-white truncate max-w-md">{file.name}</p>
                    <div className="flex items-center gap-3 text-xs text-slate-500 mt-1 font-medium">
                      <span>{(file.file_size / (1024 * 1024)).toFixed(2)} MB</span>
                      <span>•</span>
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${file.status === "processed" ? "bg-emerald-500/10 text-emerald-400" : file.status === "failed" ? "bg-rose-500/10 text-rose-400" : "bg-orange-500/10 text-orange-400"}`}>
                        {file.status.toUpperCase()}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <select
                    value={file.subject_id || ""}
                    onChange={async (e) => {
                      const val = e.target.value ? parseInt(e.target.value) : null;
                      try {
                        await api.assignFileToSubject(file.id, val);
                        loadFiles();
                        loadDashboardAnalytics();
                      } catch (err) {
                        alert("Failed to assign file to subject folder.");
                      }
                    }}
                    className="bg-slate-900 border border-slate-800 rounded px-2.5 py-1 text-[11px] text-slate-300 focus:outline-none"
                  >
                    <option value="">Unassigned</option>
                    {subjects.map((sub: any) => (
                      <option key={sub.id} value={sub.id}>{sub.name}</option>
                    ))}
                  </select>

                  <button
                    onClick={() => handleDeleteFile(file.id)}
                    className="p-2 text-slate-400 hover:text-rose-400 transition-colors cursor-pointer"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))}

            {files.length === 0 && (
              <div className="text-center py-8 space-y-2">
                <UploadCloud className="h-8 w-8 text-slate-600 mx-auto" />
                <p className="text-xs text-slate-500">No study materials found. Create a subject folder and upload notes to begin.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  // --- AI Chat Tab View ---
  const renderChat = () => {
    const activeConv = conversations.find((c) => c.id === activeConvId);

    return (
      <div className="h-[calc(100vh-140px)] flex border border-slate-800 rounded-2xl overflow-hidden bg-slate-950">
        {/* Sidebar threads */}
        <div className="w-64 border-r border-slate-800 bg-slate-900/30 flex flex-col">
          <div className="p-4 border-b border-slate-800 space-y-3">
            {/* Subject Selector for New Thread */}
            <div className="space-y-1">
              <label className="text-[9px] text-slate-500 uppercase font-bold">New Thread Subject</label>
              <select
                value={chatSubjectFilter || ""}
                onChange={(e) => setChatSubjectFilter(e.target.value ? parseInt(e.target.value) : null)}
                className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-white"
              >
                <option value="">Choose Subject Folder...</option>
                {subjects.map((sub) => (
                  <option key={sub.id} value={sub.id}>{sub.name}</option>
                ))}
              </select>
            </div>
            
            <button
              onClick={() => handleCreateConv()}
              className="w-full flex items-center justify-center gap-2 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold cursor-pointer transition-colors shadow-lg shadow-indigo-500/10"
            >
              <Plus className="h-4 w-4" /> New Discussion
            </button>
          </div>
          
          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {conversations.map((conv: any) => (
              <div
                key={conv.id}
                onClick={() => selectConversation(conv.id)}
                className={`p-3 rounded-lg flex items-center justify-between group cursor-pointer transition-colors ${activeConvId === conv.id ? "bg-indigo-600/10 border border-indigo-500/20 text-indigo-300" : "hover:bg-slate-900 text-slate-400 hover:text-slate-200"}`}
              >
                <div className="flex items-center gap-2 min-w-0">
                  <MessageSquare className="h-4 w-4 shrink-0" />
                  <p className="text-xs font-semibold truncate leading-none">{conv.title}</p>
                </div>
                <button
                  onClick={(e) => { e.stopPropagation(); handleDeleteConv(conv.id); }}
                  className="text-slate-500 hover:text-rose-400 opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Chat view */}
        <div className="flex-1 flex flex-col bg-slate-950">
          {/* Header */}
          <div className="p-4 border-b border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h3 className="text-sm font-bold text-white leading-tight">{activeConv?.title || "AI Tutor"}</h3>
              <p className="text-[10px] text-slate-500 mt-0.5">Active thread RAG model enabled</p>
            </div>
            
            <div className="flex items-center gap-3">
              {/* Scope to Folder/Subject */}
              <select
                value={chatSelectedSubjId || ""}
                onChange={(e) => {
                  const val = e.target.value ? parseInt(e.target.value) : null;
                  setChatSelectedSubjId(val);
                  setChatSelectedFileId(null);
                }}
                className="bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-[11px] text-white animate-fade-in"
              >
                <option value="">All Subjects Folder</option>
                {subjects.map((sub) => (
                  <option key={sub.id} value={sub.id}>{sub.name}</option>
                ))}
              </select>

              {/* Scope to specific file (chapter) */}
              <select
                value={chatSelectedFileId || ""}
                onChange={(e) => setChatSelectedFileId(e.target.value ? parseInt(e.target.value) : null)}
                className="bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-[11px] text-white max-w-44 animate-fade-in"
              >
                <option value="">All Chapters</option>
                {files
                  .filter((f) => !chatSelectedSubjId || f.subject_id === chatSelectedSubjId)
                  .map((file) => (
                    <option key={file.id} value={file.id}>{file.name}</option>
                  ))}
              </select>

              <label className="flex items-center gap-2 cursor-pointer bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-lg text-xs text-slate-300 font-semibold select-none shrink-0 hover:border-slate-700">
                <input 
                  type="checkbox" 
                  checked={restrictToDocs} 
                  onChange={(e) => setRestrictToDocs(e.target.checked)} 
                  className="accent-indigo-500"
                />
                Search Notes
              </label>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {chatMessages.map((msg: any) => (
              <div
                key={msg.id}
                className={`flex gap-3 max-w-3xl ${msg.sender === "user" ? "ml-auto flex-row-reverse" : ""}`}
              >
                <div className={`p-3 rounded-xl border text-sm leading-relaxed ${msg.sender === "user" ? "bg-indigo-600/10 border-indigo-500/20 text-indigo-100" : "bg-slate-900/60 border-slate-800 text-slate-200"}`}>
                  <div className="whitespace-pre-line font-sans">{msg.content}</div>

                  {msg.citations && msg.citations.length > 0 && (
                    <div className="mt-3 border-t border-slate-800 pt-2 space-y-1">
                      <p className="text-[10px] text-slate-500 uppercase tracking-wider font-bold">Retrieved Citations:</p>
                      {msg.citations.map((cit: any, idx: number) => (
                        <div key={idx} className="text-xs text-slate-400 bg-slate-950/60 p-2 border border-slate-800 rounded mt-1">
                          <span className="font-semibold text-indigo-400">{cit.file_name} (Page {cit.page_number})</span>
                          <p className="text-[11px] text-slate-500 italic mt-0.5">"{cit.snippet}"</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {chatLoading && (
              <div className="flex gap-2 items-center text-slate-500 text-xs">
                <Loader2 className="h-4 w-4 animate-spin text-indigo-400" />
                <span>AI is searching vector storage and generating answer...</span>
              </div>
            )}
            
            {chatMessages.length === 0 && (
              <div className="text-center py-20 space-y-2">
                <Sparkles className="h-8 w-8 text-slate-700 mx-auto" />
                <p className="text-xs text-slate-500">Start the conversation by asking a question regarding your notes.</p>
              </div>
            )}
            
            <div ref={chatBottomRef} />
          </div>

          {/* Chat upload status bar */}
          {chatUploadStatus && (
            <div className="px-4 py-2 bg-indigo-950/40 border-t border-slate-800/40 text-xs text-indigo-300 font-bold flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin shrink-0 text-indigo-400" />
              <span>{chatUploadStatus}</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSendChatMessage} className="p-4 border-t border-slate-800 bg-slate-900/30 flex gap-2 items-center">
            {/* Paperclip attachment option */}
            <label className="p-2.5 hover:bg-slate-800 text-slate-400 hover:text-white rounded-lg cursor-pointer transition-colors border border-transparent hover:border-slate-700 shrink-0">
              <Paperclip className="h-4 w-4" />
              <input type="file" onChange={handleChatFileUpload} className="hidden" />
            </label>

            <input
              type="text"
              required
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              placeholder={chatUploadStatus ? "Please wait..." : "Ask anything about the study slides..."}
              disabled={!!chatUploadStatus}
              className="flex-1 px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-indigo-500 disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={chatLoading || !!chatUploadStatus}
              className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg cursor-pointer transition-colors shadow-lg shadow-indigo-600/20 disabled:opacity-50"
            >
              Ask AI
            </button>
          </form>
        </div>
      </div>
    );
  };

  // --- Flashcards Tab View ---
  const renderFlashcards = () => {
    const filteredFlashcards = flashcards.filter(card => 
      !fcSelectedSubjId || card.subject_id === fcSelectedSubjId
    );
    const activeCard = filteredFlashcards.length > 0
      ? filteredFlashcards[Math.min(activeCardIdx, filteredFlashcards.length - 1)]
      : null;



    return (
      <div className="space-y-6 max-w-xl mx-auto">
        <div className="space-y-1 text-center">
          <h2 className="text-xl font-bold text-white">Active Flashcards</h2>
          <p className="text-sm text-slate-400">Master terminology and equations using spaced repetition.</p>
        </div>

        {/* Generate card quick select */}
        <div className="bg-slate-900/60 p-5 border border-slate-800 rounded-xl space-y-4 animate-fade-in">
          <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider">Generate New Flashcards</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-[10px] text-slate-500 uppercase font-bold">Select Subject</label>
              <select
                value={fcSelectedSubjId || ""}
                onChange={(e) => {
                  const val = e.target.value ? parseInt(e.target.value) : null;
                  setFcSelectedSubjId(val);
                  setFcSelectedFileId(null);
                }}
                className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500"
              >
                <option value="">Choose Subject Folder...</option>
                {subjects.map((sub) => (
                  <option key={sub.id} value={sub.id}>{sub.name}</option>
                ))}
              </select>
            </div>
            
            <div className="space-y-1">
              <label className="text-[10px] text-slate-500 uppercase font-bold">Select Document</label>
              <select
                value={fcSelectedFileId || ""}
                onChange={(e) => setFcSelectedFileId(e.target.value ? parseInt(e.target.value) : null)}
                className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500"
              >
                <option value="">Choose Chapter / Note...</option>
                {files.map((file) => {
                  const subj = subjects.find(s => s.id === file.subject_id);
                  return (
                    <option key={file.id} value={file.id}>
                      {file.name} {subj ? `(${subj.name})` : ""}
                    </option>
                  );
                })}
              </select>
            </div>
          </div>
          
          <button
            onClick={async () => {
              if (!fcSelectedFileId) {
                alert("Please select a specific document / chapter to generate flashcards.");
                return;
              }
              try {
                alert("AI is reading and extracting concepts for flashcards. This may take 5-10 seconds...");
                await api.generateFlashcards(fcSelectedFileId, 5);
                await loadFlashcards();
                loadDashboardAnalytics();
                alert("Successfully generated 5 smart flashcards!");
              } catch (e) {
                alert("Failed to generate flashcards. Please make sure the document has valid content.");
              }
            }}
            className="w-full flex items-center justify-center py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold rounded-lg cursor-pointer transition-colors shadow-lg shadow-indigo-600/20"
          >
            Generate 5 AI Flashcards
          </button>
          
          {filteredFlashcards.length > 0 && (
            <button
              onClick={async () => {
                if (confirm("Are you sure you want to clear all flashcards for this subject? This will reset the deck to 0.")) {
                  try {
                    await api.clearFlashcards(fcSelectedSubjId || undefined);
                    await loadFlashcards();
                    setActiveCardIdx(0);
                    alert("Subject deck reset to 0 cards!");
                  } catch (e) {
                    alert("Failed to clear deck.");
                  }
                }
              }}
              className="w-full flex items-center justify-center py-2 border border-rose-500/30 hover:border-rose-500 text-rose-400 text-xs font-bold rounded-lg cursor-pointer transition-colors mt-2"
            >
              Clear Subject Deck (Reset to 0)
            </button>
          )}
        </div>
 
        {activeCard ? (
          <div className="space-y-6">
            <div className="text-center text-xs text-slate-500 font-semibold">
              Flashcard {Math.min(activeCardIdx, filteredFlashcards.length - 1) + 1} of {filteredFlashcards.length}
            </div>
 
            {/* 3D Stack Effect */}
            <div className="relative group select-none">
              {/* Stack layer 2 */}
              <div className="absolute inset-0 bg-slate-900 border border-slate-800 translate-y-3.5 scale-[0.95] rounded-2xl -z-20 opacity-60 transition-transform duration-300 group-hover:translate-y-4 shadow-lg"></div>
              {/* Stack layer 1 */}
              <div className="absolute inset-0 bg-slate-800/80 border border-slate-700/50 translate-y-1.5 scale-[0.975] rounded-2xl -z-10 opacity-80 transition-transform duration-300 group-hover:translate-y-2 shadow-md"></div>
              
              {/* Flashcard container */}
              <div className="min-h-64 flex flex-col p-0 bg-white border border-slate-200 rounded-2xl shadow-xl relative overflow-hidden transition-all duration-300 hover:border-indigo-400 hover:shadow-indigo-500/5">
                {/* Top Banner Header (NON-CLICKABLE) */}
                <div className={`py-3 px-4 text-center text-[11px] font-bold text-white uppercase tracking-wider flex justify-between items-center ${!showFlashcardAnswer ? 'bg-indigo-600' : 'bg-emerald-600'}`}>
                  <span>{!showFlashcardAnswer ? 'Recall Question' : 'Correct Answer'}</span>
                  <div className="flex items-center gap-2">
                    <span className="px-1.5 py-0.5 bg-white/20 text-[9px] text-white font-bold uppercase rounded">
                      {activeCard.topic || "Topic"}
                    </span>
                    <button
                      type="button"
                      onClick={async () => {
                        if (confirm("Are you sure you want to delete this flashcard?")) {
                          try {
                            await api.deleteFlashcard(activeCard.id);
                            
                            // Remove from local list instantly for immediate UI update!
                            const updatedList = flashcards.filter(c => c.id !== activeCard.id);
                            setFlashcards(updatedList);
                            
                            // Adjust active card index cleanly
                            const newFilteredLength = updatedList.filter(card => 
                              !fcSelectedSubjId || card.subject_id === fcSelectedSubjId
                            ).length;
                            
                            if (activeCardIdx >= newFilteredLength && activeCardIdx > 0) {
                              setActiveCardIdx(newFilteredLength - 1);
                            }
                            setShowFlashcardAnswer(false);
                            loadDashboardAnalytics();
                          } catch (err) {
                            alert("Failed to delete flashcard.");
                          }
                        }
                      }}
                      className="p-1 text-white/70 hover:text-white transition-colors cursor-pointer"
                      title="Delete Flashcard"
                    >
                      <Trash2 className="h-3.5 w-3.5 pointer-events-none" />
                    </button>
                  </div>
                </div>

                {/* Clickable Card Body */}
                <div 
                  onClick={() => setShowFlashcardAnswer(!showFlashcardAnswer)}
                  className="flex-1 flex flex-col justify-center items-center p-8 text-center min-h-[180px] cursor-pointer hover:bg-slate-50/50 transition-colors"
                >
                  {!showFlashcardAnswer ? (
                    <div className="space-y-4">
                      <p className="text-base font-bold text-slate-800 leading-snug">{activeCard.front}</p>
                      <span className="inline-flex text-[10px] text-indigo-600 font-bold uppercase tracking-wider group-hover:underline">Click to Flip card</span>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      <p className="text-sm font-semibold text-slate-700 leading-relaxed">{activeCard.back}</p>
                      <span className="inline-flex text-[10px] text-emerald-600 font-bold uppercase tracking-wider">Click to see Question</span>
                    </div>
                  )}
                </div>
              </div>
            </div>


            {/* SM-2 Review Ratings */}
            {showFlashcardAnswer && (
              <div className="bg-slate-900/60 p-4 border border-slate-800 rounded-xl space-y-3">
                <p className="text-xs text-center text-slate-300 font-semibold">How well did you recall this answer?</p>
                <div className="grid grid-cols-6 gap-2">
                  {[0, 1, 2, 3, 4, 5].map((val) => (
                    <button
                      key={val}
                      onClick={() => handleReviewFlashcard(val)}
                      className="py-1.5 bg-slate-950 border border-slate-800 hover:border-indigo-500 text-slate-200 hover:text-white rounded text-xs font-bold cursor-pointer transition-colors"
                    >
                      {val}
                    </button>
                  ))}
                </div>
                <div className="flex justify-between text-[9px] text-slate-500 font-bold uppercase tracking-wider px-1">
                  <span>Forgot</span>
                  <span>Perfect</span>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="text-center py-20 bg-slate-900/30 border border-slate-800 border-dashed rounded-xl space-y-3">
            <CheckCircle className="h-8 w-8 text-emerald-500/80 mx-auto" />
            <p className="text-xs text-slate-500 max-w-xs mx-auto leading-relaxed">No due flashcards found. Create flashcards from your uploaded files to build study memories.</p>
          </div>
        )}
      </div>
    );
  };

  // --- Quiz Tab View ---
  const renderQuiz = () => {
    if (activeQuiz) {
      const isCompleted = activeQuiz.status === "completed" || quizResults !== null;
      const displayQuiz = quizResults || activeQuiz;

      return (
        <div className="space-y-6 max-w-xl mx-auto">
          {/* Quiz running header */}
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <h2 className="text-lg font-bold text-white">{displayQuiz.title}</h2>
              <p className="text-xs text-slate-400 mt-0.5">AI Generated evaluation</p>
            </div>
            {!isCompleted ? (
              <div className="text-sm font-mono font-bold text-indigo-400 flex items-center gap-1.5">
                <Clock className="h-4 w-4" /> {formatTimer(quizTimer)}
              </div>
            ) : (
              <div className="text-sm font-bold text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded">
                Score: {displayQuiz.score} / {displayQuiz.max_score}
              </div>
            )}
          </div>

          {/* Question List */}
          <div className="space-y-4">
            {(isCompleted ? displayQuiz.results : displayQuiz.questions).map((q: any, idx: number) => (
              <div key={q.id} className="bg-slate-900/60 p-5 border border-slate-800 rounded-xl space-y-3">
                <div className="text-xs text-indigo-400 font-bold uppercase tracking-wider">Question {idx + 1}</div>
                <p className="text-sm font-bold text-white leading-snug">{q.question_text}</p>

                {/* MCQ Options */}
                {q.options ? (
                  <div className="grid grid-cols-1 gap-2.5 pt-2">
                    {q.options.map((opt: string, oIdx: number) => {
                      const isSelected = activeQuizAnswers[q.id] === opt || q.user_answer === opt;
                      const isCorrect = q.correct_answer === opt;
                      
                      let btnStyle = "bg-slate-950 border-slate-800 text-slate-300 hover:border-slate-700";
                      if (!isCompleted) {
                        if (isSelected) btnStyle = "bg-indigo-600/20 border-indigo-500 text-indigo-300";
                      } else {
                        if (isCorrect) btnStyle = "bg-emerald-500/20 border-emerald-500 text-emerald-300";
                        else if (isSelected) btnStyle = "bg-rose-500/20 border-rose-500 text-rose-300";
                      }

                      return (
                        <button
                          key={oIdx}
                          onClick={() => !isCompleted && handleQuizAnswerSelect(q.id, opt)}
                          disabled={isCompleted}
                          className={`w-full text-left px-4 py-2.5 border rounded-lg text-xs font-semibold transition-all cursor-pointer ${btnStyle}`}
                        >
                          {opt}
                        </button>
                      );
                    })}
                  </div>
                ) : (
                  // Free text input for non-MCQ
                  <div className="pt-2">
                    <input
                      type="text"
                      disabled={isCompleted}
                      value={activeQuizAnswers[q.id] || q.user_answer || ""}
                      onChange={(e) => handleQuizAnswerSelect(q.id, e.target.value)}
                      placeholder="Type your answer..."
                      className="w-full px-4 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none"
                    />
                  </div>
                )}

                {/* Explanation block if completed */}
                {isCompleted && q.explanation && (
                  <div className="mt-3 bg-slate-950 p-3 border border-slate-800 rounded text-xs space-y-1">
                    <div className="font-bold text-slate-400 uppercase tracking-wider text-[10px]">Explanation:</div>
                    <p className="text-slate-300 leading-relaxed">{q.explanation}</p>
                    {q.feedback && <p className="text-indigo-400 font-semibold mt-1">Feedback: {q.feedback}</p>}
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Submit/Return buttons */}
          {!isCompleted ? (
            <button
              onClick={handleQuizSubmit}
              className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold rounded-lg cursor-pointer transition-colors shadow-lg shadow-indigo-600/20"
            >
              Submit Quiz Solutions
            </button>
          ) : (
            <button
              onClick={() => setActiveQuiz(null)}
              className="w-full py-2.5 bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 text-xs font-bold rounded-lg cursor-pointer transition-colors"
            >
              Back to Quizzes list
            </button>
          )}
        </div>
      );
    }

    return (
      <div className="space-y-6 max-w-xl mx-auto">
        <div className="space-y-1 text-center">
          <h2 className="text-xl font-bold text-white">AI Quiz Generator</h2>
          <p className="text-sm text-slate-400">Generate tests to review and lock concepts in memory.</p>
        </div>

        {/* Generate Panel */}
        <form onSubmit={handleGenerateQuiz} className="bg-slate-900/60 p-5 border border-slate-800 rounded-xl space-y-4">
          <div className="space-y-1.5">
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">Quiz Title</label>
            <input
              type="text"
              required
              value={quizGenTitle}
              onChange={(e) => setQuizGenTitle(e.target.value)}
              placeholder="e.g. Weekly Chemistry Review"
              className="w-full px-4 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="space-y-1.5">
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">Subject Folder</label>
              <select
                value={quizGenSubj || ""}
                onChange={(e) => {
                  const val = e.target.value ? parseInt(e.target.value) : null;
                  setQuizGenSubj(val);
                  setQuizGenFile(null);
                }}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-300 focus:outline-none focus:border-indigo-500"
              >
                <option value="">All Subjects</option>
                {subjects.map((s) => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </select>
            </div>
            
            <div className="space-y-1.5">
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">Document / Chapter</label>
              <select
                value={quizGenFile || ""}
                onChange={(e) => setQuizGenFile(e.target.value ? parseInt(e.target.value) : null)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-300 focus:outline-none focus:border-indigo-500 animate-fade-in"
              >
                <option value="">All Documents</option>
                {files
                  .filter((f) => !quizGenSubj || f.subject_id === quizGenSubj)
                  .map((file) => (
                    <option key={file.id} value={file.id}>{file.name}</option>
                  ))}
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">Difficulty</label>
              <select
                value={quizGenDifficulty}
                onChange={(e) => setQuizGenDifficulty(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-300 focus:outline-none focus:border-indigo-500"
              >
                <option value="easy">Easy</option>
                <option value="medium">Medium</option>
                <option value="hard">Hard</option>
              </select>
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">Number of Questions: {quizGenSize}</label>
            <input
              type="range"
              min="3"
              max="15"
              value={quizGenSize}
              onChange={(e) => setQuizGenSize(parseInt(e.target.value))}
              className="w-full accent-indigo-500 bg-slate-950 border border-slate-800 rounded"
            />
          </div>

          <button
            type="submit"
            disabled={generatingQuiz}
            className="w-full flex items-center justify-center gap-2 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold rounded-lg cursor-pointer transition-colors shadow-lg shadow-indigo-600/20"
          >
            {generatingQuiz ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
            {generatingQuiz ? "AI Generating Quiz Questions..." : "Generate AI Practice Test"}
          </button>
        </form>

        {/* Quiz list history */}
        <div className="bg-slate-900/60 p-5 border border-slate-800 rounded-xl space-y-4">
          <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">Quiz History</h3>
          <div className="divide-y divide-slate-800">
            {quizList.map((q: any) => (
              <div key={q.id} className="py-3 flex items-center justify-between">
                <div>
                  <p className="text-xs font-bold text-white">{q.title}</p>
                  <p className="text-[10px] text-slate-500 mt-1 uppercase font-semibold">
                    {q.difficulty} • {q.max_score} Questions • {q.status}
                  </p>
                </div>
                <div>
                  {q.status === "completed" ? (
                    <button
                      onClick={() => startQuiz(q)}
                      className="px-3 py-1 bg-slate-950 border border-slate-800 hover:border-indigo-500 text-slate-300 hover:text-white rounded text-xs font-bold cursor-pointer transition-colors"
                    >
                      View Score: {q.score}/{q.max_score}
                    </button>
                  ) : (
                    <button
                      onClick={() => startQuiz(q)}
                      className="px-3 py-1 bg-indigo-600 hover:bg-indigo-500 text-white rounded text-xs font-bold cursor-pointer transition-colors"
                    >
                      Take Test
                    </button>
                  )}
                </div>
              </div>
            ))}

            {quizList.length === 0 && (
              <p className="text-xs text-slate-500 text-center py-6">No quizzes created yet. Generate one above to test your skills.</p>
            )}
          </div>
        </div>
      </div>
    );
  };

  // --- Planner Tab View ---
  const renderPlanner = () => {
    return (
      <div className="space-y-6 max-w-xl mx-auto">
        <div className="space-y-1 text-center">
          <h2 className="text-xl font-bold text-white">Dynamic Study Planner</h2>
          <p className="text-sm text-slate-400">Configure parameters to generate a custom-fitted weekly schedule calendar.</p>
        </div>

        {/* Generate plan Panel */}
        <form onSubmit={handleGenerateStudyPlan} className="bg-slate-900/60 p-5 border border-slate-800 rounded-xl space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">Plan Duration (Days)</label>
              <select
                value={planGenDays}
                onChange={(e) => setPlanGenDays(parseInt(e.target.value))}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-300 focus:outline-none"
              >
                <option value={7}>7 Days (Weekly)</option>
                <option value={14}>14 Days (Fortnightly)</option>
                <option value={30}>30 Days (Monthly)</option>
              </select>
            </div>
            <div className="space-y-1.5">
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">Study Hours/Day</label>
              <select
                value={planGenHours}
                onChange={(e) => setPlanGenHours(parseInt(e.target.value))}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-300 focus:outline-none"
              >
                <option value={1}>1 Hour</option>
                <option value={2}>2 Hours</option>
                <option value={4}>4 Hours</option>
                <option value={6}>6 Hours</option>
              </select>
            </div>
          </div>

          <div className="space-y-2">
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">Include Subject Folders</label>
            <div className="grid grid-cols-2 gap-2 bg-slate-950 p-3 border border-slate-800 rounded-lg">
              {subjects.map((s) => {
                const isChecked = planGenSubjects.includes(s.id);
                return (
                  <label key={s.id} className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer select-none">
                    <input
                      type="checkbox"
                      checked={isChecked}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setPlanGenSubjects([...planGenSubjects, s.id]);
                        } else {
                          setPlanGenSubjects(planGenSubjects.filter((id) => id !== s.id));
                        }
                      }}
                      className="accent-indigo-500"
                    />
                    <span className="truncate">{s.name}</span>
                  </label>
                );
              })}
              {subjects.length === 0 && (
                <span className="col-span-2 text-slate-500 text-[11px] italic">No folders available. Create folders in Materials tab first.</span>
              )}
            </div>
          </div>

          <button
            type="submit"
            disabled={generatingPlan}
            className="w-full flex items-center justify-center gap-2 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold rounded-lg cursor-pointer transition-colors shadow-lg shadow-indigo-600/20"
          >
            {generatingPlan ? <Loader2 className="h-4 w-4 animate-spin" /> : <Calendar className="h-4 w-4" />}
            {generatingPlan ? "Optimizing adaptive tasks list..." : "Generate AI Study Schedule"}
          </button>
        </form>

        {/* Plan display */}
        {studyPlan ? (
          <div className="bg-slate-900/60 p-5 border border-slate-800 rounded-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-sm font-bold text-white">{studyPlan.title}</h3>
              <span className="text-[10px] text-indigo-400 font-bold uppercase tracking-wider bg-indigo-500/10 px-2 py-0.5 rounded">Adaptive Plan</span>
            </div>

            <div className="space-y-4">
              {studyPlan.schedule_json.map((day: any, idx: number) => (
                <div key={idx} className="space-y-2 border-l border-slate-800 pl-4 relative">
                  <div className="absolute top-1 left-[-4.5px] w-2 h-2 rounded-full bg-indigo-500" />
                  <div className="text-xs font-bold text-indigo-400">{day.date}</div>
                  
                  <div className="space-y-2">
                    {day.tasks.map((task: any, tIdx: number) => (
                      <div key={tIdx} className="bg-slate-950 p-3 border border-slate-850 rounded-lg text-xs space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-white">{task.subject} • {task.topic}</span>
                          <span className="text-slate-500">{task.duration_minutes} mins</span>
                        </div>
                        {task.notes && <p className="text-slate-400 mt-1 leading-relaxed">{task.notes}</p>}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="text-center py-20 bg-slate-900/30 border border-slate-800 border-dashed rounded-xl space-y-3">
            <Calendar className="h-8 w-8 text-slate-700 mx-auto" />
            <p className="text-xs text-slate-500 max-w-xs mx-auto">No study plan generated yet. Select subjects and goals above to compile your schedule.</p>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans select-none">
      {/* Top Navbar */}
      <header className="h-16 border-b border-slate-800 bg-slate-950/80 backdrop-blur px-6 flex items-center justify-between sticky top-0 z-50">
        <div className="flex items-center gap-2">
          <div className="p-1.5 bg-gradient-to-tr from-indigo-500 to-violet-600 rounded-lg text-white">
            <Sparkles className="h-5 w-5" />
          </div>
          <h1 className="text-md font-bold text-white tracking-tight">AI Study Assistant</h1>
        </div>
        <div className="flex items-center gap-4">
          <button
            onClick={() => {
              setSettingsName(userProfile?.full_name || "");
              setSettingsPassword("");
              setSettingsError("");
              setSettingsSuccess("");
              setShowSettingsModal(true);
            }}
            className="flex items-center gap-2 bg-slate-900 hover:bg-slate-800 hover:text-white px-3.5 py-1.5 border border-slate-800 rounded-xl text-xs font-semibold text-slate-300 transition-all cursor-pointer"
            title="Profile & Settings"
          >
            <User className="h-4 w-4 text-indigo-400" />
            {userProfile?.full_name || "Scholar"}
          </button>
          <button
            onClick={handleLogout}
            className="flex items-center gap-1.5 px-3 py-1.5 border border-slate-800 hover:border-rose-500/30 text-slate-400 hover:text-rose-400 rounded-lg text-xs font-semibold cursor-pointer transition-colors"
          >
            <LogOut className="h-4 w-4" /> Sign Out
          </button>
        </div>
      </header>

      {/* Main Body Layout */}
      <div className="flex-1 flex max-w-[1400px] w-full mx-auto p-6 gap-6 items-start">
        {/* Sidebar Navigation */}
        <aside className="w-56 bg-slate-900/20 p-4 border border-slate-850 rounded-2xl space-y-2 shrink-0 hidden md:block">
          <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider px-3 mb-2">Learning Engine</p>
          <nav className="space-y-1">
            {[
              { id: "dashboard", label: "Dashboard", icon: TrendingUp },
              { id: "materials", label: "Materials", icon: BookOpen },
              { id: "chat", label: "AI Chat Tutor", icon: MessageSquare },
              { id: "flashcards", label: "Flashcards", icon: Award },
              { id: "quiz", label: "Practice Quizzes", icon: CheckCircle },
              { id: "planner", label: "Study Planner", icon: Calendar }
            ].map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id as Tab)}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${activeTab === item.id ? "bg-indigo-600 text-white shadow-lg shadow-indigo-600/10" : "text-slate-400 hover:text-slate-200 hover:bg-slate-900/60"}`}
                >
                  <Icon className="h-4.5 w-4.5" />
                  {item.label}
                </button>
              );
            })}
          </nav>
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 bg-transparent min-w-0">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
            >
              {activeTab === "dashboard" && renderDashboard()}
              {activeTab === "materials" && renderMaterials()}
              {activeTab === "chat" && renderChat()}
              {activeTab === "flashcards" && renderFlashcards()}
              {activeTab === "quiz" && renderQuiz()}
              {activeTab === "planner" && renderPlanner()}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>

      {/* Settings Modal */}
      {showSettingsModal && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center z-[100] p-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden"
          >
            {/* Modal Header */}
            <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
              <h3 className="font-bold text-white text-sm flex items-center gap-2">
                <Settings className="h-4 w-4 text-indigo-400" />
                Profile & Deployment Settings
              </h3>
              <button
                onClick={() => setShowSettingsModal(false)}
                className="text-slate-400 hover:text-white transition-colors cursor-pointer p-1 rounded-lg hover:bg-slate-800"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* Modal Body */}
            <form onSubmit={handleUpdateProfile} className="p-6 space-y-6 overflow-y-auto max-h-[80vh]">
              {/* Profile details */}
              <div className="space-y-4">
                <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">User Account Profile</h4>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-[9px] font-bold text-slate-400 uppercase tracking-wider mb-1">Email Address</label>
                    <div className="w-full px-3 py-2 bg-slate-950/40 border border-slate-850 rounded-lg text-slate-500 text-xs truncate">
                      {userProfile?.email || "student@academy.com"}
                    </div>
                  </div>
                  <div>
                    <label className="block text-[9px] font-bold text-slate-400 uppercase tracking-wider mb-1">Account Role</label>
                    <div className="w-full px-3 py-2 bg-slate-950/40 border border-slate-850 rounded-lg text-slate-500 text-xs capitalize">
                      {userProfile?.role || "Student"}
                    </div>
                  </div>
                </div>

                <div>
                  <label className="block text-[9px] font-bold text-slate-400 uppercase tracking-wider mb-1">Full Name</label>
                  <input
                    type="text"
                    required
                    value={settingsName}
                    onChange={(e) => setSettingsName(e.target.value)}
                    placeholder="Enter your name"
                    className="w-full px-3 py-2.5 bg-slate-950/60 border border-slate-800 rounded-lg text-white text-xs placeholder-slate-600 focus:outline-none focus:border-indigo-500 transition-colors"
                  />
                </div>

                <div>
                  <label className="block text-[9px] font-bold text-slate-400 uppercase tracking-wider mb-1">Change Password (Optional)</label>
                  <input
                    type="password"
                    value={settingsPassword}
                    onChange={(e) => setSettingsPassword(e.target.value)}
                    placeholder="Enter new password (min 6 chars)"
                    className="w-full px-3 py-2.5 bg-slate-950/60 border border-slate-800 rounded-lg text-white text-xs placeholder-slate-600 focus:outline-none focus:border-indigo-500 transition-colors"
                  />
                </div>
              </div>

              <div className="w-full h-px bg-slate-800" />

              {/* OAuth Settings */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Google OAuth Production Credentials</h4>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input 
                      type="checkbox" 
                      checked={enableGoogleAuth} 
                      onChange={(e) => setEnableGoogleAuth(e.target.checked)}
                      className="sr-only peer"
                    />
                    <div className="w-9 h-5 bg-slate-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-slate-400 after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-indigo-600 peer-checked:after:bg-white"></div>
                  </label>
                </div>

                <div className={`space-y-3 transition-opacity duration-205 ${enableGoogleAuth ? 'opacity-100' : 'opacity-40 pointer-events-none'}`}>
                  <div>
                    <label className="block text-[9px] font-bold text-slate-400 uppercase tracking-wider mb-1">Google Client ID</label>
                    <input
                      type="text"
                      disabled={!enableGoogleAuth}
                      value={googleClientId}
                      onChange={(e) => setGoogleClientId(e.target.value)}
                      className="w-full px-3 py-2 bg-slate-950/60 border border-slate-800 rounded-lg text-white text-xs focus:outline-none focus:border-indigo-500"
                    />
                  </div>
                  <div>
                    <label className="block text-[9px] font-bold text-slate-400 uppercase tracking-wider mb-1">Google Client Secret</label>
                    <input
                      type="password"
                      disabled={!enableGoogleAuth}
                      value={googleClientSecret}
                      onChange={(e) => setGoogleClientSecret(e.target.value)}
                      className="w-full px-3 py-2 bg-slate-950/60 border border-slate-800 rounded-lg text-white text-xs focus:outline-none focus:border-indigo-500"
                    />
                  </div>
                </div>

                <div className="bg-indigo-950/30 border border-indigo-500/10 rounded-xl p-3.5 space-y-2">
                  <div className="text-[10px] font-bold text-indigo-400 uppercase tracking-wider">Deployment Instructions</div>
                  <p className="text-[10px] text-slate-400 leading-relaxed">
                    To enable Google Auth in production (e.g. Vercel, Render), ensure your host variables contain:
                  </p>
                  <pre className="text-[9px] font-mono bg-slate-950/60 border border-slate-850 p-2 rounded text-indigo-300 select-all">
                    GOOGLE_CLIENT_ID={googleClientId || "your-client-id"}{"\n"}
                    GOOGLE_CLIENT_SECRET=your_client_secret
                  </pre>
                  <p className="text-[9px] text-slate-500 leading-normal">
                    This maps to the Google OAuth callback on your frontend host at deployment.
                  </p>
                </div>
              </div>

              {settingsError && (
                <p className="text-xs font-semibold text-rose-400 bg-rose-500/10 p-2.5 rounded border border-rose-500/20">{settingsError}</p>
              )}
              {settingsSuccess && (
                <p className="text-xs font-semibold text-emerald-400 bg-emerald-500/10 p-2.5 rounded border border-emerald-500/20">{settingsSuccess}</p>
              )}

              {/* Action Buttons */}
              <div className="flex items-center justify-end gap-3 border-t border-slate-800 pt-4">
                <button
                  type="button"
                  onClick={() => setShowSettingsModal(false)}
                  className="px-4 py-2 border border-slate-800 hover:border-slate-700 text-slate-300 hover:text-white rounded-lg text-xs font-bold transition-colors cursor-pointer"
                >
                  Close
                </button>
                <button
                  type="submit"
                  disabled={settingsLoading}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-bold transition-all cursor-pointer shadow-lg shadow-indigo-600/20"
                >
                  {settingsLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Save Changes"}
                </button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </div>
  );
}
