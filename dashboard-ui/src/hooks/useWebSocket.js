"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { createWebSocket, getApiKey } from "@/lib/api";

export function useWebSocket() {
  const [lastMessage, setLastMessage] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef(null);
  const connectRef = useRef(null);
  const reconnectTimer = useRef(null);
  const heartbeatTimer = useRef(null);

  const clearTimers = useCallback(() => {
    clearTimeout(reconnectTimer.current);
    clearInterval(heartbeatTimer.current);
  }, []);

  const connect = useCallback(() => {
    const apiKey = getApiKey();
    if (!apiKey) return;

    clearTimers();

    try {
      const ws = createWebSocket(apiKey);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        heartbeatTimer.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send("ping");
          }
        }, 25000);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type !== "pong") {
            setLastMessage(data);
          }
        } catch {}
      };

      ws.onclose = () => {
        setIsConnected(false);
        clearTimers();
        reconnectTimer.current = setTimeout(() => connectRef.current?.(), 5000);
      };

      ws.onerror = () => {
        ws.close();
      };
    } catch {
      reconnectTimer.current = setTimeout(() => connectRef.current?.(), 5000);
    }
  }, [clearTimers]);

  useEffect(() => {
    connectRef.current = connect;
  }, [connect]);

  useEffect(() => {
    connect();
    return () => {
      clearTimers();
      if (wsRef.current) wsRef.current.close();
    };
  }, [clearTimers, connect]);

  const sendMessage = useCallback((msg) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(typeof msg === "string" ? msg : JSON.stringify(msg));
    }
  }, []);

  return { lastMessage, isConnected, sendMessage };
}
