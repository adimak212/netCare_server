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
    const { canvasComponents, connections, id } = req.body as {
      canvasComponents: Device[];
      connections: Link[];
      id: string;
    };
    let devices: Device[] | null = await getNodesFromProject(id);
    let links: Link[] | null = await getLinksFromProject(id);

    let devicesArray = await addOrDeleteNodes("add", devices, id, canvasComponents);

    let linksArray = await addOrDeleteLinks("add", links, connections, id, devicesArray);
    console.log(linksArray);
    if (linksArray?.length == 0){
      linksArray = await getLinksFromProject(id);
    }

    await addOrDeleteLinks("delete", links, linksArray, id, devicesArray);
    await addOrDeleteNodes("delete", devices, id, devicesArray);

    await updatePosition(id, canvasComponents);

    return res.status(200).json({ devicesArray, linksArray });
  } catch (error) {
    console.log("update error" + error);
    return res.status(400).send("eror in updating");
  }
}

async function getNodesFromProject(id: string): Promise<Device[] | null> {
  const tamplates: Dictionary<string> = {
    "f5f30ee0-8e87-4cbf-8682-17e5aae51685": "c7200",
    "1966b864-93e7-32d5-965f-001384eec461": "3600",
    "19021f99-e36f-394d-b4a1-8aaa902ab9cc": "PC",
    "39e257dc-8412-3174-b6b3-0ee3ed6a43e9": "Cloud",
  };
  try {
    const { data } = await axios.get(`${GNS3_API}/${id}/nodes`);
    const tamplateIds: Device[] = data.map((node: any) => ({
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
  updatedLinks: Link[] | null,
  id: string,
  canvasComponents: Device[] | null
) {
  try {
    switch (action) {
      case "delete":
        const actionsLinkAdd = links!.map(async (link) => {
          if (link.from.node_id && link.to.node_id) {
            const exists = updatedLinks?.some(
              (con) => link.from.node_id === con.from.node_id && link.to.node_id === con.to.node_id
            );
            if (!exists) {
              await axios.delete(`${GNS3_API}/${id}/links/${link.link_id}`);
            }
          }
        });
        await Promise.all(actionsLinkAdd);
        return null;
      case "add":  
        let newLinks: Link[] = [];
        const actionsLinks = updatedLinks!.map(async (con) => {
          if (con.to.node_id && con.from.node_id) {
            const exists = links?.some(
              (link) => link.from.node_id === con.from.node_id && link.to.node_id === con.to.node_id
            );

            if (!exists) {
              const { data } = await axios.post(`${GNS3_API}/${id}/links`, {
                nodes: [
                  {
                    node_id: canvasComponents![con.from.index!].node_id!,
                    adapter_number: con.from.adapter_number,
                    port_number: con.from.port_number,
                  },
                  {
                    node_id: canvasComponents![con.to.index!].node_id!,
                    adapter_number: con.to.adapter_number,
                    port_number: con.to.port_number,
                  },
                ],
              });
              newLinks.push({ link_id: data.link_id, from: data.nodes[0], to: data.nodes[1] });
            }
            newLinks.push(con);
          }
        });
        await Promise.all(actionsLinks);
        console.log(newLinks);
        return newLinks;
      default:
        return [];
    }
  } catch (error) {
    console.log("update error links: " + error);
    return [];
  }
}

async function addOrDeleteNodes(
  action: string,
  devices: Device[] | null,
  id: string,
  canvasComponents: Device[] | null
) {
  try {
    switch (action) {
      case "add":
        let result: Device[] = [];
        const actions = canvasComponents!.map(async (device) => {
          const exists = devices!.some((comp) => comp.node_id === device.node_id);
          if (!exists) {
            const uplodedDevice: Device[] | null = await createNode([device], id);
            result.push(uplodedDevice![0]);
          } else {
            result.push(device);
          }
        });

        await Promise.all(actions);
        return result;

      case "delete":
        //console.log(canvasComponents);
        //console.log(devices)
        const actionsDelete = devices!.map(async (comp) => {
          const deleteExist = canvasComponents!.some((device) => comp.node_id === device.node_id);
          //console.log(deleteExist);
          if (!deleteExist) {
            const todelete = await axios.delete(`${GNS3_API}/${id}/nodes/${comp.node_id}`);
          }
        });
        await Promise.all(actionsDelete);
        //console.log("finish");
        return null;
      default:
        return null;
    }
  } catch (error) {
    console.log("error in uploding nodes " + error);
    return null;
  }
}

async function updatePosition(id: string, canvasComponents: Device[]) {
  try {
    for (const device of canvasComponents) {
      await axios.put(`${GNS3_API}/${id}/nodes/${device.node_id}`, {
        x: Math.round(device.x!),
        y: Math.round(device.y!),
        name : device.name
      });
    }
  } catch (error) {
    console.log("error in update position " + error);
  }
}
