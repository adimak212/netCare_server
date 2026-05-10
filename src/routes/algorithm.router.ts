import { Router } from "express";
import { runAlgorithm } from "../controllers/algorithm/runAlgorithm.controller";
import { runNetworkScan } from "../controllers/algorithm/runNetworkScan.controller";

const algorithmRouter = Router();

algorithmRouter.get("/runAlgorithm" , runAlgorithm);
algorithmRouter.get("/scan" , runNetworkScan);

export default algorithmRouter;
