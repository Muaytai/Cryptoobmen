// Simple WebSocket test page
import React, { useState, useRef } from 'react';
import ReactDOM from 'react-dom/client';

const WebSocketTest = () => {
  const [messages, setMessages] = useState<string[]>([]);
  const [status, setStatus] = useState<'connected' | 'disconnected'>('disconnected');
  const wsRef = useRef<WebSocket | null>(null);

  const connect = () => {
    const wsUrl = 'ws://localhost:8000/ws/deposit_status/address/9FadeNnX2pVag1g9Yc7Tjsj8vhYyig6jp56faf8GsC3M/';
    console.log('Connecting to:', wsUrl);
    
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;
    
    ws.onopen = () => {
      console.log('WebSocket connected');
      setStatus('connected');
      setMessages(prev => [...prev, 'Connected to WebSocket']);
    };
    
    ws.onmessage = (event) => {
      console.log('Received message:', event.data);
      setMessages(prev => [...prev, `Received: ${event.data}`]);
    };
    
    ws.onerror = (error: Event) => {
      console.error('WebSocket error:', error);
      setMessages(prev => [...prev, `Error: WebSocket connection error`]);
    };
    
    ws.onclose = () => {
      console.log('WebSocket closed');
      setStatus('disconnected');
      setMessages(prev => [...prev, 'Disconnected from WebSocket']);
    };
  };
  
  const disconnect = () => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  };
  
  return (
    <div style={{ padding: '20px' }}>
      <h1>WebSocket Test</h1>
      <p>Status: {status}</p>
      <button onClick={connect} disabled={status === 'connected'}>Connect</button>
      <button onClick={disconnect} disabled={status === 'disconnected'}>Disconnect</button>
      <div style={{ marginTop: '20px' }}>
        <h2>Messages:</h2>
        <ul>
          {messages.map((msg, index) => (
            <li key={index}>{msg}</li>
          ))}
        </ul>
      </div>
    </div>
  );
};

// Render the component
const root = document.createElement('div');
document.body.appendChild(root);
const reactRoot = ReactDOM.createRoot(root);
reactRoot.render(<WebSocketTest />);