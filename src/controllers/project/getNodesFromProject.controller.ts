import { response, type Request, type Response } from "express";
import axios from "axios";
import { futimesSync } from "fs";
import { Dictionary, Component } from "../../types/types";
import { Device } from "../../classes/Device";

const GNS3_API = "http://localhost:3080/v2/projects";

const tamplates: Dictionary<string> = {
  "f5f30ee0-8e87-4cbf-8682-17e5aae51685": "c7200",
  "1966b864-93e7-32d5-965f-001384eec461": "3600",
  "19021f99-e36f-394d-b4a1-8aaa902ab9cc": "PC",
  "39e257dc-8412-3174-b6b3-0ee3ed6a43e9": "Cloud",
};

export async function getNodesFromProject(req: Request, res: Response){
  const id: string = req.query.id as string;

  const { data } = await axios.get(`${GNS3_API}/${id}/nodes`);

  try {
    const tamplateIds: Component[] = data.map((node: any) => ({
      node_id: node.node_id,
      id : node.node_id,
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
        //console.log(res.data.ports);
      })
    );
    
    return res.status(200).json(tamplateIds);
  } catch (error) {
    console.log("get nodes error" + error);
    return res.status(400).send({ message: "error in get nodes" });
  }
}
