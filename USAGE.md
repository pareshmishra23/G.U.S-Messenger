# 📘 GUSChat – Usage Guide

Welcome to **GUSChat**, a real-time chat and video calling application built with **React**, **FastAPI**, **MongoDB**, **Socket.IO**, and **WebRTC**.

---

## 🚀 Getting Started

### ✅ Prerequisites

Make sure:
- The backend is running on FastAPI with WebSocket support
- The frontend is running (usually on `localhost:3000`)
- You’ve created at least 2 users

---

## 📱 User Guide

### Why You Don’t See Contacts

You will only see **other users** in your contact list.  
👉 If you're the only registered user, your contacts list will be empty.

---

## 🧪 Test Setup Options

### Method 1: Two Browser Windows

1. **Register First User (e.g., Alice)**
   - Open [GUSChat App](https://0c7a9b73-4815-4b95-8c7a-88602d3618c8.preview.emergentagent.com)
   - Register with:
     - Username: `alice`
     - Email: `alice@example.com`
     - Password: `password123`

2. **Register Second User (e.g., Bob)**
   - Open the same URL in a **new browser tab or window**
   - Register with:
     - Username: `bob`
     - Email: `bob@example.com`
     - Password: `password123`

3. **View Contacts**
   - Alice will see "bob" and vice versa

---

### Method 2: Using Incognito or Two Browsers

- Regular browser: login as `alice`
- Incognito/private mode: login as `bob`
- Or use different browsers: Chrome & Firefox

---

## 💬 Real-Time Messaging

1. Click on a contact (e.g., "bob")
2. Type your message in the input field
3. Hit **Enter** or click **Send**
4. Switch to the other user's tab — message appears instantly

---

## 📹 Video Calling

1. Open chat with a contact
2. Click the **📹 Video Call** button
3. Allow browser to access **camera and microphone**
4. Other user will see an incoming call
5. They can **Accept** or **Reject**
6. On accept, peer-to-peer video chat starts

---

## 🟢 Online/Offline Status

- Green dot = online
- Gray dot = offline
- Updates in real-time as users connect or disconnect

---

## 🧪 API: Create Test Users (Optional)

```bash
# Alice
curl -X POST "https://<your-backend-url>/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "email": "alice@test.com", "password": "password123"}'


🛠 Troubleshooting
Issue	Fix
No contacts appear	Ensure there are multiple registered users
Messages not showing	Confirm Socket.IO is connected
Camera not working	Check browser permissions; must be on HTTPS
Calls not connecting	Check WebRTC peer signaling via dev console
UI looks broken on mobile	Try resizing or inspecting CSS responsiveness (Tailwind)

✅ App Preview
🌐 Live Demo

📁 Repo: G.U.S-Messenger

Happy chatting! 🚀
Built with ❤️ by Paresh Mishra + GUS Team

# Bob
curl -X POST "https://<your-backend-url>/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "bob", "email": "bob@test.com", "password": "password123"}'
