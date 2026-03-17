import { response, type Request, type Response } from "express";
import axios from "axios";
import { getNodesFromProject } from "./getNodesFromProject.controller";
import { Project } from "../../models/Project.model";

export const getProjectsByUser = async (req: Request, res: Response) => {
    try {
        var filter = {};
        console.log(req.query);
        if (Object.keys(req.query).length > 0 && req.query.owner_id){
            filter = {owner_id : req.query.owner_id}
        }
        const result  = await Project.find(filter);
        //console.log(result);
        return res.status(200).json(result);
    } catch (error) {
         console.log(error);
        res.status(500).send({message : "Error to get all songs" , isSucsses : false});
    }
}

