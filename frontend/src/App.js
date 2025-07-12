import React, { useState, useEffect } from 'react';
import io from 'socket.io-client';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function App() {
  const [user, setUser] = useState(null);
  const [socket, setSocket] = useState(null);
  const [users, setUsers] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [messages, setMessages] = useState([]);
  const [messageInput, setMessageInput] = useState('');
  const [isInCall, setIsInCall] = useState(false);
  const [incomingCall, setIncomingCall] = useState(null);
  const [localStream, setLocalStream] = useState(null);
  const [remoteStream, setRemoteStream] = useState(null);
  const [peerConnection, setPeerConnection] = useState(null);
  const [isLoginMode, setIsLoginMode] = useState(true);
  const [authData, setAuthData] = useState({
    username: '',
    email: '',
    password: ''
  });

  // WebRTC configuration
  const rtcConfig = {
    iceServers: [
      { urls: 'stun:stun.l.google.com:19302' },
      { urls: 'stun:stun1.l.google.com:19302' }
    ]
  };

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      const userData = JSON.parse(localStorage.getItem('user'));
      setUser(userData);
      initializeSocket(token);
    }
  }, []);

  const initializeSocket = (token) => {
    const newSocket = io(BACKEND_URL, {
      auth: { token }
    });

    newSocket.on('connect', () => {
      console.log('Connected to server');
      fetchUsers();
    });

    newSocket.on('new_message', (data) => {
      if (selectedUser && (data.message.sender_id === selectedUser.id || data.message.receiver_id === selectedUser.id)) {
        setMessages(prev => [...prev, data.message]);
      }
    });

    newSocket.on('user_online', (data) => {
      setUsers(prev => prev.map(u => 
        u.id === data.user_id ? { ...u, is_online: true } : u
      ));
    });

    newSocket.on('user_offline', (data) => {
      setUsers(prev => prev.map(u => 
        u.id === data.user_id ? { ...u, is_online: false } : u
      ));
    });

    newSocket.on('incoming_call', (data) => {
      setIncomingCall(data);
    });

    newSocket.on('call_accepted', (data) => {
      handleCallAccepted(data.answer);
    });

    newSocket.on('call_rejected', () => {
      endCall();
    });

    newSocket.on('call_ended', () => {
      endCall();
    });

    newSocket.on('ice_candidate', (data) => {
      if (peerConnection) {
        peerConnection.addIceCandidate(new RTCIceCandidate(data.candidate));
      }
    });

    setSocket(newSocket);
  };

  const fetchUsers = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/users`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      const usersData = await response.json();
      setUsers(usersData);
    } catch (error) {
      console.error('Failed to fetch users:', error);
    }
  };

  const fetchMessages = async (userId) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/messages/${userId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      const messagesData = await response.json();
      setMessages(messagesData);
    } catch (error) {
      console.error('Failed to fetch messages:', error);
    }
  };

  const handleAuth = async (e) => {
    e.preventDefault();
    try {
      const endpoint = isLoginMode ? '/api/auth/login' : '/api/auth/register';
      const response = await fetch(`${BACKEND_URL}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(authData)
      });

      const data = await response.json();
      
      if (response.ok) {
        if (isLoginMode) {
          localStorage.setItem('token', data.access_token);
          localStorage.setItem('user', JSON.stringify(data.user));
          setUser(data.user);
          initializeSocket(data.access_token);
        } else {
          setIsLoginMode(true);
          setAuthData({ username: '', email: '', password: '' });
        }
      } else {
        alert(data.detail || 'Authentication failed');
      }
    } catch (error) {
      console.error('Auth error:', error);
      alert('Authentication failed');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
    if (socket) {
      socket.disconnect();
    }
    setSocket(null);
    setUsers([]);
    setSelectedUser(null);
    setMessages([]);
  };

  const sendMessage = (e) => {
    e.preventDefault();
    if (messageInput.trim() && selectedUser && socket) {
      const messageData = {
        receiver_id: selectedUser.id,
        content: messageInput
      };
      
      socket.emit('send_message', messageData);
      
      // Add message to local state optimistically
      const newMessage = {
        id: Date.now().toString(),
        sender_id: user.id,
        receiver_id: selectedUser.id,
        content: messageInput,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, newMessage]);
      setMessageInput('');
    }
  };

  const initiateCall = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      setLocalStream(stream);
      
      const pc = new RTCPeerConnection(rtcConfig);
      setPeerConnection(pc);
      
      stream.getTracks().forEach(track => {
        pc.addTrack(track, stream);
      });

      pc.onicecandidate = (event) => {
        if (event.candidate && socket) {
          socket.emit('ice_candidate', {
            other_user_id: selectedUser.id,
            candidate: event.candidate
          });
        }
      };

      pc.ontrack = (event) => {
        setRemoteStream(event.streams[0]);
      };

      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);
      
      socket.emit('call_user', {
        receiver_id: selectedUser.id,
        offer: offer
      });
      
      setIsInCall(true);
    } catch (error) {
      console.error('Failed to initiate call:', error);
    }
  };

  const acceptCall = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      setLocalStream(stream);
      
      const pc = new RTCPeerConnection(rtcConfig);
      setPeerConnection(pc);
      
      stream.getTracks().forEach(track => {
        pc.addTrack(track, stream);
      });

      pc.onicecandidate = (event) => {
        if (event.candidate && socket) {
          socket.emit('ice_candidate', {
            other_user_id: incomingCall.caller.id,
            candidate: event.candidate
          });
        }
      };

      pc.ontrack = (event) => {
        setRemoteStream(event.streams[0]);
      };

      await pc.setRemoteDescription(new RTCSessionDescription(incomingCall.offer));
      const answer = await pc.createAnswer();
      await pc.setLocalDescription(answer);
      
      socket.emit('call_accepted', {
        caller_id: incomingCall.caller.id,
        answer: answer
      });
      
      setIsInCall(true);
      setIncomingCall(null);
    } catch (error) {
      console.error('Failed to accept call:', error);
    }
  };

  const handleCallAccepted = async (answer) => {
    if (peerConnection) {
      await peerConnection.setRemoteDescription(new RTCSessionDescription(answer));
    }
  };

  const rejectCall = () => {
    if (socket && incomingCall) {
      socket.emit('call_rejected', {
        caller_id: incomingCall.caller.id
      });
    }
    setIncomingCall(null);
  };

  const endCall = () => {
    if (socket && selectedUser) {
      socket.emit('end_call', {
        other_user_id: selectedUser.id
      });
    }
    
    if (localStream) {
      localStream.getTracks().forEach(track => track.stop());
    }
    
    if (peerConnection) {
      peerConnection.close();
    }
    
    setIsInCall(false);
    setLocalStream(null);
    setRemoteStream(null);
    setPeerConnection(null);
  };

  const selectUser = (selectedUser) => {
    setSelectedUser(selectedUser);
    fetchMessages(selectedUser.id);
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="bg-white p-8 rounded-lg shadow-lg w-full max-w-md">
          <div className="text-center mb-6">
            <h1 className="text-3xl font-bold text-gray-800 mb-2">EmergentChat</h1>
            <p className="text-gray-600">Connect and video chat with friends</p>
          </div>
          
          <form onSubmit={handleAuth} className="space-y-4">
            <div>
              <input
                type="text"
                placeholder="Username"
                value={authData.username}
                onChange={(e) => setAuthData({...authData, username: e.target.value})}
                className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
            
            {!isLoginMode && (
              <div>
                <input
                  type="email"
                  placeholder="Email"
                  value={authData.email}
                  onChange={(e) => setAuthData({...authData, email: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
            )}
            
            <div>
              <input
                type="password"
                placeholder="Password"
                value={authData.password}
                onChange={(e) => setAuthData({...authData, password: e.target.value})}
                className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
            
            <button
              type="submit"
              className="w-full bg-blue-500 text-white p-3 rounded-lg hover:bg-blue-600 transition-colors font-medium"
            >
              {isLoginMode ? 'Login' : 'Register'}
            </button>
          </form>
          
          <div className="text-center mt-4">
            <button
              onClick={() => setIsLoginMode(!isLoginMode)}
              className="text-blue-500 hover:text-blue-600 text-sm"
            >
              {isLoginMode ? 'Need an account? Register' : 'Already have an account? Login'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200 p-4">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-800">EmergentChat</h1>
          <div className="flex items-center space-x-4">
            <span className="text-gray-600">Welcome, {user.username}</span>
            <button
              onClick={handleLogout}
              className="bg-red-500 text-white px-4 py-2 rounded-lg hover:bg-red-600 transition-colors"
            >
              Logout
            </button>
          </div>
        </div>
      </div>

      <div className="flex h-screen">
        {/* Sidebar */}
        <div className="w-1/3 bg-white border-r border-gray-200">
          <div className="p-4 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-800">Contacts</h2>
          </div>
          <div className="overflow-y-auto">
            {users.map(contactUser => (
              <div
                key={contactUser.id}
                onClick={() => selectUser(contactUser)}
                className={`p-4 border-b border-gray-100 cursor-pointer hover:bg-gray-50 ${
                  selectedUser?.id === contactUser.id ? 'bg-blue-50 border-blue-200' : ''
                }`}
              >
                <div className="flex items-center space-x-3">
                  <div className="relative">
                    <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center">
                      <span className="text-white font-medium">
                        {contactUser.username.charAt(0).toUpperCase()}
                      </span>
                    </div>
                    <div className={`absolute -bottom-1 -right-1 w-4 h-4 rounded-full border-2 border-white ${
                      contactUser.is_online ? 'bg-green-500' : 'bg-gray-400'
                    }`}></div>
                  </div>
                  <div>
                    <div className="font-medium text-gray-800">{contactUser.username}</div>
                    <div className="text-sm text-gray-500">
                      {contactUser.is_online ? 'Online' : 'Offline'}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Main Chat Area */}
        <div className="flex-1 flex flex-col">
          {selectedUser ? (
            <>
              {/* Chat Header */}
              <div className="bg-white p-4 border-b border-gray-200 flex justify-between items-center">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center">
                    <span className="text-white font-medium">
                      {selectedUser.username.charAt(0).toUpperCase()}
                    </span>
                  </div>
                  <div>
                    <div className="font-medium text-gray-800">{selectedUser.username}</div>
                    <div className="text-sm text-gray-500">
                      {selectedUser.is_online ? 'Online' : 'Offline'}
                    </div>
                  </div>
                </div>
                <button
                  onClick={initiateCall}
                  disabled={!selectedUser.is_online || isInCall}
                  className="bg-green-500 text-white px-4 py-2 rounded-lg hover:bg-green-600 transition-colors disabled:bg-gray-400"
                >
                  📹 Video Call
                </button>
              </div>

              {/* Messages Area */}
              <div className="flex-1 p-4 overflow-y-auto bg-gray-50">
                <div className="space-y-4">
                  {messages.map(message => (
                    <div
                      key={message.id}
                      className={`flex ${message.sender_id === user.id ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                          message.sender_id === user.id
                            ? 'bg-blue-500 text-white'
                            : 'bg-white text-gray-800 border border-gray-200'
                        }`}
                      >
                        <div className="break-words">{message.content}</div>
                        <div className="text-xs mt-1 opacity-70">
                          {new Date(message.timestamp).toLocaleTimeString()}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Message Input */}
              <div className="bg-white p-4 border-t border-gray-200">
                <form onSubmit={sendMessage} className="flex space-x-2">
                  <input
                    type="text"
                    value={messageInput}
                    onChange={(e) => setMessageInput(e.target.value)}
                    placeholder="Type a message..."
                    className="flex-1 p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <button
                    type="submit"
                    className="bg-blue-500 text-white px-6 py-3 rounded-lg hover:bg-blue-600 transition-colors"
                  >
                    Send
                  </button>
                </form>
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center bg-gray-50">
              <div className="text-center">
                <div className="text-6xl text-gray-400 mb-4">💬</div>
                <h2 className="text-2xl font-semibold text-gray-600 mb-2">Welcome to EmergentChat</h2>
                <p className="text-gray-500">Select a contact to start chatting</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Video Call Modal */}
      {isInCall && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg max-w-4xl w-full mx-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-semibold">Video Call with {selectedUser?.username}</h3>
              <button
                onClick={endCall}
                className="bg-red-500 text-white px-4 py-2 rounded-lg hover:bg-red-600 transition-colors"
              >
                End Call
              </button>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-200 aspect-video rounded-lg flex items-center justify-center">
                {localStream ? (
                  <video
                    ref={video => {
                      if (video) video.srcObject = localStream;
                    }}
                    autoPlay
                    muted
                    playsInline
                    className="w-full h-full object-cover rounded-lg"
                  />
                ) : (
                  <div className="text-gray-600">Your Video</div>
                )}
              </div>
              <div className="bg-gray-200 aspect-video rounded-lg flex items-center justify-center">
                {remoteStream ? (
                  <video
                    ref={video => {
                      if (video) video.srcObject = remoteStream;
                    }}
                    autoPlay
                    playsInline
                    className="w-full h-full object-cover rounded-lg"
                  />
                ) : (
                  <div className="text-gray-600">Remote Video</div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Incoming Call Modal */}
      {incomingCall && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg max-w-md w-full mx-4">
            <div className="text-center">
              <div className="text-6xl mb-4">📞</div>
              <h3 className="text-xl font-semibold mb-2">Incoming Call</h3>
              <p className="text-gray-600 mb-6">{incomingCall.caller.username} is calling you...</p>
              <div className="flex space-x-4">
                <button
                  onClick={acceptCall}
                  className="flex-1 bg-green-500 text-white py-3 rounded-lg hover:bg-green-600 transition-colors"
                >
                  Accept
                </button>
                <button
                  onClick={rejectCall}
                  className="flex-1 bg-red-500 text-white py-3 rounded-lg hover:bg-red-600 transition-colors"
                >
                  Reject
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;