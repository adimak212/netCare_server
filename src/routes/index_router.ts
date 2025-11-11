import { Router } from "express";
import { createProject } from "../controllers/CreateProject/createProject.controller";
import { getAllProjects } from "../controllers/ProjectGallaryPage/getAllProjects.controller";
import { deleteProject } from "../controllers/ProjectGallaryPage/deleteProject.controller";
import { getNodesFromProject } from "../controllers/ProjectGallaryPage/getNodesFromProject.controller";
import { openPick } from "../controllers/ProjectGallaryPage/openPick.controller"
import {closeProject} from "../controllers/ProjectGallaryPage/closeProject.controller"
const router = Router();

router.post("/createProject", createProject);
router.get("/getAllProjects", getAllProjects);
router.get("/deleteProject", deleteProject);
router.get("/getNodes" , getNodesFromProject)
router.post("/openProject" , openPick);
router.post("/closeProject" , closeProject);

export default router;
