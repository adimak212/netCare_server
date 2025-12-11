import { Router } from "express";
import { runAlgorithm } from "../controllers/algorithm/runAlgorithm.controller";


const algorithmRouter = Router();

algorithmRouter.get("/runAlgorithm" , runAlgorithm);

export default algorithmRouter;
