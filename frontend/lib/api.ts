const getBaseUrl = (): string => {
    if (typeof window !== "undefined") {
        // Check if environment variable is defined
        const envUrl = process.env.NEXT_PUBLIC_API_URL;
        if (envUrl) return envUrl;

        // Otherwise check hostname
        const hostname = window.location.hostname;
        if (hostname === "localhost" || hostname === "127.0.0.1") {
            return "http://127.0.0.1:8000/api/v1";
        }
        // Fallback: assume monorepo proxy routing on Vercel
        return `${window.location.origin}/api/v1`;
    }
    return "http://127.0.0.1:8000/api/v1";
};

const API_BASE_URL = getBaseUrl();


class APIClient {
    private getHeaders(isMultipart = false): HeadersInit {
        const headers: Record<string, string> = {};
        if (!isMultipart) {
            headers["Content-Type"] = "application/json";
        }
        
        const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
        if (token) {
            headers["Authorization"] = `Bearer ${token}`;
        }
        return headers;
    }

    async request(endpoint: string, options: RequestInit = {}): Promise<any> {
        const url = `${API_BASE_URL}${endpoint}`;
        const isMultipart = options.body instanceof FormData;
        
        const config: RequestInit = {
            ...options,
            headers: {
                ...this.getHeaders(isMultipart),
                ...(options.headers || {}),
            },
        };

        const response = await fetch(url, config);

        if (!response.ok) {
            let errorMsg = "Something went wrong";
            try {
                const errData = await response.json();
                errorMsg = errData.detail || errorMsg;
            } catch (e) {
                // fall through
            }
            throw new Error(errorMsg);
        }

        if (response.status === 204) {
            return null;
        }

        return response.json();
    }

    // Auth endpoints
    async register(data: any) {
        return this.request("/auth/register", {
            method: "POST",
            body: JSON.stringify(data),
        });
    }

    async verifyOTP(data: any) {
        return this.request("/auth/verify-otp", {
            method: "POST",
            body: JSON.stringify(data),
        });
    }

    async login(data: any) {
        return this.request("/auth/login", {
            method: "POST",
            body: JSON.stringify(data),
        });
    }

    async getProfile() {
        return this.request("/auth/me");
    }

    async getAuthConfig() {
        return this.request("/auth/config");
    }


    async updateProfile(data: any) {
        return this.request("/auth/me", {
            method: "PUT",
            body: JSON.stringify(data),
        });
    }


    async loginGoogle(idToken: string) {
        return this.request(`/auth/google?id_token=${encodeURIComponent(idToken)}`, {
            method: "POST",
        });
    }

    // Subjects and Files
    async getSubjects() {
        return this.request("/materials/subjects");
    }

    async createSubject(data: any) {
        return this.request("/materials/subjects", {
            method: "POST",
            body: JSON.stringify(data),
        });
    }

    async deleteSubject(id: number) {
        return this.request(`/materials/subjects/${id}`, {
            method: "DELETE",
        });
    }

    async getFiles(subjectId?: number) {
        const query = subjectId ? `?subject_id=${subjectId}` : "";
        return this.request(`/materials/files${query}`);
    }

    async uploadFile(formData: FormData) {
        return this.request("/materials/upload", {
            method: "POST",
            body: formData,
        });
    }

    async deleteFile(id: number) {
        return this.request(`/materials/files/${id}`, {
            method: "DELETE",
        });
    }

    async assignFileToSubject(fileId: number, subjectId: number | null) {
        const query = subjectId !== null ? `?subject_id=${subjectId}` : "";
        return this.request(`/materials/files/${fileId}/subject${query}`, {
            method: "PATCH",
        });
    }

    async getFileStatus(id: number) {
        return this.request(`/materials/files/${id}`);
    }

    // RAG AI Chat
    async getConversations(subjectId?: number) {
        const query = subjectId ? `?subject_id=${subjectId}` : "";
        return this.request(`/chat/conversations${query}`);
    }

    async createConversation(title: string, subjectId?: number) {
        return this.request("/chat/conversations", {
            method: "POST",
            body: JSON.stringify({ title, subject_id: subjectId }),
        });
    }

    async deleteConversation(id: number) {
        return this.request(`/chat/conversations/${id}`, {
            method: "DELETE",
        });
    }

    async getMessages(conversationId: number) {
        return this.request(`/chat/conversations/${conversationId}/messages`);
    }

    async sendMessage(conversationId: number, query: any) {
        return this.request(`/chat/conversations/${conversationId}/query`, {
            method: "POST",
            body: JSON.stringify(query),
        });
    }

    getStreamURL(conversationId: number, message: string, restrict: boolean) {
        const token = typeof window !== "undefined" ? localStorage.getItem("token") : "";
        return `${API_BASE_URL}/chat/conversations/${conversationId}/query/stream?message=${encodeURIComponent(message)}&restrict_to_materials=${restrict}&token=${token}`;
    }

    // Study tools (Notes, Flashcards, Quizzes)
    async generateNotes(fileIds: number[], noteType: string) {
        return this.request(`/study-tools/notes?note_type=${encodeURIComponent(noteType)}`, {
            method: "POST",
            body: JSON.stringify(fileIds),
        });
    }

    async getFlashcards(subjectId?: number, dueOnly = false) {
        const params = [];
        if (subjectId) params.push(`subject_id=${subjectId}`);
        if (dueOnly) params.push(`due_only=true`);
        const query = params.length ? `?${params.join("&")}` : "";
        return this.request(`/study-tools/flashcards${query}`);
    }

    async generateFlashcards(fileId: number, numCards = 5) {
        return this.request(`/study-tools/flashcards/generate?file_id=${fileId}&num_cards=${numCards}`, {
            method: "POST",
        });
    }

    async reviewFlashcard(cardId: number, rating: number) {
        return this.request(`/study-tools/flashcards/${cardId}/review`, {
            method: "POST",
            body: JSON.stringify({ rating }),
        });
    }

    async deleteFlashcard(cardId: number) {
        return this.request(`/study-tools/flashcards/${cardId}`, {
            method: "DELETE",
        });
    }

    async clearFlashcards(subjectId?: number) {
        const query = subjectId ? `?subject_id=${subjectId}` : "";
        return this.request(`/study-tools/flashcards${query}`, {
            method: "DELETE",
        });
    }



    // Quiz endpoints
    async generateQuiz(data: any) {
        return this.request("/quiz", {
            method: "POST",
            body: JSON.stringify(data),
        });
    }

    async getQuizzes(subjectId?: number) {
        const query = subjectId ? `?subject_id=${subjectId}` : "";
        return this.request(`/quiz${query}`);
    }

    async getQuizDetails(id: number) {
        return this.request(`/quiz/${id}`);
    }

    async submitQuiz(id: number, answers: any[], timeTaken: number) {
        return this.request(`/quiz/${id}/submit`, {
            method: "POST",
            body: JSON.stringify({ answers, time_taken: timeTaken }),
        });
    }

    // Study Planner
    async generateStudyPlan(data: any) {
        return this.request("/planner", {
            method: "POST",
            body: JSON.stringify(data),
        });
    }

    async getActiveStudyPlan() {
        return this.request("/planner");
    }

    async startStudySession(subjectId?: number, notes?: string) {
        return this.request("/planner/sessions/start", {
            method: "POST",
            body: JSON.stringify({ subject_id: subjectId, notes, start_time: new Date().toISOString() }),
        });
    }

    async endStudySession(sessionId: number, notes?: string) {
        return this.request(`/planner/sessions/${sessionId}/end`, {
            method: "POST",
            body: JSON.stringify({ notes, end_time: new Date().toISOString() }),
        });
    }

    async getStudySessions(subjectId?: number) {
        const query = subjectId ? `?subject_id=${subjectId}` : "";
        return this.request(`/planner/sessions${query}`);
    }

    // Dashboard Analytics
    async getAnalytics() {
        return this.request("/analytics");
    }
}

export const api = new APIClient();
export default api;
