import express from "express";
import cors from "cors";
import http from "http";
import { WebSocketServer, type WebSocket, type RawData } from "ws";
import type { IncomingMessage } from "http";
import net from "net";
import indexRouter from "./routes/index_router";

const app = express();
const PORT = 3000;

app.use(express.json());

app.use(
  cors({
    origin: "http://localhost:5173",
    methods: ["GET", "POST"],
    credentials: true,
  }),
);

app.use("/v1", indexRouter);

const server = http.createServer(app);

const wss = new WebSocketServer({ server, path: "/ws/console" });

wss.on("connection", (ws: WebSocket, req: IncomingMessage) => {
  const url = new URL(req.url ?? "", "http://localhost");
  const port = Number(url.searchParams.get("port"));
  const tcp = net.createConnection({ host: "172.20.10.14", port }, () => {
    console.log("Connected to GNS3 console");
  });
  ws.on("close", () => {
    tcp.end();
  });

  tcp.on("close", () => {
    ws.close();
  });
  wss.on("connection", (ws: WebSocket, req: IncomingMessage) => {
    ws.on("message", (data: RawData) => {
      const text = typeof data === "string" ? data : Buffer.from(data as any).toString("utf-8");
      ws.send(`echo: ${text}`);
    });
  });

  ws.on("close", () => console.log("WS closed"));
  ws.on("error", (err: Error) => console.error("WS error:", err));
});

server.listen(PORT, () => {
  console.log(`✅ Server running at http://localhost:${PORT}`);
  console.log(`✅ WS at ws://localhost:${PORT}/ws/console`);
});
