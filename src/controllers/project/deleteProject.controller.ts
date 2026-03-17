import type { Request, Response, ErrorRequestHandler } from "express";
import { Project } from "../../models/Project.model";
import axios from "axios";

const GNS3_API = "http://adi-makdasi.tail2be12f.ts.net:3080/v2/projects";

export const deleteProject = async (req: Request, res: Response) => {
  const id = req.query.id as string;
  try {
    const response = await axios.delete(`${GNS3_API}/${id}`);
    await Project.deleteOne({ project_id: id });
    res.status(200).send("project deleted");
  } catch (error: any) {
    console.log("Error in deleting" + error);
    console.log(error.message);
    res.status(400).send("Error in delete");
  }
};
