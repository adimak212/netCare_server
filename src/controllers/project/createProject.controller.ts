import type { Request, Response } from "express";
import axios from "axios";
import { Link } from "../../types/types";
import { Device } from "../../classes/Device";

const GNS3_API = "http://100.71.52.17:3080/v2/projects";

export const createProject = async (req: Request, res: Response) => {
  try {
    const { canvasComponents, ProjectName, connections } = req.body as {
      canvasComponents: Device[];
      ProjectName: string;
      connections: Link[];
    };
    //console.log("Links" + connections.values);
    const response = await createGNS3Project(ProjectName);
    const project_id = response.project_id;
    var createNodeResult = await createNode(canvasComponents, project_id);
    console.log("Nodes: " + createNodeResult);
    const linksResult = await createLinks(connections, project_id, createNodeResult);
    console.log(linksResult);
    return res.status(200).json({
      message: "Project created successfully",
      project_id: project_id,
      nodes: createNodeResult,
      links: linksResult,
    });
  } catch (error) {
    console.error("Error in createProject controller:", error);
    res.status(500).json({ error: "Internal Server Error" });
  }
};

async function createLinks(links: Link[], projectId: string, createNodeResult: Device[] | null) {
  let result = [];
  for (const link of links) {
    try {
      const node = [
        {
          node_id: createNodeResult![Number(link.from.index!)].node_id,
          adapter_number: link.from.adapter_number,
          port_number: link.from.port_number,
        },
        {
          node_id: createNodeResult![Number(link.to.index!)].node_id,
          adapter_number: link.to.adapter_number,
          port_number: link.to.port_number,
        },
      ];
      await axios.post(`${GNS3_API}/${projectId}/links`, { nodes: node });
      result.push({ from: node[0], to: node[1] });
    } catch (error) {
      console.error("Error creating link:", error);
    }
  }
  return result;
}

async function createGNS3Project(name: string) {
  try {
    const response = await axios.post(GNS3_API, {
      name,
      auto_close: false,
    });
    //console.log("Project created: ", response.data);
    return response.data;
  } catch (error: any) {
    console.error("Error creating project:", error.response?.data || error.message);
    throw error;
  }
}

export async function createNode(canvasComponents: Device[], project_id: string) {
  try {
    const results: Device[] = [];

    for (const component of canvasComponents) {
      const x = Number.isFinite(component.x as number) ? Math.round(component.x as number) : 0;
      const y = Number.isFinite(component.y as number) ? Math.round(component.y as number) : 0;
      let payload: any;
      switch (component.node_type) {
        case "dynamips": {
          payload = {
            name: component.name,
            node_type: "dynamips",
            template_id: "533361ab-e9de-4326-a9ee-9d3770a4bbb1",
            compute_id: "local",
            x: x,
            y: y,
            symbol: ":/symbols/router.svg",
            properties: {
              platform: "c7200",
              npe: "npe-400",
              image: "c7200-adventerprisek9-mz.153-3.XB12.image",
              ram: 512,
              nvram: 512,
              slot0: "C7200-IO-FE",
              slot1: "PA-4T+",
              slot2: "PA-2FE-TX",
            },
          };
          break;
        }

        case "ethernet_switch": {
          payload = {
            name: component.name,
            node_type: "ethernet_switch",
            template_id: "1966b864-93e7-32d5-965f-001384eec461",
            compute_id: "local",
            x: x,
            y: y,
            symbol: ":/symbols/ethernet_switch.svg",
            properties: { ports: 8 },
          };
          break;
        }

        case "vpcs": {
          payload = {
            name: component.name,
            node_type: "vpcs",
            template_id: "19021f99-e36f-394d-b4a1-8aaa902ab9cc",
            compute_id: "local",
            x: x,
            y: y,
            symbol: ":/symbols/vpcs_guest.svg",
            properties: { base_script_file: "vpcs_base_config.txt" },
          };
          break;
        }

        case "cloud": {
          payload = {
            name: component.name,
            node_type: "cloud",
            template_id: "39e257dc-8412-3174-b6b3-0ee3ed6a43e9",
            compute_id: "local",
            x: x,
            y: y,
            symbol: ":/symbols/cloud.svg",
            properties: {},
          };
          break;
        }
        default: {
          console.warn("Unknown component id:", component.node_id);
          continue;
        }
      }
      const response = await axios.post(`${GNS3_API}/${project_id}/nodes`, payload, {
        headers: { "Content-Type": "application/json" },
      });
      results.push(response.data);
    }
    return results;
  } catch (error: any) {
    console.error("Error creating nodes:", error.response?.data || error.message);
    return null;
  }
}
