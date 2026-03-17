import { User } from "../../models/User.model";
import bcrypt from "bcrypt";
import { Request, Response } from "express";

const register = async (req : Request , res: Response) => {
  try {
    const body = req.body;
    const user = await User.findOne({ email: body.email });
    if (user) {
      return res.status(400).send({ message: "Email is not validate" });
    }
    
    const newPassword = await bcrypt.hash(body.password, 10);
    body.password = newPassword;
    const newUser = new User(body);
    await newUser.save();
    return res.status(200).send(newUser);
  } catch (error) {
    console.log(error);
    return res.status(500).send({ message: "Error to register user", isSucsses: false });
  }
};

export default register