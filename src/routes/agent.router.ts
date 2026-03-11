import { Router } from "express";
import fs from "fs";
import path from "path";

const router = Router();

const API_KEY = process.env.NETCARE_API_KEY ?? "netcare_local_secret";

/* הדרך הנכונה אצלך */
const PROJECT_ROOT = path.resolve(__dirname, "..", "..");
const DATA_DIR = path.join(PROJECT_ROOT, "data");
const REPORTS_FILE = path.join(DATA_DIR, "reports.jsonl");

if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR, { recursive: true });

console.log("Saving reports to:", REPORTS_FILE);

router.post("/report", (req, res) => {
  const auth = req.header("authorization") ?? "";

  if (auth !== `Bearer ${API_KEY}`) {
    return res.status(401).json({ ok: false });
  }

  const report = req.body;
  console.log("CWD:", process.cwd());
  console.log("REPORTS_FILE:", REPORTS_FILE);
  fs.appendFileSync(REPORTS_FILE, JSON.stringify(report) + "\n", "utf8");
  console.log("WROTE OK. Exists?", fs.existsSync(REPORTS_FILE));

  res.json({ ok: true });
});

export default router;
