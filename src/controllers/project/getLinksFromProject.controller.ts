import type { Request, Response } from "express";
import axios from "axios";
import { Link } from "../../types/types";
import { Device } from "../../classes/Device";

const GNS3_API = "http://100.71.52.17:3080/v2/projects";

export const getLinksFromProject = async (req: Request, res: Response) => {
  try {
    const id: string = req.query.id as string;
    const { data } = await axios.get(`${GNS3_API}/${id}/links`);
    const links: Link[] = data.map((link: any) => ({
      link_id: link.link_id,
      from: link.nodes[0],
      to: link.nodes[1],
    }));
    ////(links)
    return res.status(200).json(links);
  } catch (error) {
    console.log(error);
    return res.status(400).send({ message: "error in get links" });
  }
};
