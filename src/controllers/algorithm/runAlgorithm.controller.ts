import type { Request, Response } from "express";
import { spawn } from "child_process";

export const runAlgorithm = (req: Request, res: Response) => {
  const params = req.query;

  const python = spawn("python", ["-m", "src.algorithm.version2.main", JSON.stringify(params)], {
    cwd: process.cwd(),
  });

  let dataString = "";
  let errorString = "";

  python.stdout.on("data", (data) => {
    //console.log("Python output:", data.toString());
    dataString += data.toString();
  });
  python.stderr.on("data", (data) => {
    console.error("Python error:", data.toString());
    errorString += data.toString();
  });

  python.on("close", (code) => {
    console.log(`Python process exited with code ${code}`);
    if (code !== 0) {
      return res.status(500).json({
        error: "Algorithm failed",
        details: errorString || dataString,
        exitCode: code,
      });
    }
    const raw = dataString.trim();
    if (!raw) {
      return res.status(500).json({
        error: "Python returned empty output",
        details: errorString,
      });
    }
    try {
      const parsed = JSON.parse(raw);
      console.log(raw);
      if (params["build_or_bestfit"] === "bestfit") {
        const ranksArray = Object.entries(parsed.ranks).map(([name, score]) => ({
          name,
          score,
        }));
        parsed.ranks = ranksArray;
      }
      return res.status(200).json(parsed);
    } catch (e: any) {
      return res.status(500).json({
        error: "Python did not return valid JSON",
        raw,
        details: errorString,
      });
    }
  });

  python.on("error", (error) => {
    console.error("Failed to start Python:", error);
    return res.status(500).json({
      error: "Failed to start algorithm",
      details: error.message,
    });
  });
};
