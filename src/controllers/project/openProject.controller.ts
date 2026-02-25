import type { Request, Response } from "express";
import axios from "axios";

const GNS3_API = "http://100.71.52.17:3080/v2/projects";

export const openProject = async (req: Request, res: Response) => {
  try {
    const { id } = req.body.params;
    const response = await axios.post(`${GNS3_API}/${id}/open`);
    res.status(200).json({ message: "project opend successfully", data: id });
  } catch (error) {
    console.error("Error opening project:", error);
    res.status(500).json({ message: "Failed to open project" });
  }
};
