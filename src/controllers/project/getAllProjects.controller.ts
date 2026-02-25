import { response, type Request, type Response } from "express";
import axios from "axios";
import { getNodesFromProject } from "./getNodesFromProject.controller";

const GNS3_API = "http://100.71.52.17:3080/v2/projects";

export const getAllProjects = async (req: Request, res: Response) => {
  const response = await axios.get(GNS3_API).then((response) => {
    res.status(200).json(response.data);
  });
};
