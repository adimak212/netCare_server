import { Router } from "express";
import {getResponse} from "../controllers/getResponse.controller";
import {createProject} from "../controllers/createProject.controller";

const router = Router();

// GET /api/hello
router.get("/getResponse", getResponse);
router.post("/createProject", createProject);

export default router;
