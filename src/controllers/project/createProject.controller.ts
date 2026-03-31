import type { Request, Response } from "express";
import axios from "axios";
import { Link } from "../../types/types";
import { Device } from "../../classes/Device";
import { Project } from "../../models/Project.model";
const GNS3_API = "http://adi-makdasi.tail2be12f.ts.net:3080/v2/projects";

export const createProject = async (req: Request, res: Response) => {
  try {
    const { canvasComponents, ProjectName, connections, owner_id } = req.body as {
      canvasComponents: Device[];
      ProjectName: string;
      connections: Link[];
      owner_id: string;
    };
    console.log(canvasComponents);
    const GNS3_name = `${ProjectName}_${owner_id}`;
    const response = await createGNS3Project(GNS3_name);
    const project_id = response.project_id;
    var createNodeResult = await createNode(canvasComponents, project_id);
    const linksResult = await createLinks(connections, project_id, createNodeResult!);

    const body = {
      name: ProjectName,
      project_id: project_id,
      owner_id: owner_id,
      GNS3_name: GNS3_name,
    };
    const mongoProject = new Project(body);
    await mongoProject.save();
    return res.status(200).json({
      message: "Project created successfully",
      project_id: project_id,
      nodes: createNodeResult,
      links: linksResult,
    });
  } catch (error: any) {
    console.error(error);
    res.status(500).json({ error: error });
  }
};
async function createLinks(links: Link[], projectId: string, createNodeResult: Device[] | null) {
  let result = [];
  for (const link of links) {
    console.log("link from:", link.from.adapter_number, link.from.port_number);
    console.log("link to:", link.to.adapter_number, link.to.port_number);
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
    return response.data;
  } catch (error: any) {
    console.error("Error creating project:", error);
    const errorMassege = getFriendlyError(error);
    throw errorMassege;
  }
}
function getFriendlyError(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const status = err.response?.status;

    if (status === 400) {
      return "Invalid project details. Please check your input.";
    }

    if (status === 401) {
      return "You are not authorized.";
    }
    if (status === 409) {
      return "Project name already exist , Pleast pick another name";
    }
    if (status === 500) {
      return "Server error. Please try again later.";
    }

    return "Request failed. Please try again.";
  }

  return "Something went wrong.";
}

export async function createNode(canvasComponents: Device[], project_id: string) {
  try {
    const results: Device[] = [];

    for (const component of canvasComponents) {
      const x = Number.isFinite(component.x as number) ? Math.round(component.x as number) : 0;
      const y = Number.isFinite(component.y as number) ? Math.round(component.y as number) : 0;
      let payload: any;
      console.log()
      if (component.node_type === "qemu"){
        const payload = {
          x: x,
          y: y,
          name: component.name,
        };
        const response = await axios.post(
          `http://adi-makdasi.tail2be12f.ts.net:3080/v2/projects/${project_id}/templates/96ff8c08-2f4c-4dc5-bfa6-79849810c400`,
          payload,
          { headers: { "Content-Type": "application/json" } }
        );
        results.push(response.data);
      }
      else{
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
        console.log(response);
        results.push(response.data);
        
      }
     
    }
    return results;
  } catch (error: any) {
    console.log(error);
  }
}
