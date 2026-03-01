import type { Request, Response } from "express";
import axios from "axios";

const GNS3_API = "http://adi-makdasi.tail2be12f.ts.net:3080/v2/projects";

export const closeProject = async (req: Request, res: Response) => {
  try {
    const { id } = req.body.params;
    ////(id);
    const response = await axios.post(`${GNS3_API}/${id}/close`);
    res.status(200).json({ message: "project closed successfully", data: id });
  } catch (error) {
    console.error("Error opening project:", error);
    res.status(500).json({ message: "Failed to close project" });
  }
};
