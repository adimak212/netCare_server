import { Request, Response } from "express";
import { User } from "../../models/User.model";
import bcrypt from "bcrypt";
import jwt from "jsonwebtoken";

interface LoginBody {
  email: string;
  password: string;
}

export const login = async (req: Request<{}, {}, LoginBody>, res: Response): Promise<Response> => {
  try {
    const { email, password } = req.body;
    if (!email || !password) {
      return res.status(400).send({
        message: "Email and password are required",
        isSuccess: false,
      });
    }
    const user = await User.findOne({ email });
    if (!user) {
      return res.status(400).send({
        message: "User not found",
        isSuccess: false,
      });
    }
    const isMatch = await bcrypt.compare(password, user.password);
    if (!isMatch) {
      return res.status(401).send({
        message: "Password is incorrect",
        isSuccess: false,
      });
    }
    const token = jwt.sign({ id: user._id, email: user.email }, process.env.JWT_SECRET as string, {
      expiresIn: "3h",
    });
    return res.status(200).send({
      user: {
        _id: user._id,
        email: user.email,
        userName: user.userName,
      },
      token,
      isSuccess: true,
    });
  } catch (error) {
    console.log(error);
    return res.status(500).send({
      message: "Error in login",
      isSuccess: false,
    });
  }
};

export default login;
