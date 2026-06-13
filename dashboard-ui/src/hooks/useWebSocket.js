"use client";
import { useEffect, useRef, useState, useCallback } from "react";
import { createWebSocket, getApiKey } from "@/lib/api";

/**
 * WebSocket hook — 自动连接、重连、心跳。
 * 返回 { lastMessage, isConnected, sendMessage }
 */
export function useWebSocket() {
  const [lastMessage, setLastMessage] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef(null);
  const reconnectTimer = useRef(null);
  const heartbeatTimer = useRef(null);

  const connect = useCallback(() => {
    const apiKey = getApiKey();
    if (!apiKey) return;

    try {
      const ws = createWebSocket(apiKey);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        // 心跳
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
        clearInterval(heartbeatTimer.current);
        // 5s 后重连
        reconnectTimer.current = setTimeout(connect, 5000);
      };

      ws.onerror = () => {
        ws.close();
      };
    } catch {}
  }, []);

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectTimer.current);
      clearInterval(heartbeatTimer.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, [connect]);

  const sendMessage = useCallback((msg) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(typeof msg === "string" ? msg : JSON.stringify(msg));
    }
  }, []);

  return { lastMessage, isConnected, sendMessage };
}
