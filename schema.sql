-- AI Study Assistant Database Schema (PostgreSQL Compatible)

-- Enums Definition
CREATE TYPE user_role AS ENUM ('student', 'admin');
CREATE TYPE otp_purpose AS ENUM ('verify_email', 'reset_password');
CREATE TYPE file_status AS ENUM ('uploading', 'processing', 'processed', 'failed');
CREATE TYPE ocr_status AS ENUM ('pending', 'processing', 'completed', 'failed', 'skipped');
CREATE TYPE message_sender AS ENUM ('user', 'assistant');
CREATE TYPE quiz_difficulty AS ENUM ('easy', 'medium', 'hard');
CREATE TYPE quiz_status AS ENUM ('pending', 'completed');
CREATE TYPE question_type AS ENUM ('mcq', 'true_false', 'fill_blank', 'short_answer', 'long_answer');

-- 1. Users Table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT FALSE NOT NULL,
    role user_role DEFAULT 'student' NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 2. User OTPs Table
CREATE TABLE user_otps (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    code VARCHAR(10) NOT NULL,
    purpose otp_purpose NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_used BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 3. Subjects Table
CREATE TABLE subjects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    color VARCHAR(7) DEFAULT '#4F46E5' NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 4. Files Table
CREATE TABLE files (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    path VARCHAR(512) NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    file_size INTEGER NOT NULL,
    status file_status DEFAULT 'uploading' NOT NULL,
    ocr_status ocr_status DEFAULT 'pending' NOT NULL,
    error_message TEXT,
    subject_id INTEGER REFERENCES subjects(id) ON DELETE SET NULL,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 5. Document Metadata Table
CREATE TABLE document_metadata (
    id SERIAL PRIMARY KEY,
    file_id INTEGER UNIQUE NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    title VARCHAR(255),
    author VARCHAR(255),
    total_pages INTEGER DEFAULT 1 NOT NULL,
    language VARCHAR(10) DEFAULT 'en' NOT NULL,
    extra_info JSONB
);

-- 6. OCR Results Table
CREATE TABLE ocr_results (
    id SERIAL PRIMARY KEY,
    file_id INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL,
    extracted_text TEXT NOT NULL,
    layout_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 7. Document Chunks Table
CREATE TABLE document_chunks (
    id SERIAL PRIMARY KEY,
    file_id INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL,
    chunk_index INTEGER NOT NULL,
    text_content TEXT NOT NULL,
    vector_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 8. Conversations Table
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) DEFAULT 'New Conversation' NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subject_id INTEGER REFERENCES subjects(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 9. Messages Table
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    sender message_sender NOT NULL,
    content TEXT NOT NULL,
    audio_url VARCHAR(512),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 10. Message Citations Table
CREATE TABLE message_citations (
    id SERIAL PRIMARY KEY,
    message_id INTEGER NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    file_id INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    page_number INTEGER,
    snippet TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 11. Quizzes Table
CREATE TABLE quizzes (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subject_id INTEGER REFERENCES subjects(id) ON DELETE SET NULL,
    difficulty quiz_difficulty DEFAULT 'medium' NOT NULL,
    score INTEGER DEFAULT 0 NOT NULL,
    max_score INTEGER DEFAULT 0 NOT NULL,
    time_taken INTEGER,
    status quiz_status DEFAULT 'pending' NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 12. Quiz Questions Table
CREATE TABLE quiz_questions (
    id SERIAL PRIMARY KEY,
    quiz_id INTEGER NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    question_type question_type NOT NULL,
    options JSONB,
    correct_answer TEXT NOT NULL,
    explanation TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 13. Quiz User Answers Table
CREATE TABLE quiz_user_answers (
    id SERIAL PRIMARY KEY,
    quiz_id INTEGER NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE,
    question_id INTEGER NOT NULL REFERENCES quiz_questions(id) ON DELETE CASCADE,
    user_answer TEXT NOT NULL,
    is_correct BOOLEAN,
    points_awarded INTEGER DEFAULT 0 NOT NULL,
    feedback TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 14. Flashcards Table
CREATE TABLE flashcards (
    id SERIAL PRIMARY KEY,
    front TEXT NOT NULL,
    back TEXT NOT NULL,
    difficulty VARCHAR(50) DEFAULT 'medium' NOT NULL,
    topic VARCHAR(255),
    next_review TIMESTAMP WITH TIME ZONE NOT NULL,
    interval INTEGER DEFAULT 0 NOT NULL,
    ease_factor DOUBLE PRECISION DEFAULT 2.5 NOT NULL,
    repetitions INTEGER DEFAULT 0 NOT NULL,
    subject_id INTEGER REFERENCES subjects(id) ON DELETE SET NULL,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 15. Study Plans Table
CREATE TABLE study_plans (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    start_date TIMESTAMP WITH TIME ZONE NOT NULL,
    end_date TIMESTAMP WITH TIME ZONE NOT NULL,
    daily_hours INTEGER DEFAULT 2 NOT NULL,
    schedule_json JSONB NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 16. Study Sessions Table
CREATE TABLE study_sessions (
    id SERIAL PRIMARY KEY,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER DEFAULT 0 NOT NULL,
    notes TEXT,
    subject_id INTEGER REFERENCES subjects(id) ON DELETE SET NULL,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 17. Notifications Table
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE NOT NULL,
    notification_type VARCHAR(50) DEFAULT 'info' NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 18. Feedbacks Table
CREATE TABLE feedbacks (
    id SERIAL PRIMARY KEY,
    rating INTEGER NOT NULL,
    comments TEXT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Indexes for Query Performance Optimization
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_user_otps_user ON user_otps(user_id);
CREATE INDEX idx_subjects_user ON subjects(user_id);
CREATE INDEX idx_files_user ON files(user_id);
CREATE INDEX idx_files_subject ON files(subject_id);
CREATE INDEX idx_document_chunks_file ON document_chunks(file_id);
CREATE INDEX idx_document_chunks_vector ON document_chunks(vector_id);
CREATE INDEX idx_conversations_user ON conversations(user_id);
CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_quizzes_user ON quizzes(user_id);
CREATE INDEX idx_quiz_questions_quiz ON quiz_questions(quiz_id);
CREATE INDEX idx_flashcards_user ON flashcards(user_id);
CREATE INDEX idx_flashcards_next_review ON flashcards(next_review);
CREATE INDEX idx_study_plans_user ON study_plans(user_id);
CREATE INDEX idx_study_sessions_user ON study_sessions(user_id);
