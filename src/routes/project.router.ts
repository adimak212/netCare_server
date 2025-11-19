import { Router } from "express";
import { createProject } from "../controllers/project/createProject.controller";
import { getAllProjects } from "../controllers/project/getAllProjects.controller";
import { deleteProject } from "../controllers/project/deleteProject.controller";
import { getNodesFromProject } from "../controllers/project/getNodesFromProject.controller";
import { openProject } from "../controllers/project/openProject.controller"
import {closeProject} from "../controllers/project/closeProject.controller"
import { getLinksFromProject } from "../controllers/project/getLinksFromProject.controller";
import { updateProject } from "../controllers/project/updateProject.controller";
const projectRouter = Router();

projectRouter.post("/createProject", createProject);
projectRouter.get("/getAllProjects", getAllProjects);
projectRouter.get("/deleteProject", deleteProject);
projectRouter.get("/getProjectNodes" , getNodesFromProject)
projectRouter.post("/openProject" , openProject);
projectRouter.post("/closeProject" , closeProject);
projectRouter.get("/getProjectLinks" , getLinksFromProject);
projectRouter.post("/updateProject" , updateProject);

export default projectRouter;
