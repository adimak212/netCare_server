import { response, type Request , type Response } from "express";
import axios from "axios";
import { futimesSync } from "fs";


const GNS3_API = "http://localhost:3080/v2/projects";

export const getAllProjects = (req :Request , res: Response) => {
    
    const response = axios.get(GNS3_API).then(response => { 
        console.log(response.data);
        res.status(200).json(response.data)
    });

}