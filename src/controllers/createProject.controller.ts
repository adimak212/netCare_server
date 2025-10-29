import type { Request, Response } from "express";
import axios from "axios";
import { CanvasComponent} from "../types/types";

const GNS3_API = "http://localhost:3080/v2/projects"; // base URL for GNS3 API
const PROJECT_ID = "3a733b20-8d5e-4d6b-aca8-43454b3cb410"; 


export const createProject = async (req: Request, res: Response) => {
    try {
        const {canvasComponents , ProjectName} = req.body as {canvasComponents : CanvasComponent[], ProjectName : string};
        const response = await createGNS3Project(ProjectName);
        for (const component of canvasComponents) {
            switch (component.id) {
                case "router":
                    const nodeRes = await axios.post(`${GNS3_API}/${response.project_id}/nodes`,
                        {
                            name: "router1",
                            node_type: "dynamips",
                            template_id: "f5f30ee0-8e87-4cbf-8682-17e5aae51685",
                            compute_id: "local",
                            x: Math.round(component.x),
                            y: Math.round(component.y),
                            symbol: ":/symbols/router.svg",
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
                  const switchRes = await axios.post(
                    `${GNS3_API}/${response.project_id}/nodes`,
                    {
                      name: "switch1",
                      node_type: "ethernet_switch",
                      template_id: "1966b864-93e7-32d5-965f-001384eec461",
                      compute_id: "local",
                      x: Math.round(component.x),
                      y: Math.round(component.y),
                      symbol : ":/symbols/ethernet_switch.svg" ,
                      properties: {
                        ports: 8, 
                      },
                    },
                    { headers: { "Content-Type": "application/json" } }
                  );
                break;

                case "pc":
                  const pcRes = await axios.post(
                    `${GNS3_API}/${response.project_id}/nodes`,
                    {
                      name: "pc1",
                      node_type: "vpcs",
                      template_id: "19021f99-e36f-394d-b4a1-8aaa902ab9cc",
                      compute_id: "local",
                      x: Math.round(component.x),
                      y: Math.round(component.y),
                      symbol: ":/symbols/vpcs_guest.svg",
                      properties: {
                        base_script_file: "vpcs_base_config.txt"
                      }
                    },
                    { headers: { "Content-Type": "application/json" } }
                  );
                break;

                case "cloud":
                  const cloudRes =  await axios.post(
                    `${GNS3_API}/${response.project_id}/nodes`,
                    {
                      name: "cloud1",
                      node_type: "cloud",
                      template_id: "39e257dc-8412-3174-b6b3-0ee3ed6a43e9",
                      compute_id: "local",
                      x: Math.round(component.x),
                      y: Math.round(component.y),
                      symbol: ":/symbols/cloud.svg",
                      properties: {}
                    },
                    { headers: { "Content-Type": "application/json" } }
                  );
                break;
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
