import { Router } from "express";
import  register  from "../controllers/user/register.controller";
import login from "../controllers/user/login.controller";


const usersRouter = Router();

usersRouter.post("/register" , register);
usersRouter.post("/login" , login)

export default usersRouter;
