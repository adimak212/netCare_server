import type { Request, Response } from "express";
import { spawn } from "child_process";

export const runAlgorithm = (req: Request, res: Response) => {
  const params = req.query;
  
  const python = spawn("python", [
    "src/algorithm/mainAlgorithm.py", 
    JSON.stringify(params)
  ]);

  let dataString = "";
  let errorString = "";

  python.stdout.on("data", (data) => {
    console.log("Python output:", data.toString());
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
        details: errorString 
      });
    }
    
    return res.status(200).json({ 
      message: "Success", 
      result: dataString 
    });
  });

  python.on("error", (error) => {
    console.error("Failed to start Python:", error);
    return res.status(500).json({ 
      error: "Failed to start algorithm", 
      details: error.message 
    });
  });
};