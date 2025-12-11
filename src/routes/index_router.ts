import { Router } from "express";
import projectRouter from "./project.router";
import algorithmRouter from "./algorithm.router";
const indexRouter = Router();


indexRouter.use("/projects" , projectRouter);
indexRouter.use("/algorithm" , algorithmRouter);



export default indexRouter