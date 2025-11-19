import type { Request, Response } from "express";
import axios from "axios";
import { Link } from "../../types/types";
import { Device } from "../../classes/Device";
import { Dictionary, Component } from "../../types/types";
import { createNode } from "./createProject.controller";
import { link } from "fs";

const GNS3_API = "http://localhost:3080/v2/projects";

export async function updateProject(req: Request, res: Response) {
  try {
    const { canvasComponents, ProjectName, connections, id } = req.body as {
      canvasComponents: Device[];
      ProjectName: string;
      connections: Link[];
      id: string;
    };
    let devices: Component[] | null = await getNodesFromProject(id);
    let links: Link[] | null = await getLinksFromProject(id);

    addOrDeleteNodes("add", devices, id, canvasComponents);
    addOrDeleteLinks("add", links, connections, id, canvasComponents);

    devices = await getNodesFromProject(id);
    links = await getLinksFromProject(id);

    addOrDeleteLinks("delete", links, connections, id, canvasComponents);
    addOrDeleteNodes("delete", devices, id, canvasComponents);

    updatePosition(id, canvasComponents);

    return res.status(200).json({ message: "Project updated" });
  } catch (error) {
    console.log("update error" + error);
    return res.status(400).send("eror in updating");
  }
}

async function getNodesFromProject(id: string): Promise<Component[] | null> {
  const tamplates: Dictionary<string> = {
    "f5f30ee0-8e87-4cbf-8682-17e5aae51685": "c7200",
    "1966b864-93e7-32d5-965f-001384eec461": "3600",
    "19021f99-e36f-394d-b4a1-8aaa902ab9cc": "PC",
    "39e257dc-8412-3174-b6b3-0ee3ed6a43e9": "Cloud",
  };
  try {
    const { data } = await axios.get(`${GNS3_API}/${id}/nodes`);
    const tamplateIds: Component[] = data.map((node: any) => ({
      node_id: node.node_id,
      name: node.name,
      modelType: tamplates[node.template_id],
      x: node.x,
      y: node.y,
      deviceType: node.node_type,
      ports: [],
    }));
    await Promise.all(
      tamplateIds.map(async (element) => {
        const res = await axios.get(
          `http://localhost:3080/v2/projects/${id}/nodes/${element.node_id}`
        );
        element.ports = res.data.ports;
      })
    );
    return tamplateIds;
  } catch (error) {
    console.log("get nodes error" + error);
    return null;
  }
}

async function getLinksFromProject(id: string) {
  try {
    const { data } = await axios.get(`${GNS3_API}/${id}/links`);
    const links: Link[] = data.map((link: any) => ({
      from: link.nodes[0],
      to: link.nodes[1],
    }));
    return links;
  } catch (error) {
    console.log(error);
    return null;
  }
}

async function addOrDeleteLinks(
  action: string,
  links: Link[] | null,
  updatedLinks: Link[],
  id: string,
  canvasComponents: Device[]
) {
  try {
    switch (action) {
      case "delete":
        links?.forEach(async (link) => {
          const exists = updatedLinks?.some(
            (con) =>
              link.from.node_id === con.from.node_id &&
              link.to.node_id === con.to.node_id
          );
          if (!exists) {
            const uplodedLink = await axios.delete(
              `${GNS3_API}/${id}/links/${link.link_id}`
            );
          }
        });
        break;
      case "add":
        updatedLinks?.forEach(async (con) => {
          console.log(con.from.node_id);
          const exists = links?.some(
            (link) =>
              link.from.node_id === con.from.node_id &&
              link.to.node_id === con.to.node_id
          );
          if (!exists) {
            const uplodedLink = await axios.post(`${GNS3_API}/${id}/links`, {
              nodes: [
                {
                  node_id: canvasComponents[con.from.index!].node_id,
                  adapter_number: con.from.adapter_number,
                  port_number: con.from.port_number,
                },
                {
                  node_id: canvasComponents[con.to.index!].node_id,
                  adapter_number: con.to.adapter_number,
                  port_number: con.to.port_number,
                },
              ], 
            });
          }
        });
        break;
    }
  } catch (error) {
    console.log("update error main" + error);
    throw new Error("error in update links");
  }
}

async function addOrDeleteNodes (
  action: string,
  devices: Component[] | null,
  id: string,
  canvasComponents: Device[]
) {
  try {
    switch (action) {
      case "add":
        let result : Device[] = [];
        canvasComponents.forEach(async (device) => {
          const exists = devices!.some(
            (comp) => comp.node_id === device.node_id
          );
          if (!exists) {
            const uplodedDevice: Device[] | null = await createNode(
              [device],
              id
            );
            device.node_id = uplodedDevice![0].node_id;
            result.push(device);
          }
        });
        return result;

      case "delete":
        devices!.forEach(async (comp) => {
          const deleteExist = canvasComponents.some(
            (device) => comp.node_id === device.node_id
          );
          if (!deleteExist) {
            const todelete = await axios.delete(
              `${GNS3_API}/${id}/nodes/${comp.node_id}`
            );
          }
        });
        break;
    }
  } catch (error) {
    console.log("error in uploding nodes " + error);
    throw new Error("error in update nodes");
  }
}

async function updatePosition(id: string, canvasComponents: Device[]) {
  try {
    for (const device of canvasComponents) {
      await axios.put(`${GNS3_API}/${id}/nodes/${device.node_id}`, {
        x: Math.round(device.x!),
        y: Math.round(device.y!),
      });
    }
  } catch (error) {
    console.log("error in update position " + error);
  }
}
