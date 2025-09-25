import type { Request, Response } from "express";
import axios from "axios";
import { CanvasComponent , NodeData } from "../types/types";

const GNS3_API = "http://localhost:3080/v2/projects"; // base API
const PROJECT_ID = "1b0a3369-23ea-46e1-a5e9-8a5b885e3d7e"; // replace with your GNS3 project ID


export const createProject = (req: Request, res: Response) => {
    try {
        const {canvasComponents} = req.body;
    //createGNS3Project("netCareLab", PROJECT_ID);
        for (const component of canvasComponents) {
            switch (component.type) {
                case "router":
                    createNode(PROJECT_ID , { name: component.name, node_type: "dynamips", compute_id: "local", x: 100, y: 100 });
                    break;
                case "pc":
                    createNode(PROJECT_ID , { name: component.name, node_type: "vpcs", compute_id: "local", x: 200, y: 100 });
                    break; 
                case "cloud":
                    createNode(PROJECT_ID , { name: component.name, node_type: "cloud", compute_id: "local", x: 300, y: 100 });
                    break;
                case "switch":
                    createNode(PROJECT_ID , { name: component.name, node_type: "ethernet_switch", compute_id: "local", x: 400, y: 100 });
                    break;  
            }
        }
    }
    catch (error) {
        console.error("Error in createProject controller:", error);
        res.status(500).json({ error: "Internal Server Error" });
    }
}

async function createGNS3Project(name : string , id : string) {
    const lab = axios.post(GNS3_API, {
            name: name,
            auto_close: false
        }).then(response => {
            console.log("Project created:", response.data);
            return response.data;
        }).catch(error => {
            console.error("Error creating project:", error.response?.data || error.message);
            throw error;
        });
}

// Function to create a router node in GNS3
async function createNode(projectId : string , nodeData: NodeData) {
  try {
    const response = await axios.post(`${GNS3_API}/${PROJECT_ID}/nodes`, nodeData);
    console.log("Node created:", response.data);
    return response.data;
  } catch (error: any) {
    console.error("Error creating node:", error.response?.data || error.message);
    throw error;
  }
}

