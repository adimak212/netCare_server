import { Router } from "express";
import { getResponse } from "../controllers/getResponse.controller";
import { createProject } from "../controllers/createProject.controller";
import { getAllProjects } from "../controllers/getAllProjects.controller";
import {deleteProject} from "../controllers/deleteProject.controller"

const router = Router();

router.get("/getResponse", getResponse);
router.post("/createProject", createProject);
router.get("/getAllProjects", getAllProjects);
router.get("/deleteProject" , deleteProject)

export default router;
