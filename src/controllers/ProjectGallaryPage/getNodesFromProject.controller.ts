import { response, type Request, type Response } from "express";
import axios from "axios";
import { futimesSync } from "fs";
import { Dictionary, Component } from "../../types/types";

const GNS3_API = "http://localhost:3080/v2/projects";

const tamplates: Dictionary<string> = {
  "f5f30ee0-8e87-4cbf-8682-17e5aae51685": "c7200",
  "1966b864-93e7-32d5-965f-001384eec461": "3600",
  "19021f99-e36f-394d-b4a1-8aaa902ab9cc": "PC",
  "39e257dc-8412-3174-b6b3-0ee3ed6a43e9": "Cloud",
};

export const getNodesFromProject = async (req: Request, res: Response) => {
  const id: string = req.query.id as string;

  const { data } = await axios.get(`${GNS3_API}/${id}/nodes`);

  const tamplateIds: Component[] = data.map((node: any) => ({
    id: node.node_id,
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
        `http://localhost:3080/v2/projects/${id}/nodes/${element.id}`
      );
      element.ports = res.data.ports;
      console.log(element.ports);
    })
  );

  //console.log(tamplateIds);
  return res.status(200).json(tamplateIds);
};
