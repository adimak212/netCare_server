import { Router } from "express";
import projectRouter from "./project.router";
import algorithmRouter from "./algorithm.router";
import agentRouter from "./agent.router"
import usersRouter from "./users.router";
const indexRouter = Router();


indexRouter.use("/projects" , projectRouter);
indexRouter.use("/algorithm" , algorithmRouter);
indexRouter.use("/agents" , agentRouter);
indexRouter.use("/users" , usersRouter);



export default indexRouter