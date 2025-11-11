import express from "express";

import indexRouter from "./routes/index_router";
import cors from "cors";

const app = express();
const PORT = 3000;

app.use(express.json());

app.use(
  cors({
    origin: "http://localhost:5173", // frontend dev server
    methods: ["GET", "POST"], // allowed methods
    credentials: true, // if you use cookies/auth
  })
);

// Use hello routes

app.use("/", indexRouter);

app.listen(PORT, () => {
  console.log(`✅ Server running at http://localhost:${PORT}`);
});
