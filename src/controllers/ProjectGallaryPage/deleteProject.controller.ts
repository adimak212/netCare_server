import type { Request , Response , ErrorRequestHandler} from "express";
import axios from "axios";

const GNS3_API = "http://localhost:3080/v2/projects";

export const deleteProject = async (req :Request , res: Response) => {
    const id = req.query.id as string;
    console.log(id);
    try {
        const response = await axios.delete(`${GNS3_API}/${id}`);
        res.status(200).send("project deleted")     
    } catch (error : any) {
       console.log("Error in deleting");
       console.log(error.message); 
       res.status(400).send("Error in delete")
    }
}