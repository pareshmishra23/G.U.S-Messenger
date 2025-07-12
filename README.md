# Here are your Instructions

# 🗒️ NOTE.md – GUSChat Development Notes

This file is intended to track key decisions, architecture choices, pending features, and contributor responsibilities for the **GUSChat** project.

---

## 📌 Project Overview

**GUSChat** is a real-time messaging and video calling web application designed using:
- **Frontend**: React.js (v19) + Tailwind CSS
- **Backend**: FastAPI + Python-SocketIO
- **Database**: MongoDB (via Motor)
- **Real-time Communication**: WebSockets with Socket.IO
- **Video Calling**: WebRTC (pure, no third-party dependencies)
- **Auth**: JWT-based, bcrypt hashed passwords

---

## 🚧 Active Contributors

| Name             | Role                         | Area of Work                     |
|------------------|-------------------------------|----------------------------------|
| Paresh Mishra    | Project Owner / Architect     | Vision, Planning, Testing        |
| Emergent Agent   | Fullstack Bot Developer       | Initial Architecture, UI, WebRTC |
| ChatGPT          | Code Advisor + Doc Generator  | Planning, AI Integration, Code   |

---

## ✅ Completed Milestones

- [x] JWT-based auth system
- [x] Real-time 1:1 messaging with Socket.IO
- [x] User status (online/offline)
- [x] WebRTC peer-to-peer calling
- [x] Production-ready UI with Tailwind
- [x] MongoDB persistence layer
- [x] `USAGE.md` completed

---

## 🛠 Upcoming Features (Planned)

| Feature                  | Priority | Owner     | Notes                                                    |
|--------------------------|----------|-----------|----------------------------------------------------------|
| Group chat rooms         | 🔥 High  | TBA       | Enable multiple users in one room                       |
| File sharing             | 🔥 High  | TBA       | Upload/download in chat                                 |
| Screen sharing           | ⚡ Medium| TBA       | WebRTC add-on                                           |
| Chat history search      | ⚡ Medium| TBA       | MongoDB search/filter                                   |
| Push notifications       | ⚡ Medium| TBA       | For new messages and call invites                       |
| Message encryption       | 🧠 Low   | ChatGPT   | End-to-end (AES or libsodium)                           |
| React Native App         | 🧠 Low   | You       | Mobile version for Android/iOS                          |
| AI Assistant Integration | 🧠 Low   | ChatGPT   | "SmartBot" user powered by GPT                          |

---

## 💡 Future Integration (AI Ideas)

- ✨ **ShramSetu** App (New Project)
  - AI-powered voice bot that calls laborers using TTS in regional languages
  - Takes job acceptance input via DTMF or voice
  - Matches job-givers with daily wage workers
  - **Status**: Planning started (to be added as a new repo)

- 🤖 GPT Agent inside GUSChat
  - AI chat with GPT via a virtual user: `ai_assistant`

---

## 🧪 Testing Notes

| Area            | Status       | Comments                              |
|------------------|--------------|---------------------------------------|
| Backend API      | ✅ Pass (13/15)| Minor validation edge cases pending   |
| Frontend UI      | ✅ OK         | Fully functional, mobile responsive   |
| WebRTC           | ✅ Working    | Call setup via STUN only, no TURN     |
| MongoDB Storage  | ✅ Working    | All messages, users saved persistently|

---

## 📝 Repo Structure (Recap)


