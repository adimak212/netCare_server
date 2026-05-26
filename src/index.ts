import express from "express";
import cors from "cors";
import http from "http";
import { WebSocketServer, type WebSocket } from "ws";
import type { IncomingMessage } from "http";
import net from "net";
import indexRouter from "./routes/index_router";
import type { RawData } from "ws";
import initDb  from "./models/db.model"
import dotenv from "dotenv";


const app = express();
app.use(express.json());
const PORT = 3000;

dotenv.config();
app.use(
  cors({
    origin: "http://localhost:5173",
    methods: ["GET", "POST"],
    credentials: true,
  }),
);
initDb();
app.use("/v1", indexRouter);

const server = http.createServer(app);
const wss = new WebSocketServer({ server, path: "/ws/console" });

function assertNever(x: never): never {
  throw new Error("Unexpected RawData type");
}

export function rawDataToString(data: RawData): string {
  if (typeof data === "string") return data;
  if (Buffer.isBuffer(data)) return data.toString("utf8");
  if (data instanceof ArrayBuffer) return Buffer.from(data).toString("utf8");
  if (Array.isArray(data)) return Buffer.concat(data).toString("utf8");
  return assertNever(data);
}

wss.on("connection", (ws: WebSocket, req: IncomingMessage) => {
  // ws://localhost:3000/ws/console?host=172.20.10.14&port=5021
  const url = new URL(req.url ?? "", "http://localhost");
  const host = "100.71.52.17"//url.searchParams.get("host") ?? "172.20.10.14";
  const port = Number(url.searchParams.get("port"));

  if (!port || Number.isNaN(port)) {
    ws.close(1008, "Missing/invalid port");
    return;
  }

  const tcp = net.createConnection({ host, port });

  tcp.on("connect", () => {
    //(`✅ TCP connected to ${host}:${port}`);
  });

  tcp.on("data", (chunk) => {
    // מהקונסול -> לדפדפן
    if (ws.readyState === ws.OPEN) ws.send(chunk);
  });

  tcp.on("error", (err) => {
    console.error("TCP error:", err.message);
    try {
      ws.close(1011, "TCP error");
    } catch {}
  });

  tcp.on("close", () => {
    try {
      ws.close();
    } catch {}
  });

  ws.on("message", (data: RawData) => {
    const text = rawDataToString(data);
    tcp.write(text.replace(/\n/g, "\r\n"));
  });

  ws.on("close", () => {
    tcp.end();
  });

  ws.on("error", (err) => {
    console.error("WS error:", err.message);
    tcp.end();
  });
});

server.listen(PORT, "0.0.0.0", () => {
  console.log(`Server listening on port ${PORT}`);
});