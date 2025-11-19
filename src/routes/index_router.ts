import { Router } from "express";
import projectRouter from "./project.router";
const indexRouter = Router();


indexRouter.use("/projects" , projectRouter);



export default indexRouter