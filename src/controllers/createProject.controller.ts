import type { Request, Response } from "express";
import axios from "axios";
import { CanvasComponent , NodeData } from "../types/types";

const GNS3_API = "http://localhost:3080/v2/projects"; // base API
const PROJECT_ID = "3a733b20-8d5e-4d6b-aca8-43454b3cb410"; // replace with your GNS3 project ID


export const createProject = async (req: Request, res: Response) => {
    try {
        const {canvasComponents} = req.body;
         const response = await createGNS3Project("Test1UploadRouter");
         console.log("GNS3 Project creation response:", response.project_id);
        for (const component of canvasComponents) {
            switch (component.id) {
                case "router":
                    const nodeRes = await axios.post(`${GNS3_API}/${response.project_id}/nodes`,
                        {
                            name: "router1",
                            node_type: "dynamips",
                            template_id: "f5f30ee0-8e87-4cbf-8682-17e5aae51685",
                            compute_id: "local",
                            x: 100,
                            y: 100,
                            properties: {
                            platform: "c7200",
                            npe: "npe-400",
                            image: "c7200-adventerprisek9-mz.153-3.XB12.image",
                            ram: 512,
                            nvram: 512,
                            slot0: "C7200-IO-FE",
                            slot1: "PA-4T+",
                            slot2: "PA-2FE-TX"
                            }
                        },
                        { headers: { "Content-Type": "application/json" } }
                    );
                    break;
                case "switch":
            }
        }
       res.status(200).json({ message: "Project creation initiated", response });
    } 
    catch (error) {
        console.error("Error in createProject controller:", error);
        res.status(500).json({ error: "Internal Server Error" });
    }

}
async function createGNS3Project(name : string) {
  try {
    const response = await axios.post(GNS3_API, {
      name,
      auto_close: false,
    });
    console.log("Project created: ", response.data);
    return response.data;
  } catch (error: any) {
    console.error("Error creating project:", error.response?.data || error.message);
    throw error;
  }
}
