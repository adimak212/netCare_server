import mongoose, { Schema, Document, Model } from "mongoose";

export interface IUser extends Document {
  email: string;
  password: string;
  userName: string;
}

const userSchema: Schema<IUser> = new Schema({
  email: {
    type: String,
    required: true,
    unique: true,
  },
  password: {
    type: String,
    required: true,
  },
  userName: {
    type: String,
    required : true,
  }
});

export const User: Model<IUser> = mongoose.model<IUser>("users", userSchema);
console.log("Collection name:", User.collection.name);