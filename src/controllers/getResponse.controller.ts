import type { Request, Response } from "express";

// Controller function
export const getResponse = (req: Request, res: Response) => {
    console.log("Controller function called");
    res.setHeader("Cache-Control", "no-store");
    res.json([{ text: "Hello from backend 🚀"} , { text: "I am  a developper!!!!"}]);
};
